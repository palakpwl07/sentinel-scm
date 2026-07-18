"""find_alternative_suppliers — ranked list of viable backup suppliers."""

from database.neo4j_client import get_client


def find_alternative_suppliers(
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
    cypher = """
    MATCH (s:Supplier)-[rel:SUPPLIES]->(m:Material {id: $material_id})
    WHERE NOT s.id IN $excluded_ids
      AND s.is_available = true
      AND rel.lead_time_days <= $max_lead_time
      AND NOT EXISTS {
        MATCH (s)-[:SHIPS_VIA]->(p:Port {is_disrupted: true})
        WHERE p.disruption_severity IN ['CRITICAL', 'HIGH']
      }
      AND NOT EXISTS {
        MATCH (s)-[:LOCATED_IN]->(r:Region)<-[:AFFECTS]-(d:DisruptionEvent {is_active: true})
        WHERE d.severity = 'CRITICAL'
      }
    OPTIONAL MATCH (route:ShippingRoute {id: s.route_id})
    RETURN s{.*} AS supplier, rel{.*} AS rel, route{.*} AS route
    ORDER BY rel.cost_per_unit_sgd ASC
    """
    records = get_client().run_query(
        cypher,
        {
            "material_id": material_id,
            "excluded_ids": excluded_supplier_ids,
            "max_lead_time": max_lead_time_days,
        },
    )

    primary = get_client().run_query(
        """
        MATCH (s:Supplier)-[rel:SUPPLIES {is_primary: true}]->(m:Material {id: $material_id})
        RETURN rel.cost_per_unit_sgd AS primary_cost
        """,
        {"material_id": material_id},
    )
    primary_cost = primary[0]["primary_cost"] if primary else None

    alternatives = []
    for record in records:
        supplier = record["supplier"]
        rel = record["rel"]
        route = record.get("route") or {}
        cost = rel.get("cost_per_unit_sgd", supplier.get("cost_per_unit_sgd"))

        if route.get("disruption_type") == "BLOCKED":
            route_status = "blocked"
        elif route.get("disruption_type") == "REROUTED":
            route_status = "rerouted"
        else:
            route_status = "active"

        cost_delta_pct = (
            round((cost - primary_cost) / primary_cost * 100.0, 1)
            if primary_cost
            else None
        )

        alternatives.append(
            {
                "supplier_id": supplier.get("id"),
                "name": supplier.get("name"),
                "country": supplier.get("country"),
                "cost_per_unit_sgd": cost,
                "lead_time_days": rel.get("lead_time_days"),
                "quality_tier": rel.get("quality_tier"),
                "capacity_units_per_month": supplier.get("capacity_units_per_month"),
                "reliability_score": supplier.get("reliability_score"),
                "cost_delta_vs_primary_pct": cost_delta_pct,
                "route_status": route_status,
            }
        )
    return alternatives