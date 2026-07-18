"""Single-agent Qwen baseline.

Fairness requirement: the baseline receives IDENTICAL information to the agent
society — the full supplier/port/route/material state and the active event
descriptions — serialised as text from the same seed constants ground_truth.py
uses. No tools, no graph traversal, no multi-step reasoning loop. One call,
one response, temperature 0 for reproducibility.
"""

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from config import qwen_chat_json                                      # noqa: E402
from database.seed import (                                            # noqa: E402
    DISRUPTION_EVENTS,
    EVAL_DISRUPTION_EVENTS,
    MATERIALS,
    PORTS,
    ROUTES,
    SUPPLIERS,
)

_ALL_EVENTS = {e["id"]: e for e in DISRUPTION_EVENTS + EVAL_DISRUPTION_EVENTS}

BASELINE_SYSTEM_PROMPT = """You are a supply chain risk analyst for Orbital Manufacturing Pte Ltd,
a Singapore-based precision electronics manufacturer.
Given the company's supplier network and a set of active disruption events, identify which suppliers
are affected and recommend mitigation strategies.
Respond ONLY in valid JSON, no preamble:
{
  "affected_suppliers": [
    {"supplier_id": str, "risk_level": "CRITICAL"|"HIGH"|"MEDIUM", "is_available": bool,
     "estimated_additional_delay_days": int}
  ],
  "recommended_strategies": [
    {"strategy_type": str, "material_id": str, "target_supplier_id": str,
     "quantity_units": int, "estimated_additional_cost_sgd": float}
  ],
  "highest_risk_material_id": str
}"""


def build_context(active_event_ids: list[str], world: dict | None = None) -> str:
    """Serialise the full network state as text. `world` optionally overrides
    per-scenario supplier availability and port/route disruption flags so the
    baseline sees exactly the same world state the agent society reads from
    Neo4j (information parity, provably from the same constants)."""
    world = world or {}
    supplier_available = world.get("supplier_available", {})
    port_state = world.get("port_state", {})
    route_state = world.get("route_state", {})

    lines = ["=== SUPPLIERS (24) ==="]
    for s in SUPPLIERS:
        available = supplier_available.get(s["id"], s["is_available"])
        lines.append(
            f"- {s['id']} | {s['name']} | country={s['country']} | material={s['material_id']} "
            f"| primary={s['is_primary']} | port={s['primary_port_id']} | route={s['route_id']} "
            f"| cost_per_unit_sgd={s['cost_per_unit_sgd']} | lead_time_days={s['lead_time_days']} "
            f"| capacity_per_month={s['capacity_units_per_month']} | quality={s['quality_tier']} "
            f"| reliability={s['reliability_score']} | is_available={available}"
        )

    lines.append("\n=== PORTS (16) ===")
    for p in PORTS:
        state = port_state.get(p["id"], {})
        disrupted = state.get("is_disrupted", p["is_disrupted"])
        severity = state.get("severity", p["disruption_severity"])
        lines.append(
            f"- {p['id']} | {p['name']} | {p['country']} | is_disrupted={disrupted} "
            f"| severity={severity}"
        )

    lines.append("\n=== SHIPPING ROUTES (13) ===")
    for r in ROUTES:
        state = route_state.get(r["id"], {})
        disrupted = state.get("is_disrupted", r["is_disrupted"])
        dtype = state.get("disruption_type", r["disruption_type"])
        transit = state.get("transit_days_current", r["transit_days_current"])
        lines.append(
            f"- {r['id']} | {r['name']} | mode={r['mode']} "
            f"| transit_days_normal={r['transit_days_normal']} | transit_days_current={transit} "
            f"| freight_normal_sgd={r['freight_cost_sgd_per_unit_normal']} "
            f"| hormuz={r['passes_through_hormuz']} | red_sea={r['passes_through_red_sea']} "
            f"| is_disrupted={disrupted} | disruption_type={dtype}"
        )

    lines.append("\n=== MATERIALS (6) ===")
    for m in MATERIALS:
        lines.append(
            f"- {m['id']} | {m['name']} | criticality={m['criticality']} "
            f"| monthly_demand={m['monthly_demand_units']} {m['unit']} "
            f"| inventory_days_remaining={m['current_inventory_days']} "
            f"| reorder_point_days={m['reorder_point_days']} "
            f"| revenue_per_unit_sgd={m['unit_revenue_contribution_sgd']}"
        )

    lines.append("\n=== ACTIVE DISRUPTION EVENTS ===")
    for event_id in active_event_ids:
        event = _ALL_EVENTS[event_id]
        lines.append(
            f"- {event['id']} | {event['name']} | type={event['type']} "
            f"| severity={event['severity']} | region={event['affected_region']} "
            f"| start={event['start_date']} | source={event['source']}\n"
            f"  {event['description']}"
        )

    return "\n".join(lines)


def run_baseline(active_event_ids: list[str], world: dict | None = None) -> dict:
    """Single Qwen call with the full serialised network state. Returns the
    parsed JSON dict (affected_suppliers, recommended_strategies,
    highest_risk_material_id)."""
    context = build_context(active_event_ids, world)
    payload = qwen_chat_json(
        BASELINE_SYSTEM_PROMPT,
        "Analyse the following network state and active disruptions.\n\n" + context,
        temperature=0.0,
    )
    if not isinstance(payload, dict):
        raise ValueError(f"Baseline returned non-dict payload: {type(payload)}")
    payload.setdefault("affected_suppliers", [])
    payload.setdefault("recommended_strategies", [])
    payload.setdefault("highest_risk_material_id", None)
    return payload
