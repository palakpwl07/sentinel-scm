"""Operations Manager Agent — weighted arbitration and final recommendation."""

import json
from datetime import datetime, timezone

from config import qwen_chat_json

from .state import SupplyChainState

SYSTEM_PROMPT = """You are the Operations Manager Agent — the final decision-maker in a supply chain AI system.
Synthesise inputs from Monitoring, Risk, Planning, and Finance agents.
Produce a final recommendation that a VP of Operations could act on immediately.
Every claim must be traceable to evidence. Be specific about costs, timelines, and confidence.
Respond ONLY in valid JSON matching the FinalRecommendation schema. No preamble."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _arbitration_score(state: SupplyChainState, strategy: dict, evaluation: dict) -> float:
    risk_score = state.get("overall_risk_score", 0.5)
    costs = [abs(e["additional_cost_sgd"]) for e in state["strategy_evaluations"]] or [1.0]
    max_cost = max(max(costs), 1.0)
    cost_impact_normalised = abs(evaluation["additional_cost_sgd"]) / max_cost
    runway = state["inventory_runways"].get(strategy["material_id"], {})
    timeline_criticality = 1.0 if runway.get("days_remaining", 99) < 10 else 0.5
    return (
        risk_score * 0.5
        + (1 - cost_impact_normalised) * 0.3
        + timeline_criticality * 0.2
    )


def _build_evidence(state: SupplyChainState, accepted: list[dict]) -> list[dict]:
    evidence = []
    for event in state.get("detected_events", []):
        evidence.append(
            {
                "source": f"{event['source']} ({event['event_id']})",
                "fact": f"{event['name']} — severity {event['severity']}",
                "impact": (
                    f"Affects regions {', '.join(event['affected_regions']) or 'n/a'} "
                    f"and ports {', '.join(event['affected_ports']) or 'n/a'}"
                ),
            }
        )
    for material_id, runway in state.get("inventory_runways", {}).items():
        if runway.get("is_critical"):
            evidence.append(
                {
                    "source": "Digital Twin — inventory data",
                    "fact": (
                        f"{runway['material_name']} inventory: {runway['days_remaining']} days "
                        f"remaining, reorder point: {runway['reorder_point_days']} days"
                    ),
                    "impact": (
                        f"Stockout on {runway['stockout_date']} without intervention — "
                        f"SGD {runway['at_risk_revenue_sgd']:,.0f} revenue at risk"
                    ),
                }
            )
    for item in accepted:
        strategy, evaluation = item["strategy"], item["evaluation"]
        evidence.append(
            {
                "source": "Finance Agent evaluation",
                "fact": (
                    f"{strategy['strategy_id']} ({strategy['strategy_type']}, "
                    f"{strategy['material_id']}): additional cost "
                    f"SGD {evaluation['additional_cost_sgd']:,.0f}"
                ),
                "impact": (
                    f"Protects SGD {evaluation['revenue_protected_sgd']:,.0f} revenue "
                    f"(net benefit SGD {evaluation['net_benefit_sgd']:,.0f})"
                ),
            }
        )
    return evidence


def ops_manager_agent(state: SupplyChainState) -> dict:
    evaluations_by_id = {e["strategy_id"]: e for e in state["strategy_evaluations"]}
    accepted, arbitrated = [], []

    for strategy in state["proposed_strategies"]:
        evaluation = evaluations_by_id.get(strategy["strategy_id"])
        if evaluation is None:
            continue
        if evaluation["finance_recommendation"] in ("APPROVE", "CONDITIONAL"):
            accepted.append({"strategy": strategy, "evaluation": evaluation})
        else:
            score = _arbitration_score(state, strategy, evaluation)
            arbitrated.append(
                {"strategy": strategy, "evaluation": evaluation, "score": score}
            )
            if score >= 0.6:
                accepted.append({"strategy": strategy, "evaluation": evaluation})

    total_cost = round(sum(i["evaluation"]["additional_cost_sgd"] for i in accepted), 2)
    total_revenue = round(sum(i["evaluation"]["revenue_protected_sgd"] for i in accepted), 2)
    net_benefit = round(total_revenue - total_cost, 2)
    primary_actions = [i["strategy"]["description"] for i in accepted]
    evidence = _build_evidence(state, accepted)
    confidence = round(
        min(0.95, 0.6 + 0.1 * len(accepted) + 0.15 * (state.get("overall_risk_score", 0) > 0.5)),
        2,
    )

    fallback = {
        "decision": (
            f"Execute {len(accepted)} mitigation strategies covering "
            f"{len({i['strategy']['material_id'] for i in accepted})} materials at a total "
            f"additional cost of SGD {total_cost:,.0f}, protecting "
            f"SGD {total_revenue:,.0f} in revenue."
        ),
        "primary_actions": primary_actions,
        "evidence": evidence,
        "confidence_score": confidence,
        "additional_cost_sgd": total_cost,
        "revenue_protected_sgd": total_revenue,
        "net_benefit_sgd": net_benefit,
        "requires_human_approval": True,
    }

    try:
        payload = qwen_chat_json(
            SYSTEM_PROMPT,
            "Produce the FinalRecommendation JSON. Use ONLY these figures — do not invent "
            "numbers.\n\n"
            f"Detected events: {json.dumps(state.get('detected_events', []))}\n"
            f"Risk justification: {state.get('risk_justification', '')}\n"
            f"Accepted strategies: {json.dumps([i['strategy'] for i in accepted])}\n"
            f"Evaluations: {json.dumps([i['evaluation'] for i in accepted])}\n"
            f"Arbitrated (weighted-score) items: "
            f"{json.dumps([{**{'strategy_id': a['strategy']['strategy_id']}, 'score': a['score']} for a in arbitrated])}\n"
            f"Totals: cost={total_cost}, revenue_protected={total_revenue}, net={net_benefit}\n"
            f"Evidence list to include verbatim: {json.dumps(evidence)}",
        )
        final_recommendation = {
            "decision": payload.get("decision", fallback["decision"]),
            "primary_actions": payload.get("primary_actions", primary_actions),
            "evidence": payload.get("evidence", evidence),
            "confidence_score": float(payload.get("confidence_score", confidence)),
            "additional_cost_sgd": total_cost,
            "revenue_protected_sgd": total_revenue,
            "net_benefit_sgd": net_benefit,
            "requires_human_approval": True,
        }
    except Exception:
        final_recommendation = fallback

    message = (
        "Final recommendation (pending human approval):\n"
        f"**Decision**: {final_recommendation['decision']}\n"
        + "\n".join(f"- {a}" for a in final_recommendation["primary_actions"])
        + f"\n\nAdditional cost: SGD {total_cost:,.0f} | Revenue protected: "
        f"SGD {total_revenue:,.0f} | Net benefit: SGD {net_benefit:,.0f} | "
        f"Confidence: {final_recommendation['confidence_score']:.2f}"
    )

    return {
        "final_recommendation": final_recommendation,
        "awaiting_human_approval": True,
        "agent_messages": [
            {"agent": "ops_manager", "message": message, "timestamp": _now()}
        ],
    }
