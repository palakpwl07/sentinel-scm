"""calculate_inventory_runway — days-to-stockout per material."""

from datetime import date, timedelta

import config
from database.neo4j_client import get_client


def calculate_inventory_runway(material_ids: list[str]) -> dict:
    """
    Calculate days until stockout for each specified material.
    Uses current_inventory_days and monthly_demand_units from Material nodes.
    Returns stockout date and units needed to bridge to next safe shipment.
    """
    cypher = """
    MATCH (m:Material) WHERE m.id IN $material_ids
    RETURN m.id AS material_id, m.name AS material_name,
           m.current_inventory_days AS days_remaining,
           m.monthly_demand_units AS monthly_demand,
           m.criticality AS criticality,
           m.reorder_point_days AS reorder_point_days,
           m.unit_revenue_contribution_sgd AS revenue_per_unit
    """
    records = get_client().run_query(cypher, {"material_ids": material_ids})
    today = date.fromisoformat(config.SIMULATION_DATE)

    runways = {}
    for record in records:
        days_remaining = int(record["days_remaining"])
        monthly_demand = int(record["monthly_demand"])
        daily_demand = monthly_demand / 30.0
        stockout_date = today + timedelta(days=days_remaining)

        bridge_days = max(0, 30 - days_remaining)
        units_needed = int(round(daily_demand * bridge_days))
        at_risk_revenue = round(units_needed * float(record["revenue_per_unit"]), 2)

        runways[record["material_id"]] = {
            "material_name": record["material_name"],
            "days_remaining": days_remaining,
            "stockout_date": stockout_date.isoformat(),
            "monthly_demand": monthly_demand,
            "criticality": record["criticality"],
            "reorder_point_days": int(record["reorder_point_days"]),
            "units_needed_30_day_bridge": units_needed,
            "at_risk_revenue_sgd": at_risk_revenue,
            "is_critical": days_remaining < int(record["reorder_point_days"]),
        }
    return runways
