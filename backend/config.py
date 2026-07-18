"""Environment variables, constants, and the shared Qwen client.

All LLM calls in this project go through the OpenAI-compatible client
returned by get_qwen_client(), pointed at QWEN_BASE_URL.
"""

import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# --- Neo4j ---
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://localhost.databases.neo4j.io")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

# --- Qwen (OpenAI-compatible endpoint) ---
QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv(
    "QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-plus")

# --- MCP server ---
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))

# --- Backend ---
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# --- Business constants ---
COMPANY_ID = "ORB-SG-001"
ANNUAL_REVENUE_SGD = 285_000_000.0
MONTHLY_REVENUE_SGD = ANNUAL_REVENUE_SGD / 12.0
SIMULATION_DATE = "2026-03-04"  # "today" inside the March 2026 scenario

AIR_FREIGHT_MULTIPLIER = 3.5
CARRYING_COST_PCT_ANNUAL = 0.25
REALLOCATION_FIXED_COST_SGD = 15_000.0
MARGIN_IMPACT_THRESHOLD_PCT = 5.0
MAX_NEGOTIATION_ROUNDS = 2

_qwen_client: OpenAI | None = None


def get_qwen_client() -> OpenAI:
    """OpenAI-compatible client for Qwen (DashScope compatible mode)."""
    global _qwen_client
    if _qwen_client is None:
        _qwen_client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
    return _qwen_client


def qwen_chat(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
    """Single-turn chat completion against Qwen. Returns the raw content string."""
    client = get_qwen_client()
    response = client.chat.completions.create(
        model=QWEN_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""


def qwen_chat_json(system_prompt: str, user_prompt: str, temperature: float = 0.2):
    """Chat completion that expects a JSON payload; strips code fences and parses.

    Raises on API failure or unparseable output — callers provide deterministic
    fallbacks so the demo never blocks on the LLM.
    """
    raw = qwen_chat(system_prompt, user_prompt, temperature=temperature)
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    start = min(
        [i for i in (cleaned.find("{"), cleaned.find("[")) if i >= 0], default=-1
    )
    if start > 0:
        cleaned = cleaned[start:]
    return json.loads(cleaned)
