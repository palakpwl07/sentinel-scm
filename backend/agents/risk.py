"""Risk Assessment Agent — supplier impact + inventory runway + overall score."""

from datetime import datetime, timezone

from database.neo4j_client import get_client
from mcp_server.client import call_tool_sync
from mcp_server.tools.inventory_runway import calculate_inventory_runway
from mcp_server.tools.supplier_risk import assess_supplier_risk
from scenarios.march_2026 import SCENARIOS

from .state import SupplyChainState

ALL_MATERIAL_IDS = ["MAT-IC", "MAT-HE", "MAT-SC", "MAT-PM", "MAT-PB", "MAT-OC"]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def risk_agent(state: SupplyChainState) -> dict:
    scenario = SCENARIOS.get(state["scenario_id"])
    active_event_ids = scenario["active_event_ids"] if scenario else [
        e["event_id"] for e in state.get("detected_events", [])
    ]

    supplier_records = get_client().run_query(
        """
        MATCH (s:Supplier)-[rel:SUPPLIES]->(m:Material)
        RETURN s.id AS supplier_id, s.name AS supplier_name,
               m.id AS material_id, m.criticality AS criticality,
               rel.is_primary AS is_primary
        """
    )

    inventory_runways = call_tool_sync(
        "calculate_inventory_runway_tool",
        {"material_ids": ALL_MATERIAL_IDS},
        fallback_fn=lambda: calculate_inventory_runway(ALL_MATERIAL_IDS),
    )

    affected_suppliers = []
    score = 0.0
    critical_component = 0.0
    justification_parts = []

    for record in supplier_records:
        assessment = call_tool_sync(
            "assess_supplier_risk_tool",
            {"supplier_id": record["supplier_id"], "active_event_ids": active_event_ids},
            fallback_fn=lambda r=record: assess_supplier_risk(
                r["supplier_id"], active_event_ids
            ),
        )
        if assessment["risk_level"] in ("LOW", "UNKNOWN"):
            continue

        runway = inventory_runways.get(record["material_id"], {})
        affected_suppliers.append(
            {
                "supplier_id": record["supplier_id"],
                "material_id": record["material_id"],
                "supplier_name": record["supplier_name"],
                "risk_level": assessment["risk_level"],
                "is_available": assessment["is_available"],
                "estimated_additional_delay_days": assessment[
                    "estimated_additional_delay_days"
                ],
                "inventory_runway_days": runway.get("days_remaining", 0),
            }
        )

        criticality = record["criticality"]
        is_primary = bool(record["is_primary"])
        if criticality == "CRITICAL" and is_primary and not assessment["is_available"]:
            critical_component = min(critical_component + 0.35, 0.70)
            justification_parts.append(
                f"CRITICAL material {record['material_id']} primary supplier "
                f"{record['supplier_name']} unavailable (+0.35)"
            )
        elif criticality == "HIGH" and (
            not assessment["is_available"]
            or assessment["estimated_additional_delay_days"] > 0
        ):
            score += 0.15
            justification_parts.append(
                f"HIGH material {record['material_id']} supplier "
                f"{record['supplier_name']} disrupted (+0.15)"
            )
        elif criticality == "MEDIUM":
            score += 0.05
            justification_parts.append(
                f"MEDIUM material {record['material_id']} supplier "
                f"{record['supplier_name']} affected (+0.05)"
            )

    overall_risk_score = min(score + critical_component, 1.0)
    risk_justification = (
        f"Overall risk score {overall_risk_score:.2f}. Contributions: "
        + "; ".join(justification_parts)
        if justification_parts
        else "No significant supplier disruption detected."
    )

    lines = [
        "Supplier risk assessment:",
        "| Supplier | Material | Risk | Available | Delay (days) | Runway (days) |",
        "|---|---|---|---|---|---|",
    ]
    for s in affected_suppliers:
        lines.append(
            f"| {s['supplier_name']} | {s['material_id']} | {s['risk_level']} | "
            f"{'yes' if s['is_available'] else 'NO'} | "
            f"{s['estimated_additional_delay_days']} | {s['inventory_runway_days']} |"
        )
    lines.append(f"\nOverall risk score: **{overall_risk_score:.2f}** — {risk_justification}")

    return {
        "affected_suppliers": affected_suppliers,
        "inventory_runways": inventory_runways,
        "overall_risk_score": overall_risk_score,
        "risk_justification": risk_justification,
        "agent_messages": [
            {"agent": "risk", "message": "\n".join(lines), "timestamp": _now()}
        ],
    }
