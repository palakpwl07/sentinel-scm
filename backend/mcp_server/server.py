"""MCP server exposing the Neo4j digital twin as tools.

Run standalone:  python -m mcp_server.server
The four tools are also imported directly by the LangGraph agent nodes so the
graph works in-process without a network hop.
"""

from mcp.server.fastmcp import FastMCP

import config
from mcp_server.tools.alternative_suppliers import find_alternative_suppliers
from mcp_server.tools.inventory_runway import calculate_inventory_runway
from mcp_server.tools.mitigation_cost import evaluate_mitigation_cost
from mcp_server.tools.supplier_risk import assess_supplier_risk

mcp = FastMCP(
    "supply-chain-digital-twin",
    host=config.MCP_SERVER_HOST,
    port=config.MCP_SERVER_PORT,
)


@mcp.tool()
def assess_supplier_risk_tool(supplier_id: str, active_event_ids: list[str]) -> dict:
    """
    Assess whether a specific supplier is impacted by active disruption events.
    Checks three propagation paths: (1) supplier's primary port affected,
    (2) supplier's region affected, (3) supplier directly impacted.
    Returns structured risk assessment with delay estimate.
    """
    return assess_supplier_risk(supplier_id, active_event_ids)


@mcp.tool()
def find_alternative_suppliers_tool(
    material_id: str,
    excluded_supplier_ids: list[str],
    max_lead_time_days: int = 30,
) -> list[dict]:
    """
    Find available, unaffected suppliers for a given material,
    excluding specified suppliers (e.g., already-disrupted ones).
    Filters out suppliers whose primary port or region has an active disruption.
    Returns ranked by cost_per_unit ascending.
    """
    return find_alternative_suppliers(material_id, excluded_supplier_ids, max_lead_time_days)


@mcp.tool()
def calculate_inventory_runway_tool(material_ids: list[str]) -> dict:
    """
    Calculate days until stockout for each specified material.
    Uses current_inventory_days and monthly_demand_units from Material nodes.
    Returns stockout date and units needed to bridge to next safe shipment.
    """
    return calculate_inventory_runway(material_ids)


@mcp.tool()
def evaluate_mitigation_cost_tool(
    strategy_type: str,
    material_id: str,
    target_supplier_id: str,
    quantity_units: int,
    urgency_days: int,
) -> dict:
    """
    Calculate financial impact of a mitigation strategy
    (air_freight | switch_supplier | safety_stock | delay_production | reallocate_inventory).
    Retrieves material and supplier data from Neo4j, applies the business cost model,
    and returns a cost breakdown with net benefit vs. production stoppage.
    """
    return evaluate_mitigation_cost(
        strategy_type, material_id, target_supplier_id, quantity_units, urgency_days
    )


if __name__ == "__main__":
    mcp.run(transport="sse")
