"""SupplyChainState — shared LangGraph state for the five-agent society."""

from operator import add
from typing import Annotated, Optional, TypedDict


class DetectedEvent(TypedDict):
    event_id: str
    name: str
    severity: str
    affected_regions: list[str]
    affected_ports: list[str]
    source: str


class AffectedSupplier(TypedDict):
    supplier_id: str
    material_id: str
    supplier_name: str
    risk_level: str                    # "CRITICAL", "HIGH", "MEDIUM"
    is_available: bool
    estimated_additional_delay_days: int
    inventory_runway_days: int


class MitigationStrategy(TypedDict):
    strategy_id: str
    strategy_type: str
    material_id: str
    target_supplier_id: Optional[str]
    description: str
    rationale: str
    quantity_units: int
    urgency_days: int


class StrategyEvaluation(TypedDict):
    strategy_id: str
    additional_cost_sgd: float
    revenue_protected_sgd: float
    net_benefit_sgd: float
    margin_impact_pct: float
    finance_recommendation: str        # "APPROVE" | "CONDITIONAL" | "REJECT"
    finance_notes: str


class NegotiationRound(TypedDict):
    round_number: int
    planning_proposal: str
    finance_response: str
    resolved: bool


class Evidence(TypedDict):
    source: str
    fact: str
    impact: str


class FinalRecommendation(TypedDict):
    decision: str
    primary_actions: list[str]
    evidence: list[Evidence]
    confidence_score: float
    additional_cost_sgd: float
    revenue_protected_sgd: float
    net_benefit_sgd: float
    requires_human_approval: bool


class AgentMessage(TypedDict):
    agent: str                         # "monitoring" | "risk" | "planning" | "finance" | "negotiation" | "ops_manager"
    message: str
    timestamp: str


class SupplyChainState(TypedDict):
    # Input
    scenario_id: str
    event_description: str
    event_date: str

    # Monitoring Agent output
    detected_events: list[DetectedEvent]
    affected_regions: list[str]
    affected_ports: list[str]

    # Risk Agent output
    affected_suppliers: list[AffectedSupplier]
    inventory_runways: dict            # {material_id: {days_remaining, stockout_date, ...}}
    overall_risk_score: float          # 0.0–1.0
    risk_justification: str

    # Planning Agent output
    proposed_strategies: list[MitigationStrategy]

    # Finance Agent output
    strategy_evaluations: list[StrategyEvaluation]

    # Negotiation
    negotiation_rounds: Annotated[list[NegotiationRound], add]
    negotiation_resolved: bool
    negotiation_round_count: int

    # Ops Manager output
    final_recommendation: Optional[FinalRecommendation]

    # HITL
    awaiting_human_approval: bool
    human_decision: Optional[str]      # "approve" | "reject"
    human_notes: Optional[str]

    # Streaming
    agent_messages: Annotated[list[AgentMessage], add]
