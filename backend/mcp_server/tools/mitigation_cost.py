"""evaluate_mitigation_cost — financial impact model for mitigation strategies."""

import config
from database.neo4j_client import get_client

VALID_STRATEGIES = {
    "air_freight",
    "switch_supplier",
    "safety_stock",
    "delay_production",
    "reallocate_inventory",
}


def _fetch_context(material_id: str, target_supplier_id: str | None) -> dict:
    cypher = """
    MATCH (m:Material {id: $material_id})
    OPTIONAL MATCH (primary:Supplier)-[prel:SUPPLIES {is_primary: true}]->(m)
    OPTIONAL MATCH (target:Supplier {id: $target_id})
    OPTIONAL MATCH (route:ShippingRoute {id: target.route_id})
    RETURN m{.*} AS material, primary{.*} AS primary, prel{.*} AS prel,
           target{.*} AS target, route{.*} AS route
    """
    records = get_client().run_query(
        cypher,
        {"material_id": material_id, "target_id": target_supplier_id or ""},
    )
    if not records:
        raise ValueError(f"Material {material_id} not found")
    record = records[0]
    return {
        "material": record["material"],
        "primary_rel": record.get("prel") or {},
        "target": record.get("target") or {},
        "route": record.get("route") or {},
    }


def evaluate_mitigation_cost(
    strategy_type: str,
    material_id: str,
    target_supplier_id: str,
    quantity_units: int,
    urgency_days: int,
) -> dict:
    """
    Calculate financial impact of a mitigation strategy.
    Retrieves material and supplier data from Neo4j.
    Applies business logic cost model.
    Returns cost breakdown and net benefit vs. production stoppage.

    Strategy types: air_freight | switch_supplier | safety_stock |
    delay_production | reallocate_inventory
    """
    if strategy_type not in VALID_STRATEGIES:
        raise ValueError(f"Unknown strategy_type: {strategy_type}")

    ctx = _fetch_context(material_id, target_supplier_id)
    material = ctx["material"]
    target = ctx["target"]
    route = ctx["route"]

    monthly_demand = int(material.get("monthly_demand_units", 0))
    revenue_per_unit = float(material.get("unit_revenue_contribution_sgd", 0.0))
    daily_revenue_at_risk = monthly_demand / 30.0 * revenue_per_unit
    unit_cost = float(target.get("cost_per_unit_sgd", 0.0) or 0.0)
    primary_cost = float(ctx["primary_rel"].get("cost_per_unit_sgd", unit_cost) or unit_cost)

    revenue_protected = round(quantity_units * revenue_per_unit, 2)

    if strategy_type == "air_freight":
        sea_freight_per_unit = float(
            route.get("freight_cost_sgd_per_unit_normal", 2.0) or 2.0
        )
        additional_cost = sea_freight_per_unit * config.AIR_FREIGHT_MULTIPLIER * quantity_units
        # premium sourcing cost delta also applies when flying from a non-primary supplier
        additional_cost += max(0.0, unit_cost - primary_cost) * quantity_units

    elif strategy_type == "switch_supplier":
        additional_cost = (unit_cost - primary_cost) * monthly_demand * 1

    elif strategy_type == "safety_stock":
        additional_cost = (
            quantity_units
            * unit_cost
            * config.CARRYING_COST_PCT_ANNUAL
            / 365.0
            * max(urgency_days, 30)
        )
        additional_cost += max(0.0, unit_cost - primary_cost) * quantity_units

    elif strategy_type == "delay_production":
        additional_cost = daily_revenue_at_risk * urgency_days
        revenue_protected = 0.0

    else:  # reallocate_inventory
        additional_cost = config.REALLOCATION_FIXED_COST_SGD

    additional_cost = round(max(additional_cost, 0.0), 2)
    net_benefit = round(revenue_protected - additional_cost, 2)
    margin_impact_pct = round(additional_cost / config.MONTHLY_REVENUE_SGD * 100.0, 2)

    if revenue_protected > 0 and urgency_days > 0:
        payback_days = round(additional_cost / (revenue_protected / urgency_days), 1)
    else:
        payback_days = None

    if margin_impact_pct <= config.MARGIN_IMPACT_THRESHOLD_PCT and net_benefit > 0:
        recommendation = "APPROVE"
        reason = (
            f"Margin impact {margin_impact_pct}% within {config.MARGIN_IMPACT_THRESHOLD_PCT}% "
            f"threshold and net benefit SGD {net_benefit:,.0f} is positive."
        )
    elif margin_impact_pct > config.MARGIN_IMPACT_THRESHOLD_PCT and net_benefit > 0:
        recommendation = "CONDITIONAL"
        reason = (
            f"Net benefit SGD {net_benefit:,.0f} is positive but margin impact "
            f"{margin_impact_pct}% exceeds the {config.MARGIN_IMPACT_THRESHOLD_PCT}% threshold."
        )
    else:
        recommendation = "REJECT"
        reason = (
            f"Net benefit SGD {net_benefit:,.0f} is negative"
            + (
                f" and margin impact {margin_impact_pct}% exceeds threshold."
                if margin_impact_pct > config.MARGIN_IMPACT_THRESHOLD_PCT
                else "."
            )
        )

    return {
        "strategy_type": strategy_type,
        "material_id": material_id,
        "target_supplier_id": target_supplier_id,
        "quantity_units": quantity_units,
        "urgency_days": urgency_days,
        "additional_cost_sgd": additional_cost,
        "revenue_protected_sgd": revenue_protected,
        "net_benefit_sgd": net_benefit,
        "margin_impact_pct": margin_impact_pct,
        "payback_days": payback_days,
        "recommendation": recommendation,
        "recommendation_reason": reason,
    }
