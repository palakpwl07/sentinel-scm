"""MCP protocol client — primary path for agent tool calls, with in-process fallback.

Every agent tool call goes over MCP (SSE, port 8001) by default. If the MCP
round-trip raises for any reason, the call falls back to the direct in-process
function supplied by the caller and logs a WARNING, so the demo degrades
gracefully instead of crashing.

Async→sync bridge: call_tool_sync is invoked from synchronous LangGraph nodes
that execute inside FastAPI's already-running event loop, so asyncio.run()
cannot be used on the caller's thread. Each MCP call is instead submitted to a
dedicated worker thread that owns a fresh event loop (asyncio.run inside a
ThreadPoolExecutor worker).

Registered tool names carry the `_tool` suffix (see server.py):
assess_supplier_risk_tool, find_alternative_suppliers_tool,
calculate_inventory_runway_tool, evaluate_mitigation_cost_tool.
"""

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from mcp import ClientSession
from mcp.client.sse import sse_client

import config

logger = logging.getLogger("mcp_client")
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

MCP_ENABLED = os.getenv("MCP_ENABLED", "true").strip().lower() not in (
    "0", "false", "no", "off",
)

# The server binds MCP_SERVER_HOST (0.0.0.0 in containers) — that is not a
# connectable address, so the client swaps it for localhost unless
# MCP_CLIENT_HOST points elsewhere (e.g. the compose service name).
_client_host = os.getenv("MCP_CLIENT_HOST") or config.MCP_SERVER_HOST
if _client_host in ("0.0.0.0", "::", ""):
    _client_host = "localhost"
MCP_SERVER_URL = f"http://{_client_host}:{config.MCP_SERVER_PORT}/sse"

MCP_CALL_TIMEOUT_SECONDS = float(os.getenv("MCP_CALL_TIMEOUT_SECONDS", "15"))

_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="mcp-client")

logger.info(
    "MCP client loaded: server_url=%s MCP_ENABLED=%s timeout=%.0fs",
    MCP_SERVER_URL, MCP_ENABLED, MCP_CALL_TIMEOUT_SECONDS,
)


def _parse_tool_result(tool_name: str, result) -> Any:
    """Normalise a CallToolResult to the plain Python object the direct
    in-process function would have returned."""
    if getattr(result, "isError", False):
        texts = [
            getattr(block, "text", "") for block in (result.content or [])
        ]
        raise RuntimeError(
            f"MCP tool {tool_name} returned isError: {' '.join(t for t in texts if t)[:500]}"
        )

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        # FastMCP wraps non-object returns (e.g. list results) as {"result": ...}
        if isinstance(structured, dict) and set(structured.keys()) == {"result"}:
            return structured["result"]
        return structured

    for block in result.content or []:
        text = getattr(block, "text", None)
        if text is not None:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
    return None


async def call_mcp_tool(tool_name: str, arguments: dict) -> Any:
    """Open an SSE session to the MCP server, call the named tool, and return
    the parsed payload (dict or list, matching the direct function)."""
    async def _roundtrip():
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await session.call_tool(tool_name, arguments)

    result = await asyncio.wait_for(_roundtrip(), timeout=MCP_CALL_TIMEOUT_SECONDS)
    return _parse_tool_result(tool_name, result)


def _run_in_fresh_loop(coro):
    return asyncio.run(coro)


def call_tool_sync(tool_name: str, arguments: dict, fallback_fn: Callable[[], Any]) -> Any:
    """Synchronous bridge for LangGraph nodes. MCP-first; on ANY exception from
    the MCP path, runs fallback_fn() (the pre-bound direct function) instead."""
    if not MCP_ENABLED:
        return fallback_fn()
    try:
        future = _executor.submit(_run_in_fresh_loop, call_mcp_tool(tool_name, arguments))
        result = future.result(timeout=MCP_CALL_TIMEOUT_SECONDS + 5)
        logger.debug("MCP %s -> ok", tool_name)
        return result
    except Exception as exc:
        logger.warning(
            "MCP call to %s failed (%s: %s); falling back to in-process.",
            tool_name, type(exc).__name__, exc,
        )
        return fallback_fn()


async def list_mcp_tools(timeout: float = 5.0) -> list[str]:
    """Lightweight reachability probe: list registered tool names."""
    async def _inner():
        async with sse_client(MCP_SERVER_URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                listing = await session.list_tools()
                return [tool.name for tool in listing.tools]

    return await asyncio.wait_for(_inner(), timeout=timeout)


async def probe_mcp() -> dict:
    """Health-endpoint helper: {"mcp": bool, "mcp_tools": [...]}."""
    if not MCP_ENABLED:
        return {"mcp": False, "mcp_tools": [], "mcp_disabled": True}
    try:
        tools = await list_mcp_tools()
        return {"mcp": True, "mcp_tools": tools}
    except Exception as exc:
        logger.warning("MCP health probe failed (%s: %s)", type(exc).__name__, exc)
        return {"mcp": False, "mcp_tools": []}
