"""Monitoring Agent — detects disruption events and their blast radius."""

from datetime import datetime, timezone

from config import qwen_chat
from database.neo4j_client import get_client
from scenarios.march_2026 import SCENARIOS

from .state import SupplyChainState

SYSTEM_PROMPT = """You are the Monitoring Agent for Orbital Manufacturing's supply chain control tower.
Your job is to identify supply chain disruption events and extract structured information.
Given event descriptions, identify: event type, severity, affected regions, affected ports.
Respond ONLY in valid JSON matching the DetectedEvent schema. No preamble."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def monitoring_agent(state: SupplyChainState) -> dict:
    scenario = SCENARIOS.get(state["scenario_id"])
    active_event_ids = scenario["active_event_ids"] if scenario else []
    event_description = (
        scenario["event_description"] if scenario else state.get("event_description", "")
    )

    records = get_client().run_query(
        """
        MATCH (e:DisruptionEvent)
        WHERE e.id IN $event_ids AND e.is_active = true
        OPTIONAL MATCH (e)-[:AFFECTS]->(r:Region)
        OPTIONAL MATCH (e)-[:AFFECTS]->(p:Port)
        RETURN e,
               [x IN collect(DISTINCT r.name) WHERE x IS NOT NULL] AS regions,
               [x IN collect(DISTINCT p.name) WHERE x IS NOT NULL] AS ports
        ORDER BY e.start_date
        """,
        {"event_ids": active_event_ids},
    )

    detected_events = []
    affected_regions: set[str] = set()
    affected_ports: set[str] = set()
    for record in records:
        event = record["e"]
        detected_events.append(
            {
                "event_id": event["id"],
                "name": event["name"],
                "severity": event["severity"],
                "affected_regions": record["regions"],
                "affected_ports": record["ports"],
                "source": event["source"],
            }
        )
        affected_regions.update(record["regions"])
        affected_ports.update(record["ports"])

    try:
        summary = qwen_chat(
            SYSTEM_PROMPT,
            "Summarise these active disruption events in 2-3 sentences of plain English "
            "for an operations dashboard, then stop. Events:\n"
            + "\n".join(
                f"- {e['name']} ({e['severity']}): regions {e['affected_regions']}, "
                f"ports {e['affected_ports']}"
                for e in detected_events
            )
            + f"\n\nContext: {event_description}",
        )
    except Exception:
        summary = (
            f"Detected {len(detected_events)} active disruption events: "
            + "; ".join(f"{e['name']} [{e['severity']}]" for e in detected_events)
            + f". Affected regions: {', '.join(sorted(affected_regions))}. "
            f"Affected ports: {', '.join(sorted(affected_ports))}."
        )

    return {
        "detected_events": detected_events,
        "affected_regions": sorted(affected_regions),
        "affected_ports": sorted(affected_ports),
        "event_description": event_description,
        "agent_messages": [
            {"agent": "monitoring", "message": summary, "timestamp": _now()}
        ],
    }
