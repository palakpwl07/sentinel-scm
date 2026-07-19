"""Live web search event extraction — constrained to the digital twin's graph.

Given free text (a headline, a query, or a pasted news snippet), searches the
live web via Qwen (enable_search) and extracts a structured DisruptionEvent
constrained to the actual region/port/supplier IDs in Neo4j. Returns None (not
an exception) if the search/extraction fails entirely — this means "search
failed, fall back to canned scenarios," while has_material_connection: false is
a valid, expected non-None outcome ("system correctly determined no impact").
"""

import json
import re
from datetime import datetime, timezone

from config import QWEN_MODEL, get_qwen_client
from database.neo4j_client import get_client

VALID_EVENT_TYPES = {"GEOPOLITICAL", "SHIPPING", "PORT", "SUPPLIER", "WEATHER"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM"}


def _fetch_graph_entity_reference() -> dict:
    """{id, name} pairs for all regions, ports, suppliers — the closed set that
    constrains the LLM's extraction to valid graph IDs. id/name only."""
    client = get_client()
    regions = client.run_query("MATCH (r:Region) RETURN r.id AS id, r.name AS name")
    ports = client.run_query("MATCH (p:Port) RETURN p.id AS id, p.name AS name")
    suppliers = client.run_query(
        "MATCH (s:Supplier) RETURN s.id AS id, s.name AS name, s.country AS country"
    )
    return {"regions": regions, "ports": ports, "suppliers": suppliers}


LIVE_SEARCH_SYSTEM_PROMPT = """You are the Monitoring Agent for Orbital Manufacturing's
supply chain control tower. You have live web search enabled.

Given a user's query (a headline, topic, or question about a current event), search the
web for the most recent, relevant, and factual information. Then determine whether this
event has a plausible material connection to Orbital Manufacturing's supply chain, using
ONLY the region/port/supplier reference list provided below — do not invent IDs that are
not in this list.

Reference list of valid graph entities:
{entity_reference}

Respond ONLY in valid JSON, no preamble, no markdown fences:
{{
  "has_material_connection": bool,
  "reasoning": "one sentence explaining the connection or lack thereof",
  "event": {{
    "name": "short event name",
    "type": "GEOPOLITICAL"|"SHIPPING"|"PORT"|"SUPPLIER"|"WEATHER",
    "severity": "CRITICAL"|"HIGH"|"MEDIUM",
    "description": "2-3 sentence factual summary of what you found via search",
    "source": "publication or outlet name",
    "source_url": "URL if available, else null",
    "start_date": "ISO date if known, else null",
    "affected_region_ids": ["..."],
    "affected_port_ids": ["..."],
    "directly_impacted_supplier_ids": ["..."]
  }}
}}

The affected_*_ids arrays must contain ONLY ids copied from the reference list, or be []
if none apply. If has_material_connection is false, still fill "event" with what you
found (for display), but leave the affected_*_ids arrays empty. Never fabricate a
connection to force a match."""


def extract_live_event(user_query: str) -> dict | None:
    """
    Search the live web for user_query and extract a structured event
    constrained to the graph's actual IDs. Returns the parsed payload dict, or
    None if the LLM call or JSON parse fails entirely — callers must treat None
    as "search failed, fall back to canned scenarios," NOT as "no event found."
    """
    entities = _fetch_graph_entity_reference()
    entity_text = json.dumps(entities, indent=2)

    client = get_qwen_client()
    try:
        response = client.chat.completions.create(
            model=QWEN_MODEL,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": LIVE_SEARCH_SYSTEM_PROMPT.format(entity_reference=entity_text),
                },
                {"role": "user", "content": user_query},
            ],
            extra_body={"enable_search": True},
        )
        raw = response.choices[0].message.content or ""
    except Exception:
        return None

    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    start = min(
        [i for i in (cleaned.find("{"), cleaned.find("[")) if i >= 0], default=-1
    )
    if start > 0:
        cleaned = cleaned[start:]

    try:
        payload = json.loads(cleaned)
    except Exception:
        return None

    if not isinstance(payload, dict) or "event" not in payload:
        return None
    return payload


def _validate_ids_against_graph(payload: dict, entities: dict) -> dict:
    """
    Defensive filter: drop any ID in the extracted event that isn't actually in
    the graph reference. The constrained prompt should prevent these, but LLM
    output is never trusted blindly — filter, don't crash.
    """
    valid_regions = {r["id"] for r in entities["regions"]}
    valid_ports = {p["id"] for p in entities["ports"]}
    valid_suppliers = {s["id"] for s in entities["suppliers"]}

    event = payload.get("event", {})
    event["affected_region_ids"] = [
        i for i in event.get("affected_region_ids", []) if i in valid_regions
    ]
    event["affected_port_ids"] = [
        i for i in event.get("affected_port_ids", []) if i in valid_ports
    ]
    event["directly_impacted_supplier_ids"] = [
        i for i in event.get("directly_impacted_supplier_ids", []) if i in valid_suppliers
    ]
    if event.get("type") not in VALID_EVENT_TYPES:
        event["type"] = "GEOPOLITICAL"
    if event.get("severity") not in VALID_SEVERITIES:
        event["severity"] = "MEDIUM"
    payload["event"] = event
    return payload


def write_live_event_to_graph(payload: dict) -> str:
    """
    Write the extracted event as a real DisruptionEvent node with AFFECTS /
    DIRECTLY_IMPACTS relationships, is_active=true. Returns the new event id
    (LIVE-{timestamp}). MERGE is used defensively on the generated id.
    """
    entities = _fetch_graph_entity_reference()
    payload = _validate_ids_against_graph(payload, entities)
    event = payload["event"]

    event_id = f"LIVE-{int(datetime.now(timezone.utc).timestamp())}"
    client = get_client()

    client.run_write(
        """
        MERGE (e:DisruptionEvent {id: $id})
        SET e.name = $name, e.type = $type, e.severity = $severity,
            e.affected_region = $region_summary, e.start_date = $start_date,
            e.source = $source, e.source_url = $source_url,
            e.description = $description, e.is_active = true
        """,
        {
            "id": event_id,
            "name": event.get("name") or "Live-searched event",
            "type": event["type"],
            "severity": event["severity"],
            "region_summary": ", ".join(event["affected_region_ids"]) or "n/a",
            "start_date": event.get("start_date")
            or datetime.now(timezone.utc).date().isoformat(),
            "source": event.get("source") or "Live web search",
            "source_url": event.get("source_url"),
            "description": event.get("description") or "",
        },
    )
    for region_id in event["affected_region_ids"]:
        client.run_write(
            "MATCH (e:DisruptionEvent {id: $eid}), (r:Region {id: $rid}) "
            "MERGE (e)-[:AFFECTS]->(r)",
            {"eid": event_id, "rid": region_id},
        )
    for port_id in event["affected_port_ids"]:
        client.run_write(
            "MATCH (e:DisruptionEvent {id: $eid}), (p:Port {id: $pid}) "
            "MERGE (e)-[:AFFECTS]->(p)",
            {"eid": event_id, "pid": port_id},
        )
    for supplier_id in event["directly_impacted_supplier_ids"]:
        client.run_write(
            "MATCH (e:DisruptionEvent {id: $eid}), (s:Supplier {id: $sid}) "
            "MERGE (e)-[:DIRECTLY_IMPACTS]->(s)",
            {"eid": event_id, "sid": supplier_id},
        )
    return event_id


def clear_live_events() -> int:
    """
    Deactivate all LIVE-* events (is_active=false, never deleted — consistent
    with how run_eval restores demo defaults). Called before each new live
    search and exposed as a manual reset. Returns the count deactivated.
    """
    records = get_client().run_query(
        "MATCH (e:DisruptionEvent) WHERE e.id STARTS WITH 'LIVE-' "
        "SET e.is_active = false RETURN count(e) AS n"
    )
    return records[0]["n"] if records else 0
