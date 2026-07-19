"""Finance Agent — evaluates every proposed strategy through the cost model."""

from datetime import datetime, timezone

import config
from mcp_server.client import call_tool_sync
from mcp_server.tools.mitigation_cost import evaluate_mitigation_cost

from .state import SupplyChainState


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finance_agent(state: SupplyChainState) -> dict:
    evaluations = []
    lines = [
        "Financial evaluation of proposed strategies:",
        "| Strategy | Type | Cost (SGD) | Revenue protected | Net benefit | Margin impact | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]

    for strategy in state["proposed_strategies"]:
        try:
            result = call_tool_sync(
                "evaluate_mitigation_cost_tool",
                {
                    "strategy_type": strategy["strategy_type"],
                    "material_id": strategy["material_id"],
                    "target_supplier_id": strategy.get("target_supplier_id") or "",
                    "quantity_units": strategy["quantity_units"],
                    "urgency_days": strategy["urgency_days"],
                },
                fallback_fn=lambda s=strategy: evaluate_mitigation_cost(
                    s["strategy_type"], s["material_id"], s.get("target_supplier_id") or "",
                    s["quantity_units"], s["urgency_days"],
                ),
            )
        except Exception as exc:
            result = {
                "additional_cost_sgd": 0.0,
                "revenue_protected_sgd": 0.0,
                "net_benefit_sgd": 0.0,
                "margin_impact_pct": 0.0,
                "recommendation_reason": f"Evaluation failed: {exc}",
            }

        margin = result["margin_impact_pct"]
        net = result["net_benefit_sgd"]
        if margin > config.MARGIN_IMPACT_THRESHOLD_PCT and net < 0:
            recommendation = "REJECT"
        elif margin > config.MARGIN_IMPACT_THRESHOLD_PCT and net > 0:
            recommendation = "CONDITIONAL"
        elif margin <= config.MARGIN_IMPACT_THRESHOLD_PCT and net > 0:
            recommendation = "APPROVE"
        else:
            recommendation = "REJECT"

        evaluations.append(
            {
                "strategy_id": strategy["strategy_id"],
                "additional_cost_sgd": result["additional_cost_sgd"],
                "revenue_protected_sgd": result["revenue_protected_sgd"],
                "net_benefit_sgd": result["net_benefit_sgd"],
                "margin_impact_pct": result["margin_impact_pct"],
                "finance_recommendation": recommendation,
                "finance_notes": result.get("recommendation_reason", ""),
            }
        )
        lines.append(
            f"| {strategy['strategy_id']} | {strategy['strategy_type']} | "
            f"{result['additional_cost_sgd']:,.0f} | {result['revenue_protected_sgd']:,.0f} | "
            f"{result['net_benefit_sgd']:,.0f} | {result['margin_impact_pct']:.2f}% | "
            f"{recommendation} |"
        )

    rejected = [e for e in evaluations if e["finance_recommendation"] == "REJECT"]
    round_count = state.get("negotiation_round_count", 0)
    if rejected:
        round_count += 1
        lines.append(
            f"\n{len(rejected)} strategy(ies) REJECTED — escalating to negotiation "
            f"(round count now {round_count})."
        )
    else:
        lines.append("\nAll strategies APPROVE/CONDITIONAL — no negotiation needed.")

    return {
        "strategy_evaluations": evaluations,
        "negotiation_round_count": round_count,
        "agent_messages": [
            {"agent": "finance", "message": "\n".join(lines), "timestamp": _now()}
        ],
    }
