"""Planning Agent — proposes mitigation strategies for affected suppliers."""

import json
from datetime import datetime, timezone

from config import qwen_chat_json
from mcp_server.client import call_tool_sync
from mcp_server.tools.alternative_suppliers import find_alternative_suppliers

from .state import SupplyChainState

SYSTEM_PROMPT = """You are the Planning Agent for a precision electronics manufacturer. Given supply chain risks,
propose concrete mitigation strategies. Each strategy must include: type, target supplier,
quantity, urgency, and a clear business rationale. Be specific about trade-offs.
Respond ONLY in valid JSON as a list of MitigationStrategy objects. No preamble."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _enrich_with_qwen(strategies: list[dict], context: str) -> list[dict]:
    """Ask Qwen to write description/rationale for each strategy; fall back to templates."""
    try:
        payload = qwen_chat_json(
            SYSTEM_PROMPT,
            "For each strategy below, return the same list with improved 'description' and "
            "'rationale' fields (keep every other field unchanged).\n\n"
            f"Risk context:\n{context}\n\nStrategies:\n{json.dumps(strategies, indent=2)}",
        )
        if isinstance(payload, list) and len(payload) == len(strategies):
            for original, enriched in zip(strategies, payload):
                if isinstance(enriched, dict):
                    original["description"] = enriched.get("description", original["description"])
                    original["rationale"] = enriched.get("rationale", original["rationale"])
    except Exception:
        pass
    return strategies


def planning_agent(state: SupplyChainState) -> dict:
    strategies: list[dict] = []
    counter = 0
    lines = ["Proposed mitigation strategies:"]

    critical = [
        s for s in state["affected_suppliers"]
        if not s["is_available"] or s["risk_level"] == "CRITICAL"
    ]
    moderate = [
        s for s in state["affected_suppliers"]
        if s["is_available"]
        and s["risk_level"] in ("HIGH", "MEDIUM")
        and 0 < s["estimated_additional_delay_days"] < 999
    ]

    handled_materials: set[str] = set()

    for supplier in critical:
        material_id = supplier["material_id"]
        if material_id in handled_materials:
            continue
        handled_materials.add(material_id)

        excluded = [
            s["supplier_id"] for s in state["affected_suppliers"]
            if s["material_id"] == material_id
        ]
        alternatives = call_tool_sync(
            "find_alternative_suppliers_tool",
            {"material_id": material_id, "excluded_supplier_ids": excluded},
            fallback_fn=lambda m=material_id, e=excluded: find_alternative_suppliers(m, e),
        )
        if not alternatives:
            lines.append(f"- {material_id}: NO viable alternatives found — flagged for arbitration")
            continue

        runway = state["inventory_runways"].get(material_id, {})
        urgency = int(runway.get("days_remaining", 14))
        bridge_units = int(runway.get("units_needed_30_day_bridge", 0)) or int(
            runway.get("monthly_demand", 1000)
        )

        fastest = min(alternatives, key=lambda a: a["lead_time_days"])
        cheapest = alternatives[0]  # already ranked by cost ascending

        counter += 1
        strategies.append(
            {
                "strategy_id": f"STRAT-{counter:03d}",
                "strategy_type": "air_freight",
                "material_id": material_id,
                "target_supplier_id": fastest["supplier_id"],
                "description": (
                    f"Air freight {bridge_units:,} units of {material_id} from "
                    f"{fastest['name']} ({fastest['lead_time_days']}-day lead time)."
                ),
                "rationale": (
                    f"Aggressive bridge: inventory runway is {urgency} days; air freight from the "
                    f"fastest unaffected supplier closes the gap before stockout."
                ),
                "quantity_units": bridge_units,
                "urgency_days": urgency,
            }
        )
        counter += 1
        strategies.append(
            {
                "strategy_id": f"STRAT-{counter:03d}",
                "strategy_type": "switch_supplier",
                "material_id": material_id,
                "target_supplier_id": cheapest["supplier_id"],
                "description": (
                    f"Switch {material_id} sourcing to {cheapest['name']} "
                    f"({cheapest['lead_time_days']}-day lead time, "
                    f"SGD {cheapest['cost_per_unit_sgd']}/unit) and build safety stock."
                ),
                "rationale": (
                    "Conservative: requalify the cheapest available alternative on standard sea "
                    "freight; slower but sustainable for the duration of the disruption."
                ),
                "quantity_units": int(runway.get("monthly_demand", bridge_units)),
                "urgency_days": urgency,
            }
        )
        lines.append(
            f"- {material_id}: air freight via {fastest['name']} (aggressive) / "
            f"switch to {cheapest['name']} (conservative)"
        )

    for supplier in moderate:
        material_id = supplier["material_id"]
        if material_id in handled_materials:
            continue
        handled_materials.add(material_id)

        runway = state["inventory_runways"].get(material_id, {})
        urgency = int(runway.get("days_remaining", 21))
        buffer_units = int(round(runway.get("monthly_demand", 1000) * 0.5))

        counter += 1
        strategies.append(
            {
                "strategy_id": f"STRAT-{counter:03d}",
                "strategy_type": "safety_stock",
                "material_id": material_id,
                "target_supplier_id": supplier["supplier_id"],
                "description": (
                    f"Increase {material_id} safety stock by {buffer_units:,} units to absorb "
                    f"the +{supplier['estimated_additional_delay_days']}-day reroute delay."
                ),
                "rationale": (
                    f"Supplier {supplier['supplier_name']} remains available but rerouted "
                    f"(+{supplier['estimated_additional_delay_days']} days). A larger buffer "
                    "avoids a costlier supplier switch."
                ),
                "quantity_units": buffer_units,
                "urgency_days": urgency,
            }
        )
        lines.append(
            f"- {material_id}: +{buffer_units:,} units safety stock "
            f"(reroute +{supplier['estimated_additional_delay_days']}d)"
        )

    strategies = _enrich_with_qwen(strategies, state.get("risk_justification", ""))

    return {
        "proposed_strategies": strategies,
        "agent_messages": [
            {"agent": "planning", "message": "\n".join(lines), "timestamp": _now()}
        ],
    }
