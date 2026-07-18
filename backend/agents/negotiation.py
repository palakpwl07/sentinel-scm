"""Negotiation node — structured Planning↔Finance loop for rejected strategies."""

from datetime import datetime, timezone

from config import qwen_chat

from .state import SupplyChainState

QUANTITY_REDUCTION_PCT = 0.30

PLANNING_NEG_PROMPT = """You are the Planning Agent in a negotiation with the Finance Agent.
A mitigation strategy you proposed was rejected on cost grounds. Propose a concrete
counter-proposal (e.g., partial air freight instead of full, phased ordering).
Reply in 2-3 sentences, business tone, no JSON."""

FINANCE_NEG_PROMPT = """You are the Finance Agent responding to a Planning counter-proposal.
State whether the reduced-scope proposal is financially acceptable and why, referencing
cost and margin impact. Reply in 2-3 sentences, business tone, no JSON."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def negotiation_round(state: SupplyChainState) -> dict:
    round_number = state.get("negotiation_round_count", 0)
    rejected_ids = {
        e["strategy_id"]
        for e in state["strategy_evaluations"]
        if e["finance_recommendation"] == "REJECT"
    }

    updated_strategies = []
    adjusted_names = []
    for strategy in state["proposed_strategies"]:
        if strategy["strategy_id"] in rejected_ids:
            reduced = dict(strategy)
            reduced["quantity_units"] = int(
                round(strategy["quantity_units"] * (1 - QUANTITY_REDUCTION_PCT))
            )
            reduced["description"] += (
                f" [Negotiated round {round_number + 1}: quantity reduced 30% to "
                f"{reduced['quantity_units']:,} units]"
            )
            updated_strategies.append(reduced)
            adjusted_names.append(
                f"{strategy['strategy_id']} ({strategy['strategy_type']} for "
                f"{strategy['material_id']}): {strategy['quantity_units']:,} → "
                f"{reduced['quantity_units']:,} units"
            )
        else:
            updated_strategies.append(strategy)

    context = (
        f"Rejected strategies adjusted: {'; '.join(adjusted_names)}. "
        f"Risk context: {state.get('risk_justification', '')}"
    )
    try:
        planning_proposal = qwen_chat(PLANNING_NEG_PROMPT, context)
    except Exception:
        planning_proposal = (
            "Planning counter-proposal: reduce rejected strategy quantities by 30% "
            f"({'; '.join(adjusted_names)}) to bring costs inside the margin threshold "
            "while still covering the most urgent stockout window."
        )
    try:
        finance_response = qwen_chat(
            FINANCE_NEG_PROMPT, f"Counter-proposal: {planning_proposal}\n\n{context}"
        )
    except Exception:
        finance_response = (
            "Finance response: the 30% volume reduction materially lowers the additional "
            "cost. Re-running the cost model to confirm margin impact falls within the "
            "5% threshold before approval."
        )

    message = (
        f"Negotiation round {round_number + 1}:\n"
        f"**Planning**: {planning_proposal}\n"
        f"**Finance**: {finance_response}"
    )

    return {
        "proposed_strategies": updated_strategies,
        "negotiation_rounds": [
            {
                "round_number": round_number + 1,
                "planning_proposal": planning_proposal,
                "finance_response": finance_response,
                "resolved": False,
            }
        ],
        "negotiation_round_count": round_number + 1,
        "agent_messages": [
            {"agent": "negotiation", "message": message, "timestamp": _now()}
        ],
    }
