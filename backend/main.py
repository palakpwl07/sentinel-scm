"""FastAPI backend — scenario triggering, SSE agent stream, digital twin state, HITL."""

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import config
from agents.graph import graph
from database.neo4j_client import get_client
from mcp_server import client as mcp_client
from scenarios.march_2026 import SCENARIOS

app = FastAPI(title="SupplyChainAI Control Tower", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TriggerRequest(BaseModel):
    scenario_id: str
    session_id: str


class DecisionRequest(BaseModel):
    decision: str  # "approve" | "reject"
    notes: Optional[str] = None


class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.queue: asyncio.Queue = asyncio.Queue()
        self.decision_event = asyncio.Event()
        self.decision: Optional[str] = None
        self.notes: Optional[str] = None
        self.done = False


SESSIONS: dict[str, Session] = {}

_SENTINEL = {"type": "complete"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run_scenario(session: Session, scenario_id: str):
    thread_config = {"configurable": {"thread_id": session.session_id}}
    initial_state = {
        "scenario_id": scenario_id,
        "event_description": SCENARIOS[scenario_id]["event_description"],
        "event_date": SCENARIOS[scenario_id]["trigger_date"],
        "detected_events": [],
        "affected_regions": [],
        "affected_ports": [],
        "affected_suppliers": [],
        "inventory_runways": {},
        "overall_risk_score": 0.0,
        "risk_justification": "",
        "proposed_strategies": [],
        "strategy_evaluations": [],
        "negotiation_rounds": [],
        "negotiation_resolved": False,
        "negotiation_round_count": 0,
        "final_recommendation": None,
        "awaiting_human_approval": False,
        "human_decision": None,
        "human_notes": None,
        "agent_messages": [],
    }

    seen_messages = 0

    async def drain(stream):
        nonlocal seen_messages
        last_state = None
        async for state in stream:
            last_state = state
            messages = state.get("agent_messages", [])
            for message in messages[seen_messages:]:
                await session.queue.put(message)
            seen_messages = len(messages)
        return last_state

    try:
        # Phase 1: run to the HITL interrupt (before ops_manager)
        state = await drain(graph.astream(initial_state, thread_config, stream_mode="values"))

        snapshot = graph.get_state(thread_config)
        if snapshot.next:  # paused before ops_manager — resume so it can draft the recommendation
            state = await drain(graph.astream(None, thread_config, stream_mode="values"))

        recommendation = (state or {}).get("final_recommendation")
        if recommendation:
            await session.queue.put({"type": "hitl_required", "recommendation": recommendation})
            await session.decision_event.wait()
            graph.update_state(
                thread_config,
                {
                    "human_decision": session.decision,
                    "human_notes": session.notes,
                    "awaiting_human_approval": False,
                },
            )
            await session.queue.put(
                {
                    "agent": "ops_manager",
                    "message": (
                        f"Human decision recorded: **{session.decision.upper()}**"
                        + (f" — {session.notes}" if session.notes else "")
                    ),
                    "timestamp": _now(),
                }
            )
        else:
            await session.queue.put(
                {
                    "agent": "ops_manager",
                    "message": "Scenario closed at risk stage (risk score below escalation threshold).",
                    "timestamp": _now(),
                }
            )
    except Exception as exc:
        import traceback
        traceback.print_exc()  # <-- add this line
        await session.queue.put({"type": "error", "message": str(exc)})
    finally:
        session.done = True
        await session.queue.put(_SENTINEL)


@app.post("/api/scenario/trigger")
async def trigger_scenario(request: TriggerRequest):
    if request.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Unknown scenario {request.scenario_id}")
    session = Session(request.session_id)
    SESSIONS[request.session_id] = session
    asyncio.create_task(_run_scenario(session, request.scenario_id))
    return {"session_id": request.session_id, "status": "started"}


@app.get("/api/scenario/stream/{session_id}")
async def stream_scenario(session_id: str):
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session")

    async def event_generator():
        while True:
            item = await session.queue.get()
            yield f"data: {json.dumps(item)}\n\n"
            if item is _SENTINEL or item.get("type") == "complete":
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/api/decision/{session_id}")
async def submit_decision(session_id: str, request: DecisionRequest):
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Unknown session")
    if request.decision not in ("approve", "reject"):
        raise HTTPException(status_code=422, detail="decision must be 'approve' or 'reject'")
    session.decision = request.decision
    session.notes = request.notes
    session.decision_event.set()
    return {"status": "resumed"}


@app.get("/api/digital-twin/state")
async def digital_twin_state():
    client = get_client()
    suppliers = client.run_query(
        """
        MATCH (s:Supplier)-[rel:SUPPLIES]->(m:Material)
        RETURN s{.*} AS supplier, m.id AS material_id, rel.is_primary AS is_primary
        """
    )
    materials = client.run_query("MATCH (m:Material) RETURN m{.*} AS material")
    ports = client.run_query("MATCH (p:Port) RETURN p{.*} AS port")
    routes = client.run_query("MATCH (r:ShippingRoute) RETURN r{.*} AS route")
    events = client.run_query(
        "MATCH (e:DisruptionEvent {is_active: true}) RETURN e{.*} AS event"
    )
    factories = client.run_query("MATCH (f:Factory) RETURN f{.*} AS factory")
    warehouses = client.run_query("MATCH (w:Warehouse) RETURN w{.*} AS warehouse")
    company = client.run_query("MATCH (c:Company) RETURN c{.*} AS company")

    return {
        "suppliers": [
            {**r["supplier"], "material_id": r["material_id"], "is_primary": r["is_primary"]}
            for r in suppliers
        ],
        "materials": [r["material"] for r in materials],
        "ports": [r["port"] for r in ports],
        "routes": [r["route"] for r in routes],
        "events": [r["event"] for r in events],
        "factories": [r["factory"] for r in factories],
        "warehouses": [r["warehouse"] for r in warehouses],
        "company": company[0]["company"] if company else None,
    }


@app.get("/api/scenarios")
async def list_scenarios():
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "trigger_date": s["trigger_date"],
        }
        for s in SCENARIOS.values()
    ]


@app.get("/api/health")
async def health():
    mcp_status = await mcp_client.probe_mcp()
    return {
        "status": "ok",
        "neo4j": get_client().verify_connectivity(),
        "mcp": mcp_status["mcp"],
        "mcp_tools": mcp_status["mcp_tools"],
        "mcp_server_url": mcp_client.MCP_SERVER_URL,
        "mcp_enabled": mcp_client.MCP_ENABLED,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=config.BACKEND_HOST, port=config.BACKEND_PORT, reload=False)
