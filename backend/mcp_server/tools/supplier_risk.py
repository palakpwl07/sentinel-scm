"""assess_supplier_risk — supplier impact assessment against active disruptions."""

from database.neo4j_client import get_client

_DELAY_BY_SEVERITY = {"CRITICAL": 60, "HIGH": 30, "MEDIUM": 14}


def assess_supplier_risk(supplier_id: str, active_event_ids: list[str]) -> dict:
    """
    Assess whether a specific supplier is impacted by active disruption events.
    Checks three propagation paths: (1) supplier's primary port affected,
    (2) supplier's region affected, (3) supplier directly impacted.
    Returns structured risk assessment with delay estimate.
    """
    cypher = """
    MATCH (s:Supplier {id: $supplier_id})
    OPTIONAL MATCH (s)-[:SHIPS_VIA]->(p:Port)<-[:AFFECTS]-(d1:DisruptionEvent)
      WHERE d1.id IN $event_ids AND d1.is_active = true
    OPTIONAL MATCH (s)-[:LOCATED_IN]->(r:Region)<-[:AFFECTS]-(d2:DisruptionEvent)
      WHERE d2.id IN $event_ids AND d2.is_active = true
    OPTIONAL MATCH (s)<-[:DIRECTLY_IMPACTS]-(d3:DisruptionEvent)
      WHERE d3.id IN $event_ids AND d3.is_active = true
    OPTIONAL MATCH (route:ShippingRoute {id: s.route_id})
    RETURN s{.*} AS supplier,
       route{.*} AS route,
       [d IN collect(DISTINCT d1) WHERE d IS NOT NULL] AS port_disruptions,
       [d IN collect(DISTINCT d2) WHERE d IS NOT NULL] AS region_disruptions,
       [d IN collect(DISTINCT d3) WHERE d IS NOT NULL] AS direct_disruptions
    """
    records = get_client().run_query(
        cypher, {"supplier_id": supplier_id, "event_ids": active_event_ids}
    )
    if not records:
        return {
            "supplier_id": supplier_id,
            "supplier_name": None,
            "is_available": False,
            "risk_level": "UNKNOWN",
            "affected_routes": [],
            "disruption_reasons": [f"Supplier {supplier_id} not found in digital twin"],
            "estimated_additional_delay_days": 0,
            "confidence": 0.0,
        }

    record = records[0]
    supplier = record["supplier"]
    route = record.get("route") or {}
    port_hits = record["port_disruptions"]
    region_hits = record["region_disruptions"]
    direct_hits = record["direct_disruptions"]
    all_hits = port_hits + region_hits + direct_hits

    is_available = bool(supplier.get("is_available", True))
    severities = {d.get("severity") for d in all_hits}

    if not is_available or direct_hits:
        risk_level = "CRITICAL"
    elif "CRITICAL" in severities:
        risk_level = "CRITICAL"
    elif "HIGH" in severities or route.get("is_disrupted"):
        risk_level = "HIGH"
    elif all_hits:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    delay = 0
    if not is_available:
        delay = 999
    elif route.get("is_disrupted") and route.get("disruption_type") == "BLOCKED":
        delay = 999
    elif route.get("is_disrupted"):
        delay = int(route.get("transit_days_current", 0)) - int(
            route.get("transit_days_normal", 0)
        )
    elif all_hits:
        delay = max(_DELAY_BY_SEVERITY.get(d.get("severity"), 7) for d in all_hits)

    reasons = []
    if supplier.get("unavailability_reason"):
        reasons.append(supplier["unavailability_reason"])
    reasons.extend(
        f"{d.get('name')}: {d.get('description')}" for d in all_hits
    )

    affected_routes = []
    if route and route.get("is_disrupted"):
        affected_routes.append(
            {
                "route_id": route.get("id"),
                "route_name": route.get("name"),
                "disruption_type": route.get("disruption_type"),
                "disruption_notes": route.get("disruption_notes"),
            }
        )

    confidence = 0.95 if (direct_hits or not is_available) else (0.85 if all_hits else 0.9)

    return {
        "supplier_id": supplier_id,
        "supplier_name": supplier.get("name"),
        "is_available": is_available,
        "risk_level": risk_level,
        "affected_routes": affected_routes,
        "disruption_reasons": list(dict.fromkeys(reasons)),
        "estimated_additional_delay_days": delay,
        "confidence": confidence,
    }
