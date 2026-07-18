"""LangGraph graph wiring the five-agent supply chain society."""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from .finance import finance_agent
from .monitoring import monitoring_agent
from .negotiation import negotiation_round
from .ops_manager import ops_manager_agent
from .planning import planning_agent
from .risk import risk_agent
from .state import SupplyChainState


def should_escalate(state: SupplyChainState) -> str:
    """Route based on risk score after monitoring."""
    if state["overall_risk_score"] < 0.2:
        return "low_risk"
    return "escalate"


def negotiation_check(state: SupplyChainState) -> str:
    """Check if Planning and Finance agents disagree."""
    rejected = [
        e for e in state["strategy_evaluations"]
        if e["finance_recommendation"] == "REJECT"
    ]
    if rejected and state["negotiation_round_count"] < 2:
        return "negotiate"
    return "arbitrate"


builder = StateGraph(SupplyChainState)

builder.add_node("monitoring", monitoring_agent)
builder.add_node("risk", risk_agent)
builder.add_node("planning", planning_agent)
builder.add_node("finance", finance_agent)
builder.add_node("negotiation", negotiation_round)
builder.add_node("ops_manager", ops_manager_agent)

builder.set_entry_point("monitoring")
builder.add_edge("monitoring", "risk")
builder.add_conditional_edges("risk", should_escalate, {"escalate": "planning", "low_risk": END})
builder.add_edge("planning", "finance")
builder.add_conditional_edges("finance", negotiation_check, {"negotiate": "negotiation", "arbitrate": "ops_manager"})
builder.add_edge("negotiation", "finance")  # loop back for re-evaluation
builder.add_edge("ops_manager", END)

# HITL interrupt before ops_manager publishes final recommendation
checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer, interrupt_before=["ops_manager"])
