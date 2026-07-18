"""Independent ground-truth computation for the eval harness.

HARD CONSTRAINT: this module imports NOTHING from mcp_server/ or agents/.
It reimplements the disruption-propagation domain rules in plain Python over
the seed data constants — no Neo4j, no Cypher, no LLM. Disagreement between
this module and the system under test indicates a real bug in the Cypher/agent
layer, which is exactly what the eval is designed to surface.
"""

import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import config  # constants only: cost-model parameters                 # noqa: E402
from database.seed import (                                            # noqa: E402
    DISRUPTION_EVENTS,
    EVAL_DISRUPTION_EVENTS,
    EVENT_AFFECTS_PORTS,
    EVENT_AFFECTS_REGIONS,
    EVENT_AFFECTS_ROUTES,
    EVENT_IMPACTS_SUPPLIERS,
    MATERIALS,
    PORTS,
    REGIONS,
    ROUTES,
    SUPPLIERS,
)

_SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
_RANK_SEVERITY = {v: k for k, v in _SEVERITY_RANK.items()}

# Delay estimates for port/region paths where the spec prescribes no formula.
# Route paths use the spec's explicit rules (BLOCKED=999, REROUTED=delta).
_PATH_DELAY_BY_SEVERITY = {"CRITICAL": 999, "HIGH": 14, "MEDIUM": 7}

ALL_EVENTS = {e["id"]: e for e in DISRUPTION_EVENTS + EVAL_DISRUPTION_EVENTS}
_PORTS_BY_ID = {p["id"]: p for p in PORTS}
_ROUTES_BY_ID = {r["id"]: r for r in ROUTES}
_MATERIALS_BY_ID = {m["id"]: m for m in MATERIALS}
_SUPPLIERS_BY_ID = {s["id"]: s for s in SUPPLIERS}


def event_wiring(event_id: str) -> dict:
    """Unified AFFECTS/DIRECTLY_IMPACTS wiring for demo and eval events."""
    event = ALL_EVENTS[event_id]
    if "affects_ports" in event:  # eval events carry wiring inline
        return {
            "regions": list(event["affects_regions"]),
            "ports": list(event["affects_ports"]),
            "routes": [],
            "suppliers": list(event["directly_impacts"]),
        }
    return {
        "regions": EVENT_AFFECTS_REGIONS.get(event_id, []),
        "ports": EVENT_AFFECTS_PORTS.get(event_id, []),
        "routes": EVENT_AFFECTS_ROUTES.get(event_id, []),
        "suppliers": EVENT_IMPACTS_SUPPLIERS.get(event_id, []),
    }


def _port_path_severity(port_id: str, event: dict) -> str:
    """Rule 4 keys off the port's disruption_severity; novel events hit ports
    whose seeded severity is null, so fall back to the event's own severity."""
    seeded = _PORTS_BY_ID[port_id].get("disruption_severity")
    return seeded or event["severity"]


def compute_affected_suppliers(active_event_ids: list[str]) -> dict[str, dict]:
    """
    Independently compute which suppliers are affected by a given event set.
    Uses plain Python over seed data constants. No Neo4j, no Cypher, no LLM.

    Propagation rules (domain logic, NOT the Cypher implementation):
      1. DIRECT:  event DIRECTLY_IMPACTS supplier          => UNAVAILABLE, CRITICAL
      2. REGION:  region hit by a CRITICAL-severity event  => UNAVAILABLE, CRITICAL
      3. REGION:  region hit by HIGH/MEDIUM event          => risk HIGH/MEDIUM
      4. PORT:    primary port hit by an event
                    - port disruption_severity CRITICAL    => risk CRITICAL
                    - HIGH                                 => risk HIGH
      5. ROUTE:   supplier's route disrupted by an active event
                    - BLOCKED   => delay 999, risk CRITICAL
                    - REROUTED  => delay = transit_current - transit_normal, risk HIGH

    Risk level is the MAX severity across all matching paths.
    """
    results: dict[str, dict] = {}
    active_events = [ALL_EVENTS[eid] for eid in active_event_ids if eid in ALL_EVENTS]

    for supplier in SUPPLIERS:
        risk_rank = 0
        delay = 0
        unavailable = False
        reason_paths: list[str] = []

        for event in active_events:
            wiring = event_wiring(event["id"])
            event_rank = _SEVERITY_RANK.get(event["severity"], 1)

            # Rule 1: DIRECT
            if supplier["id"] in wiring["suppliers"]:
                unavailable = True
                risk_rank = max(risk_rank, _SEVERITY_RANK["CRITICAL"])
                delay = max(delay, 999)
                if "direct" not in reason_paths:
                    reason_paths.append("direct")

            # Rules 2 & 3: REGION
            if supplier["region_id"] in wiring["regions"]:
                if event["severity"] == "CRITICAL":
                    unavailable = True
                    risk_rank = max(risk_rank, _SEVERITY_RANK["CRITICAL"])
                    delay = max(delay, 999)
                else:
                    risk_rank = max(risk_rank, event_rank)
                    delay = max(delay, _PATH_DELAY_BY_SEVERITY.get(event["severity"], 7))
                if "region" not in reason_paths:
                    reason_paths.append("region")

            # Rule 4: PORT
            if supplier["primary_port_id"] in wiring["ports"]:
                severity = _port_path_severity(supplier["primary_port_id"], event)
                risk_rank = max(risk_rank, _SEVERITY_RANK.get(severity, 1))
                delay = max(delay, _PATH_DELAY_BY_SEVERITY.get(severity, 7))
                if "port" not in reason_paths:
                    reason_paths.append("port")

            # Rule 5: ROUTE
            if supplier["route_id"] in wiring["routes"]:
                route = _ROUTES_BY_ID[supplier["route_id"]]
                if route["is_disrupted"]:
                    if route["disruption_type"] == "BLOCKED":
                        risk_rank = max(risk_rank, _SEVERITY_RANK["CRITICAL"])
                        delay = max(delay, 999)
                    elif route["disruption_type"] == "REROUTED":
                        risk_rank = max(risk_rank, _SEVERITY_RANK["HIGH"])
                        delay = max(
                            delay,
                            int(route["transit_days_current"]) - int(route["transit_days_normal"]),
                        )
                    if "route" not in reason_paths:
                        reason_paths.append("route")

        results[supplier["id"]] = {
            "affected": risk_rank > 0,
            "is_available": not unavailable,
            "risk_level": _RANK_SEVERITY[risk_rank] if risk_rank > 0 else "LOW",
            "expected_delay_days": delay,
            "reason_paths": reason_paths,
        }
    return results


def compute_true_mitigation_cost(
    strategy_type: str,
    material_id: str,
    target_supplier_id: str,
    quantity_units: int,
    urgency_days: int,
) -> float:
    """
    Independently compute the correct additional cost for a strategy, using the
    same business rules as the config.py constants but computed in plain Python
    from seed data (not via the MCP tool). Returns additional_cost_sgd.
    """
    material = _MATERIALS_BY_ID[material_id]
    target = _SUPPLIERS_BY_ID.get(target_supplier_id, {})
    route = _ROUTES_BY_ID.get(target.get("route_id", ""), {})
    primary = next(
        (s for s in SUPPLIERS if s["material_id"] == material_id and s["is_primary"]),
        None,
    )

    monthly_demand = int(material["monthly_demand_units"])
    revenue_per_unit = float(material["unit_revenue_contribution_sgd"])
    unit_cost = float(target.get("cost_per_unit_sgd", 0.0) or 0.0)
    primary_cost = float(primary["cost_per_unit_sgd"]) if primary else unit_cost

    if strategy_type == "air_freight":
        sea_freight = float(route.get("freight_cost_sgd_per_unit_normal", 2.0) or 2.0)
        cost = sea_freight * config.AIR_FREIGHT_MULTIPLIER * quantity_units
        cost += max(0.0, unit_cost - primary_cost) * quantity_units
    elif strategy_type == "switch_supplier":
        cost = (unit_cost - primary_cost) * monthly_demand * 1
    elif strategy_type == "safety_stock":
        cost = (
            quantity_units
            * unit_cost
            * config.CARRYING_COST_PCT_ANNUAL
            / 365.0
            * max(urgency_days, 30)
        )
        cost += max(0.0, unit_cost - primary_cost) * quantity_units
    elif strategy_type == "delay_production":
        cost = monthly_demand / 30.0 * revenue_per_unit * urgency_days
    elif strategy_type == "reallocate_inventory":
        cost = config.REALLOCATION_FIXED_COST_SGD
    else:
        raise ValueError(f"Unknown strategy_type: {strategy_type}")

    return round(max(cost, 0.0), 2)


def compute_highest_risk_material(active_event_ids: list[str]) -> str:
    """
    Which material has the greatest revenue at risk given this event set?
    revenue_at_risk = units_short * unit_revenue_contribution_sgd, where
    units_short is driven by inventory runway vs. the lead time of the best
    available alternative (lead time + any propagation delay). Only materials
    with at least one event-affected supplier are ranked — a material whose
    supply base is untouched by the event set carries no event-driven risk.
    Ties break toward the tightest runway-vs-lead-time slack. Used for
    decision-quality scoring.
    """
    affected = compute_affected_suppliers(active_event_ids)

    touched_materials = {
        s["material_id"] for s in SUPPLIERS if affected[s["id"]]["affected"]
    }
    candidates_pool = [
        m for m in MATERIALS if m["id"] in touched_materials
    ] or MATERIALS

    best_material = candidates_pool[0]["id"]
    best_key = (-1.0, float("-inf"))

    for material in candidates_pool:
        candidates = []
        for supplier in SUPPLIERS:
            if supplier["material_id"] != material["id"]:
                continue
            verdict = affected[supplier["id"]]
            if not verdict["is_available"] or verdict["risk_level"] == "CRITICAL":
                continue
            delay = verdict["expected_delay_days"] if verdict["expected_delay_days"] < 999 else 0
            candidates.append(int(supplier["lead_time_days"]) + delay)

        runway = int(material["current_inventory_days"])
        if candidates:
            best_lead = min(candidates)
            gap_days = max(0, best_lead - runway)
        else:
            best_lead = 30 + runway  # no viable supplier at all: a full month exposed
            gap_days = 30

        units_short = min(
            int(material["monthly_demand_units"]),
            round(gap_days / 30.0 * material["monthly_demand_units"]),
        )
        revenue_at_risk = units_short * float(material["unit_revenue_contribution_sgd"])
        key = (revenue_at_risk, best_lead - runway)

        if key > best_key:
            best_key = key
            best_material = material["id"]

    return best_material
