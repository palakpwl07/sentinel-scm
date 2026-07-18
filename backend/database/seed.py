"""Seed the Neo4j digital twin for Orbital Manufacturing.

Idempotent: every statement uses MERGE, so the script is safe to re-run.
Run from backend/:  python -m database.seed
"""

# NOTE: the Neo4j driver is imported lazily inside main() so that eval/
# modules can import the seed data constants below as plain Python without
# pulling in the database layer.

# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------

CONSTRAINTS = [
    "CREATE CONSTRAINT supplier_id IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT material_id IF NOT EXISTS FOR (m:Material) REQUIRE m.id IS UNIQUE",
    "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:ShippingRoute) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT factory_id IF NOT EXISTS FOR (f:Factory) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT warehouse_id IF NOT EXISTS FOR (w:Warehouse) REQUIRE w.id IS UNIQUE",
    "CREATE CONSTRAINT region_id IF NOT EXISTS FOR (r:Region) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:DisruptionEvent) REQUIRE e.id IS UNIQUE",
]

# ---------------------------------------------------------------------------
# Seed data (Section 6 of the build spec)
# ---------------------------------------------------------------------------

COMPANY = {
    "id": "ORB-SG-001",
    "name": "Orbital Manufacturing Pte Ltd",
    "hq_country": "Singapore",
    "hq_city": "Singapore",
    "annual_revenue_sgd": 285000000.0,
    "employees": 1240,
}

REGIONS = [
    {"id": "REG-SGP", "name": "Singapore", "risk_level": "LOW", "risk_reason": "Stable"},
    {"id": "REG-MYS", "name": "Malaysia", "risk_level": "LOW", "risk_reason": "Stable"},
    {"id": "REG-CHN", "name": "China", "risk_level": "MEDIUM", "risk_reason": "Geopolitical tension, tariff risk"},
    {"id": "REG-TWN", "name": "Taiwan", "risk_level": "MEDIUM", "risk_reason": "Cross-strait tension"},
    {"id": "REG-JPN", "name": "Japan", "risk_level": "LOW", "risk_reason": "Stable"},
    {"id": "REG-DEU", "name": "Germany", "risk_level": "MEDIUM", "risk_reason": "Cape reroute adds 14 days to Singapore shipments"},
    {"id": "REG-BEL", "name": "Belgium", "risk_level": "MEDIUM", "risk_reason": "Cape reroute adds 14 days to Singapore shipments"},
    {"id": "REG-ISR", "name": "Israel", "risk_level": "CRITICAL", "risk_reason": "Active conflict zone — US/Israel-Iran war, Feb 28 2026"},
    {"id": "REG-QAT", "name": "Qatar", "risk_level": "CRITICAL", "risk_reason": "Strait of Hormuz closed, QatarEnergy force majeure March 4 2026"},
    {"id": "REG-UAE", "name": "UAE", "risk_level": "HIGH", "risk_reason": "Jebel Ali port severely disrupted, Hormuz closure"},
    {"id": "REG-USA", "name": "USA", "risk_level": "LOW", "risk_reason": "Stable, Pacific routes unaffected"},
    {"id": "REG-AUS", "name": "Australia", "risk_level": "LOW", "risk_reason": "Stable, direct Indian Ocean route"},
    {"id": "REG-THA", "name": "Thailand", "risk_level": "LOW", "risk_reason": "Stable regional supplier"},
    {"id": "REG-RUS", "name": "Russia via UAE", "risk_level": "CRITICAL", "risk_reason": "UAE transit hub disrupted"},
]

PORTS = [
    {"id": "PORT-SGP", "name": "Port of Singapore (PSA)", "country": "Singapore", "city": "Singapore", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-KUL", "name": "Port Klang", "country": "Malaysia", "city": "Klang", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-JEA", "name": "Jebel Ali Port", "country": "UAE", "city": "Dubai", "is_disrupted": True, "disruption_reason": "Strait of Hormuz closure and Iranian strikes on Dubai hub infrastructure", "disruption_severity": "HIGH"},
    {"id": "PORT-RAS", "name": "Ras Laffan Industrial Port", "country": "Qatar", "city": "Ras Laffan", "is_disrupted": True, "disruption_reason": "Strait of Hormuz effectively closed, QatarEnergy force majeure", "disruption_severity": "CRITICAL"},
    {"id": "PORT-HAI", "name": "Port of Haifa", "country": "Israel", "city": "Haifa", "is_disrupted": True, "disruption_reason": "Active conflict zone — US/Israel-Iran war", "disruption_severity": "CRITICAL"},
    {"id": "PORT-HAM", "name": "Port of Hamburg", "country": "Germany", "city": "Hamburg", "is_disrupted": False, "disruption_reason": "Operational but ships rerouting via Cape (+14 days to Singapore)", "disruption_severity": None},
    {"id": "PORT-ANT", "name": "Port of Antwerp", "country": "Belgium", "city": "Antwerp", "is_disrupted": False, "disruption_reason": "Operational but ships rerouting via Cape (+14 days to Singapore)", "disruption_severity": None},
    {"id": "PORT-YOK", "name": "Port of Yokohama", "country": "Japan", "city": "Yokohama", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-KAO", "name": "Port of Kaohsiung", "country": "Taiwan", "city": "Kaohsiung", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-HOU", "name": "Port of Houston", "country": "USA", "city": "Houston", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-DAR", "name": "Port of Darwin", "country": "Australia", "city": "Darwin", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-COL", "name": "Port of Colombo", "country": "Sri Lanka", "city": "Colombo", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-SHA", "name": "Port of Shanghai", "country": "China", "city": "Shanghai", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-HKG", "name": "Hong Kong Container Port", "country": "China", "city": "Hong Kong", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-LCB", "name": "Laem Chabang Port", "country": "Thailand", "city": "Chonburi", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
    {"id": "PORT-OSA", "name": "Port of Osaka", "country": "Japan", "city": "Osaka", "is_disrupted": False, "disruption_reason": None, "disruption_severity": None},
]

ROUTES = [
    {"id": "RT-GULF-SGP", "name": "Persian Gulf → Singapore", "origin_port_id": "PORT-RAS", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 9, "transit_days_current": 999, "freight_cost_sgd_per_unit_normal": 1.20, "freight_cost_sgd_per_unit_current": 999.0, "passes_through_hormuz": True, "passes_through_red_sea": False, "is_disrupted": True, "disruption_type": "BLOCKED", "disruption_notes": "Strait of Hormuz closed March 2 2026"},
    {"id": "RT-ISR-SGP", "name": "Israel → Singapore", "origin_port_id": "PORT-HAI", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 18, "transit_days_current": 999, "freight_cost_sgd_per_unit_normal": 2.10, "freight_cost_sgd_per_unit_current": 999.0, "passes_through_hormuz": False, "passes_through_red_sea": True, "is_disrupted": True, "disruption_type": "BLOCKED", "disruption_notes": "Port of Haifa in conflict zone, Red Sea blocked"},
    {"id": "RT-HAM-SGP-CAPE", "name": "Hamburg → Singapore (Cape Reroute)", "origin_port_id": "PORT-HAM", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 14, "transit_days_current": 28, "freight_cost_sgd_per_unit_normal": 2.80, "freight_cost_sgd_per_unit_current": 3.64, "passes_through_hormuz": False, "passes_through_red_sea": True, "is_disrupted": True, "disruption_type": "REROUTED", "disruption_notes": "Red Sea blocked, rerouting via Cape of Good Hope adds 14 days and 30% freight cost"},
    {"id": "RT-ANT-SGP-CAPE", "name": "Antwerp → Singapore (Cape Reroute)", "origin_port_id": "PORT-ANT", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 14, "transit_days_current": 28, "freight_cost_sgd_per_unit_normal": 2.90, "freight_cost_sgd_per_unit_current": 3.77, "passes_through_hormuz": False, "passes_through_red_sea": True, "is_disrupted": True, "disruption_type": "REROUTED", "disruption_notes": "Red Sea blocked, Cape of Good Hope reroute"},
    {"id": "RT-YOK-SGP", "name": "Yokohama → Singapore", "origin_port_id": "PORT-YOK", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 7, "transit_days_current": 7, "freight_cost_sgd_per_unit_normal": 1.50, "freight_cost_sgd_per_unit_current": 1.50, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-KAO-SGP", "name": "Kaohsiung → Singapore", "origin_port_id": "PORT-KAO", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 4, "transit_days_current": 4, "freight_cost_sgd_per_unit_normal": 1.20, "freight_cost_sgd_per_unit_current": 1.20, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-SHA-SGP", "name": "Shanghai → Singapore", "origin_port_id": "PORT-SHA", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 5, "transit_days_current": 5, "freight_cost_sgd_per_unit_normal": 1.10, "freight_cost_sgd_per_unit_current": 1.10, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-HKG-SGP", "name": "Hong Kong → Singapore", "origin_port_id": "PORT-HKG", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 4, "transit_days_current": 4, "freight_cost_sgd_per_unit_normal": 1.15, "freight_cost_sgd_per_unit_current": 1.15, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-HOU-SGP", "name": "Houston → Singapore (Pacific)", "origin_port_id": "PORT-HOU", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 22, "transit_days_current": 22, "freight_cost_sgd_per_unit_normal": 3.40, "freight_cost_sgd_per_unit_current": 3.40, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-DAR-SGP", "name": "Darwin → Singapore", "origin_port_id": "PORT-DAR", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 8, "transit_days_current": 8, "freight_cost_sgd_per_unit_normal": 1.80, "freight_cost_sgd_per_unit_current": 1.80, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-KUL-SGP", "name": "Port Klang → Singapore", "origin_port_id": "PORT-KUL", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 2, "transit_days_current": 2, "freight_cost_sgd_per_unit_normal": 0.60, "freight_cost_sgd_per_unit_current": 0.60, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-LCB-SGP", "name": "Laem Chabang → Singapore", "origin_port_id": "PORT-LCB", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 4, "transit_days_current": 4, "freight_cost_sgd_per_unit_normal": 0.90, "freight_cost_sgd_per_unit_current": 0.90, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
    {"id": "RT-OSA-SGP", "name": "Osaka → Singapore", "origin_port_id": "PORT-OSA", "destination_port_id": "PORT-SGP", "mode": "sea", "transit_days_normal": 7, "transit_days_current": 7, "freight_cost_sgd_per_unit_normal": 1.55, "freight_cost_sgd_per_unit_current": 1.55, "passes_through_hormuz": False, "passes_through_red_sea": False, "is_disrupted": False, "disruption_type": None, "disruption_notes": None},
]

DISRUPTION_EVENTS = [
    {
        "id": "DISRUPT-001",
        "name": "US-Israel Operation Epic Fury",
        "type": "GEOPOLITICAL",
        "severity": "CRITICAL",
        "affected_region": "Israel, Middle East",
        "start_date": "2026-02-28",
        "source": "Reuters",
        "source_url": "https://reuters.com",
        "description": "US and Israel launched Operation Epic Fury, air and maritime strikes on Iran. Israel in active conflict zone. All Israeli ports and suppliers unavailable.",
        "is_active": True,
    },
    {
        "id": "DISRUPT-002",
        "name": "Houthi Red Sea Attacks Resumed",
        "type": "SHIPPING",
        "severity": "HIGH",
        "affected_region": "Red Sea, Bab el-Mandeb, Suez Canal",
        "start_date": "2026-02-28",
        "source": "WorldCargo News",
        "source_url": "https://worldcargonews.com",
        "description": "Houthi forces resumed attacks on commercial vessels in Red Sea on Feb 28. Maersk, MSC, Hapag-Lloyd, CMA CGM all suspended Suez Canal transits. Ships rerouting via Cape of Good Hope (+14 days, +30% freight cost).",
        "is_active": True,
    },
    {
        "id": "DISRUPT-003",
        "name": "Strait of Hormuz IRGC Closure",
        "type": "SHIPPING",
        "severity": "CRITICAL",
        "affected_region": "Persian Gulf, Strait of Hormuz, Gulf of Oman",
        "start_date": "2026-03-02",
        "source": "IRGC / Reuters",
        "source_url": "https://reuters.com",
        "description": "IRGC confirmed Strait of Hormuz closed March 2. Commercial traffic dropped 90%+. All major carriers suspended Gulf transits. First time in modern history both Hormuz and Red Sea simultaneously blocked.",
        "is_active": True,
    },
    {
        "id": "DISRUPT-004",
        "name": "QatarEnergy Force Majeure",
        "type": "SUPPLIER",
        "severity": "HIGH",
        "affected_region": "Qatar",
        "start_date": "2026-03-04",
        "source": "Carra Globe / QatarEnergy",
        "source_url": "https://carraglobe.com/strait-of-hormuz-closure-2026",
        "description": "QatarEnergy invoked force majeure on all LNG and helium shipments March 4. Ras Laffan port inaccessible due to Hormuz closure. All QatarEnergy supply contracts suspended indefinitely.",
        "is_active": True,
    },
    {
        "id": "DISRUPT-005",
        "name": "Jebel Ali Port Severe Disruption",
        "type": "PORT",
        "severity": "HIGH",
        "affected_region": "UAE, Dubai",
        "start_date": "2026-03-01",
        "source": "IMO",
        "source_url": "https://www.imo.org",
        "description": "Jebel Ali port in Dubai severely disrupted by Hormuz closure and regional instability. VSMPO-AVISMA titanium transshipment through Dubai hub effectively halted. War risk insurance surcharges applied to all UAE-routing cargo.",
        "is_active": True,
    },
]

MATERIALS = [
    {"id": "MAT-IC", "name": "Semiconductor ICs", "category": "Electronics", "unit": "units", "monthly_demand_units": 15000, "criticality": "HIGH", "current_inventory_days": 18, "reorder_point_days": 14, "unit_revenue_contribution_sgd": 320.0},
    {"id": "MAT-HE", "name": "Industrial Helium", "category": "Industrial Gas", "unit": "cylinders", "monthly_demand_units": 8000, "criticality": "HIGH", "current_inventory_days": 12, "reorder_point_days": 10, "unit_revenue_contribution_sgd": 85.0},
    {"id": "MAT-SC", "name": "Specialty Chemicals & Etchants", "category": "Chemicals", "unit": "liters", "monthly_demand_units": 22000, "criticality": "MEDIUM", "current_inventory_days": 21, "reorder_point_days": 14, "unit_revenue_contribution_sgd": 28.0},
    {"id": "MAT-PM", "name": "Precision Titanium Alloy", "category": "Metals", "unit": "kg", "monthly_demand_units": 5000, "criticality": "MEDIUM", "current_inventory_days": 25, "reorder_point_days": 14, "unit_revenue_contribution_sgd": 410.0},
    {"id": "MAT-PB", "name": "PCB Substrates", "category": "Electronics", "unit": "units", "monthly_demand_units": 18000, "criticality": "HIGH", "current_inventory_days": 14, "reorder_point_days": 12, "unit_revenue_contribution_sgd": 95.0},
    {"id": "MAT-OC", "name": "Precision Optical Components", "category": "Optics", "unit": "units", "monthly_demand_units": 3500, "criticality": "CRITICAL", "current_inventory_days": 9, "reorder_point_days": 14, "unit_revenue_contribution_sgd": 1850.0},
]

SUPPLIERS = [
    # --- SEMICONDUCTOR ICs ---
    {"id": "SG-IC-01", "name": "TSMC-Nano (Taiwan)", "country": "Taiwan", "city": "Hsinchu", "quality_tier": "A+", "reliability_score": 0.97, "capacity_units_per_month": 20000, "lead_time_days": 21, "cost_per_unit_sgd": 45.00, "contract_type": "long_term", "annual_volume_sgd": 8100000.0, "certifications": ["ISO9001", "IATF16949"], "is_available": True, "unavailability_reason": None, "region_id": "REG-TWN", "primary_port_id": "PORT-KAO", "route_id": "RT-KAO-SGP", "material_id": "MAT-IC", "is_primary": True},
    {"id": "SG-IC-02", "name": "GlobalFab Shenzhen (China)", "country": "China", "city": "Shenzhen", "quality_tier": "A", "reliability_score": 0.91, "capacity_units_per_month": 25000, "lead_time_days": 14, "cost_per_unit_sgd": 28.50, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-CHN", "primary_port_id": "PORT-SHA", "route_id": "RT-SHA-SGP", "material_id": "MAT-IC", "is_primary": False},
    {"id": "SG-IC-03", "name": "Kyushu Micro (Japan)", "country": "Japan", "city": "Fukuoka", "quality_tier": "A+", "reliability_score": 0.98, "capacity_units_per_month": 12000, "lead_time_days": 18, "cost_per_unit_sgd": 52.00, "contract_type": "long_term", "annual_volume_sgd": 9400000.0, "certifications": ["ISO9001", "AS9100"], "is_available": True, "unavailability_reason": None, "region_id": "REG-JPN", "primary_port_id": "PORT-YOK", "route_id": "RT-YOK-SGP", "material_id": "MAT-IC", "is_primary": False},
    {"id": "SG-IC-04", "name": "PenangChip (Malaysia)", "country": "Malaysia", "city": "Penang", "quality_tier": "A-", "reliability_score": 0.89, "capacity_units_per_month": 18000, "lead_time_days": 5, "cost_per_unit_sgd": 32.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-MYS", "primary_port_id": "PORT-KUL", "route_id": "RT-KUL-SGP", "material_id": "MAT-IC", "is_primary": False},
    # --- HELIUM ---
    {"id": "SG-HE-01", "name": "QatarEnergy LNG (Qatar)", "country": "Qatar", "city": "Ras Laffan", "quality_tier": "A", "reliability_score": 0.0, "capacity_units_per_month": 12000, "lead_time_days": 9, "cost_per_unit_sgd": 18.50, "contract_type": "long_term", "annual_volume_sgd": 2200000.0, "certifications": ["ISO9001"], "is_available": False, "unavailability_reason": "FORCE MAJEURE declared March 4 2026. Strait of Hormuz closed. All QatarEnergy shipments suspended indefinitely.", "region_id": "REG-QAT", "primary_port_id": "PORT-RAS", "route_id": "RT-GULF-SGP", "material_id": "MAT-HE", "is_primary": True},
    {"id": "SG-HE-02", "name": "Air Products USA (Texas)", "country": "USA", "city": "Freeport, TX", "quality_tier": "A", "reliability_score": 0.99, "capacity_units_per_month": 10000, "lead_time_days": 22, "cost_per_unit_sgd": 45.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-USA", "primary_port_id": "PORT-HOU", "route_id": "RT-HOU-SGP", "material_id": "MAT-HE", "is_primary": False},
    {"id": "SG-HE-03", "name": "Icelink Gas (Australia)", "country": "Australia", "city": "Darwin", "quality_tier": "A", "reliability_score": 0.97, "capacity_units_per_month": 6000, "lead_time_days": 8, "cost_per_unit_sgd": 32.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-AUS", "primary_port_id": "PORT-DAR", "route_id": "RT-DAR-SGP", "material_id": "MAT-HE", "is_primary": False},
    {"id": "SG-HE-04", "name": "Messer Group (Germany)", "country": "Germany", "city": "Hamburg", "quality_tier": "A+", "reliability_score": 0.96, "capacity_units_per_month": 8000, "lead_time_days": 28, "cost_per_unit_sgd": 49.40, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-DEU", "primary_port_id": "PORT-HAM", "route_id": "RT-HAM-SGP-CAPE", "material_id": "MAT-HE", "is_primary": False},
    # --- SPECIALTY CHEMICALS ---
    {"id": "SG-SC-01", "name": "BASF SE (Germany)", "country": "Germany", "city": "Hamburg", "quality_tier": "A+", "reliability_score": 0.98, "capacity_units_per_month": 30000, "lead_time_days": 28, "cost_per_unit_sgd": 10.67, "contract_type": "long_term", "annual_volume_sgd": 2200000.0, "certifications": ["ISO9001", "ISO14001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-DEU", "primary_port_id": "PORT-HAM", "route_id": "RT-HAM-SGP-CAPE", "material_id": "MAT-SC", "is_primary": True},
    {"id": "SG-SC-02", "name": "Sinopec Chemical (China)", "country": "China", "city": "Shanghai", "quality_tier": "A-", "reliability_score": 0.90, "capacity_units_per_month": 40000, "lead_time_days": 10, "cost_per_unit_sgd": 5.80, "contract_type": "long_term", "annual_volume_sgd": 1500000.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-CHN", "primary_port_id": "PORT-SHA", "route_id": "RT-SHA-SGP", "material_id": "MAT-SC", "is_primary": False},
    {"id": "SG-SC-03", "name": "Solvay (Belgium)", "country": "Belgium", "city": "Antwerp", "quality_tier": "A+", "reliability_score": 0.97, "capacity_units_per_month": 25000, "lead_time_days": 28, "cost_per_unit_sgd": 11.83, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001", "ISO14001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-BEL", "primary_port_id": "PORT-ANT", "route_id": "RT-ANT-SGP-CAPE", "material_id": "MAT-SC", "is_primary": False},
    {"id": "SG-SC-04", "name": "PI Chemicals (Malaysia)", "country": "Malaysia", "city": "Shah Alam", "quality_tier": "A-", "reliability_score": 0.88, "capacity_units_per_month": 15000, "lead_time_days": 3, "cost_per_unit_sgd": 7.50, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-MYS", "primary_port_id": "PORT-KUL", "route_id": "RT-KUL-SGP", "material_id": "MAT-SC", "is_primary": False},
    # --- PRECISION METALS ---
    {"id": "SG-PM-01", "name": "VSMPO-AVISMA via UAE", "country": "Russia", "city": "Dubai Hub", "quality_tier": "A", "reliability_score": 0.20, "capacity_units_per_month": 8000, "lead_time_days": 35, "cost_per_unit_sgd": 125.00, "contract_type": "spot", "annual_volume_sgd": 900000.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-UAE", "primary_port_id": "PORT-JEA", "route_id": "RT-GULF-SGP", "material_id": "MAT-PM", "is_primary": True},
    {"id": "SG-PM-02", "name": "RTI International (USA)", "country": "USA", "city": "Houston, TX", "quality_tier": "A+", "reliability_score": 0.97, "capacity_units_per_month": 6000, "lead_time_days": 24, "cost_per_unit_sgd": 185.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001", "AS9100"], "is_available": True, "unavailability_reason": None, "region_id": "REG-USA", "primary_port_id": "PORT-HOU", "route_id": "RT-HOU-SGP", "material_id": "MAT-PM", "is_primary": False},
    {"id": "SG-PM-03", "name": "Toho Titanium (Japan)", "country": "Japan", "city": "Chiba", "quality_tier": "A", "reliability_score": 0.96, "capacity_units_per_month": 7000, "lead_time_days": 16, "cost_per_unit_sgd": 152.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-JPN", "primary_port_id": "PORT-YOK", "route_id": "RT-YOK-SGP", "material_id": "MAT-PM", "is_primary": False},
    {"id": "SG-PM-04", "name": "Thai Metals (Thailand)", "country": "Thailand", "city": "Rayong", "quality_tier": "A-", "reliability_score": 0.87, "capacity_units_per_month": 4000, "lead_time_days": 6, "cost_per_unit_sgd": 138.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-THA", "primary_port_id": "PORT-LCB", "route_id": "RT-LCB-SGP", "material_id": "MAT-PM", "is_primary": False},
    # --- PCB SUBSTRATES ---
    {"id": "SG-PB-01", "name": "Isola Israel (Israel)", "country": "Israel", "city": "Holon", "quality_tier": "A+", "reliability_score": 0.0, "capacity_units_per_month": 25000, "lead_time_days": 12, "cost_per_unit_sgd": 22.00, "contract_type": "long_term", "annual_volume_sgd": 4800000.0, "certifications": ["ISO9001", "IPC"], "is_available": False, "unavailability_reason": "CONFLICT ZONE — Israel in active war. Port of Haifa closed. Operations suspended indefinitely as of Feb 28 2026.", "region_id": "REG-ISR", "primary_port_id": "PORT-HAI", "route_id": "RT-ISR-SGP", "material_id": "MAT-PB", "is_primary": True},
    {"id": "SG-PB-02", "name": "Panasonic Electronic (Japan)", "country": "Japan", "city": "Osaka", "quality_tier": "A+", "reliability_score": 0.98, "capacity_units_per_month": 22000, "lead_time_days": 20, "cost_per_unit_sgd": 28.50, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-JPN", "primary_port_id": "PORT-OSA", "route_id": "RT-OSA-SGP", "material_id": "MAT-PB", "is_primary": False},
    {"id": "SG-PB-03", "name": "Kingboard Holdings (China)", "country": "China", "city": "Hong Kong", "quality_tier": "A", "reliability_score": 0.92, "capacity_units_per_month": 35000, "lead_time_days": 12, "cost_per_unit_sgd": 19.50, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-CHN", "primary_port_id": "PORT-HKG", "route_id": "RT-SHA-SGP", "material_id": "MAT-PB", "is_primary": False},
    {"id": "SG-PB-04", "name": "TTM Technologies (Malaysia)", "country": "Malaysia", "city": "Johor Bahru", "quality_tier": "A-", "reliability_score": 0.88, "capacity_units_per_month": 20000, "lead_time_days": 4, "cost_per_unit_sgd": 21.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-MYS", "primary_port_id": "PORT-KUL", "route_id": "RT-KUL-SGP", "material_id": "MAT-PB", "is_primary": False},
    # --- OPTICAL COMPONENTS ---
    {"id": "SG-OC-01", "name": "Ophir Optronics (Israel)", "country": "Israel", "city": "Jerusalem", "quality_tier": "A+", "reliability_score": 0.0, "capacity_units_per_month": 5000, "lead_time_days": 14, "cost_per_unit_sgd": 285.00, "contract_type": "long_term", "annual_volume_sgd": 12000000.0, "certifications": ["ISO9001", "MIL-SPEC"], "is_available": False, "unavailability_reason": "CONFLICT ZONE — Israel in active war. Operations fully suspended Feb 28 2026. No timeline for resumption.", "region_id": "REG-ISR", "primary_port_id": "PORT-HAI", "route_id": "RT-ISR-SGP", "material_id": "MAT-OC", "is_primary": True},
    {"id": "SG-OC-02", "name": "Jenoptik AG (Germany)", "country": "Germany", "city": "Jena", "quality_tier": "A+", "reliability_score": 0.96, "capacity_units_per_month": 4000, "lead_time_days": 28, "cost_per_unit_sgd": 416.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001", "DIN"], "is_available": True, "unavailability_reason": None, "region_id": "REG-DEU", "primary_port_id": "PORT-HAM", "route_id": "RT-HAM-SGP-CAPE", "material_id": "MAT-OC", "is_primary": False},
    {"id": "SG-OC-03", "name": "Sumitomo Electric (Japan)", "country": "Japan", "city": "Osaka", "quality_tier": "A", "reliability_score": 0.97, "capacity_units_per_month": 4500, "lead_time_days": 18, "cost_per_unit_sgd": 298.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-JPN", "primary_port_id": "PORT-OSA", "route_id": "RT-OSA-SGP", "material_id": "MAT-OC", "is_primary": False},
    {"id": "SG-OC-04", "name": "Focuslight Technologies (China)", "country": "China", "city": "Xi'an", "quality_tier": "A-", "reliability_score": 0.85, "capacity_units_per_month": 6000, "lead_time_days": 15, "cost_per_unit_sgd": 195.00, "contract_type": "spot", "annual_volume_sgd": 0.0, "certifications": ["ISO9001"], "is_available": True, "unavailability_reason": None, "region_id": "REG-CHN", "primary_port_id": "PORT-SHA", "route_id": "RT-SHA-SGP", "material_id": "MAT-OC", "is_primary": False},
]

FACTORIES = [
    {"id": "FAC-SGP-01", "name": "Singapore Main Assembly Plant", "country": "Singapore", "city": "Tuas", "daily_capacity_units": 850, "current_utilization_pct": 0.78},
    {"id": "FAC-VNM-01", "name": "Ho Chi Minh City Plant", "country": "Vietnam", "city": "Ho Chi Minh City", "daily_capacity_units": 220, "current_utilization_pct": 0.65},
]

WAREHOUSES = [
    {"id": "WH-SGP-01", "name": "Singapore Hub Warehouse", "country": "Singapore", "city": "Singapore", "region_label": "APAC"},
    {"id": "WH-NLD-01", "name": "Rotterdam Distribution Centre", "country": "Netherlands", "city": "Rotterdam", "region_label": "EMEA"},
    {"id": "WH-USA-01", "name": "Los Angeles Fulfilment Centre", "country": "USA", "city": "Los Angeles", "region_label": "AMER"},
]

# Demand split across the two factories for REQUIRES relationships
FACTORY_DEMAND_SPLIT = {"FAC-SGP-01": 0.8, "FAC-VNM-01": 0.2}

# DisruptionEvent -> AFFECTS / DIRECTLY_IMPACTS wiring
EVENT_AFFECTS_REGIONS = {
    "DISRUPT-001": ["REG-ISR"],
    "DISRUPT-002": ["REG-DEU", "REG-BEL"],
    "DISRUPT-003": ["REG-QAT", "REG-UAE", "REG-RUS"],
    "DISRUPT-004": ["REG-QAT"],
    "DISRUPT-005": ["REG-UAE", "REG-RUS"],
}
EVENT_AFFECTS_PORTS = {
    "DISRUPT-001": ["PORT-HAI"],
    "DISRUPT-002": [],
    "DISRUPT-003": ["PORT-RAS", "PORT-JEA"],
    "DISRUPT-004": ["PORT-RAS"],
    "DISRUPT-005": ["PORT-JEA"],
}
EVENT_AFFECTS_ROUTES = {
    "DISRUPT-001": ["RT-ISR-SGP"],
    "DISRUPT-002": ["RT-ISR-SGP", "RT-HAM-SGP-CAPE", "RT-ANT-SGP-CAPE"],
    "DISRUPT-003": ["RT-GULF-SGP"],
    "DISRUPT-004": ["RT-GULF-SGP"],
    "DISRUPT-005": ["RT-GULF-SGP"],
}
EVENT_IMPACTS_SUPPLIERS = {
    "DISRUPT-001": ["SG-PB-01", "SG-OC-01"],
    "DISRUPT-004": ["SG-HE-01"],
    "DISRUPT-005": ["SG-PM-01"],
}

# ---------------------------------------------------------------------------
# Eval-only disruption events (DISRUPT-101..104)
# Seeded is_active: False — activated per eval scenario only, never in demos.
# Wiring is inline (affects_ports / affects_regions / directly_impacts).
# ---------------------------------------------------------------------------

EVAL_DISRUPTION_EVENTS = [
    {
        "id": "DISRUPT-101", "name": "Super Typhoon Koinu — Kaohsiung Closure",
        "type": "WEATHER", "severity": "HIGH", "affected_region": "Taiwan",
        "start_date": "2026-03-15", "source": "Taiwan CWA", "source_url": "https://www.cwa.gov.tw",
        "description": "Super Typhoon forces closure of Port of Kaohsiung for an estimated 8 days. All container operations suspended.",
        "is_active": False,
        "affects_ports": ["PORT-KAO"], "affects_regions": ["REG-TWN"], "directly_impacts": [],
    },
    {
        "id": "DISRUPT-102", "name": "PenangChip Fabrication Plant Fire",
        "type": "SUPPLIER", "severity": "CRITICAL", "affected_region": "Malaysia",
        "start_date": "2026-03-18", "source": "The Star Malaysia", "source_url": "https://www.thestar.com.my",
        "description": "Major fire at PenangChip's Penang fabrication facility. Production halted indefinitely pending damage assessment.",
        "is_active": False,
        "affects_ports": [], "affects_regions": [], "directly_impacts": ["SG-IC-04"],
    },
    {
        "id": "DISRUPT-103", "name": "Taiwan Strait Maritime Exclusion Zone",
        "type": "GEOPOLITICAL", "severity": "CRITICAL", "affected_region": "Taiwan",
        "start_date": "2026-03-20", "source": "Reuters", "source_url": "https://reuters.com",
        "description": "Military exercises establish a maritime exclusion zone across the Taiwan Strait. Commercial shipping suspended.",
        "is_active": False,
        "affects_ports": ["PORT-KAO"], "affects_regions": ["REG-TWN"], "directly_impacts": [],
    },
    {
        "id": "DISRUPT-104", "name": "Shanghai Port Severe Congestion",
        "type": "PORT", "severity": "MEDIUM", "affected_region": "China",
        "start_date": "2026-03-22", "source": "Lloyd's List", "source_url": "https://lloydslist.com",
        "description": "Berth congestion at Port of Shanghai producing 6-day average delays on outbound container traffic.",
        "is_active": False,
        "affects_ports": ["PORT-SHA"], "affects_regions": [], "directly_impacts": [],
    },
]

# Keys on eval event dicts that are relationship wiring, not node properties
_EVAL_EVENT_WIRING_KEYS = ("affects_ports", "affects_regions", "directly_impacts")


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def seed_constraints(client):
    for stmt in CONSTRAINTS:
        client.run_write(stmt)
    print(f"  ✓ {len(CONSTRAINTS)} constraints")


def seed_nodes(client):
    client.run_write(
        "MERGE (c:Company {id: $id}) SET c += $props",
        {"id": COMPANY["id"], "props": COMPANY},
    )
    for region in REGIONS:
        client.run_write(
            "MERGE (r:Region {id: $id}) SET r += $props",
            {"id": region["id"], "props": region},
        )
    for port in PORTS:
        client.run_write(
            "MERGE (p:Port {id: $id}) SET p += $props",
            {"id": port["id"], "props": port},
        )
    for route in ROUTES:
        client.run_write(
            "MERGE (r:ShippingRoute {id: $id}) SET r += $props",
            {"id": route["id"], "props": route},
        )
    for event in DISRUPTION_EVENTS:
        client.run_write(
            "MERGE (e:DisruptionEvent {id: $id}) SET e += $props",
            {"id": event["id"], "props": event},
        )
    for material in MATERIALS:
        client.run_write(
            "MERGE (m:Material {id: $id}) SET m += $props",
            {"id": material["id"], "props": material},
        )
    for factory in FACTORIES:
        client.run_write(
            "MERGE (f:Factory {id: $id}) SET f += $props",
            {"id": factory["id"], "props": factory},
        )
    for warehouse in WAREHOUSES:
        client.run_write(
            "MERGE (w:Warehouse {id: $id}) SET w += $props",
            {"id": warehouse["id"], "props": warehouse},
        )
    for supplier in SUPPLIERS:
        node_props = {
            k: v
            for k, v in supplier.items()
            if k not in ("region_id", "material_id", "is_primary")
        }
        client.run_write(
            "MERGE (s:Supplier {id: $id}) SET s += $props",
            {"id": supplier["id"], "props": node_props},
        )
    print(
        f"  ✓ nodes: 1 company, {len(REGIONS)} regions, {len(PORTS)} ports, "
        f"{len(ROUTES)} routes, {len(DISRUPTION_EVENTS)} events, {len(MATERIALS)} materials, "
        f"{len(SUPPLIERS)} suppliers, {len(FACTORIES)} factories, {len(WAREHOUSES)} warehouses"
    )


def seed_relationships(client):
    for factory in FACTORIES:
        client.run_write(
            """
            MATCH (c:Company {id: $company_id}), (f:Factory {id: $factory_id})
            MERGE (c)-[:OPERATES]->(f)
            """,
            {"company_id": COMPANY["id"], "factory_id": factory["id"]},
        )
    for warehouse in WAREHOUSES:
        client.run_write(
            """
            MATCH (c:Company {id: $company_id}), (w:Warehouse {id: $warehouse_id})
            MERGE (c)-[:OPERATES]->(w)
            """,
            {"company_id": COMPANY["id"], "warehouse_id": warehouse["id"]},
        )

    for factory_id, split in FACTORY_DEMAND_SPLIT.items():
        for material in MATERIALS:
            client.run_write(
                """
                MATCH (f:Factory {id: $factory_id}), (m:Material {id: $material_id})
                MERGE (f)-[rel:REQUIRES]->(m)
                SET rel.monthly_units = $monthly_units
                """,
                {
                    "factory_id": factory_id,
                    "material_id": material["id"],
                    "monthly_units": int(material["monthly_demand_units"] * split),
                },
            )

    for supplier in SUPPLIERS:
        client.run_write(
            """
            MATCH (s:Supplier {id: $supplier_id}), (m:Material {id: $material_id})
            MERGE (s)-[rel:SUPPLIES]->(m)
            SET rel.cost_per_unit_sgd = $cost_per_unit_sgd,
                rel.lead_time_days = $lead_time_days,
                rel.quality_tier = $quality_tier,
                rel.annual_volume_sgd = $annual_volume_sgd,
                rel.contract_type = $contract_type,
                rel.is_primary = $is_primary
            """,
            {
                "supplier_id": supplier["id"],
                "material_id": supplier["material_id"],
                "cost_per_unit_sgd": supplier["cost_per_unit_sgd"],
                "lead_time_days": supplier["lead_time_days"],
                "quality_tier": supplier["quality_tier"],
                "annual_volume_sgd": supplier["annual_volume_sgd"],
                "contract_type": supplier["contract_type"],
                "is_primary": supplier["is_primary"],
            },
        )
        client.run_write(
            """
            MATCH (s:Supplier {id: $supplier_id}), (r:Region {id: $region_id})
            MERGE (s)-[:LOCATED_IN]->(r)
            """,
            {"supplier_id": supplier["id"], "region_id": supplier["region_id"]},
        )
        client.run_write(
            """
            MATCH (s:Supplier {id: $supplier_id}), (p:Port {id: $port_id})
            MERGE (s)-[rel:SHIPS_VIA]->(p)
            SET rel.is_primary_port = true
            """,
            {"supplier_id": supplier["id"], "port_id": supplier["primary_port_id"]},
        )

    for route in ROUTES:
        client.run_write(
            """
            MATCH (origin:Port {id: $origin_id}), (dest:Port {id: $dest_id})
            MERGE (origin)-[rel:ROUTE_TO {route_id: $route_id}]->(dest)
            SET rel.transit_days_normal = $transit_days_normal,
                rel.transit_days_current = $transit_days_current,
                rel.is_disrupted = $is_disrupted
            """,
            {
                "origin_id": route["origin_port_id"],
                "dest_id": route["destination_port_id"],
                "route_id": route["id"],
                "transit_days_normal": route["transit_days_normal"],
                "transit_days_current": route["transit_days_current"],
                "is_disrupted": route["is_disrupted"],
            },
        )

    for event_id, region_ids in EVENT_AFFECTS_REGIONS.items():
        for region_id in region_ids:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (r:Region {id: $region_id})
                MERGE (e)-[:AFFECTS]->(r)
                """,
                {"event_id": event_id, "region_id": region_id},
            )
    for event_id, port_ids in EVENT_AFFECTS_PORTS.items():
        for port_id in port_ids:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (p:Port {id: $port_id})
                MERGE (e)-[:AFFECTS]->(p)
                """,
                {"event_id": event_id, "port_id": port_id},
            )
    for event_id, route_ids in EVENT_AFFECTS_ROUTES.items():
        for route_id in route_ids:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (r:ShippingRoute {id: $route_id})
                MERGE (e)-[:AFFECTS]->(r)
                """,
                {"event_id": event_id, "route_id": route_id},
            )
    for event_id, supplier_ids in EVENT_IMPACTS_SUPPLIERS.items():
        for supplier_id in supplier_ids:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (s:Supplier {id: $supplier_id})
                MERGE (e)-[:DIRECTLY_IMPACTS]->(s)
                """,
                {"event_id": event_id, "supplier_id": supplier_id},
            )
    print("  ✓ relationships: OPERATES, REQUIRES, SUPPLIES, LOCATED_IN, SHIPS_VIA, ROUTE_TO, AFFECTS, DIRECTLY_IMPACTS")


def seed_eval_events(client):
    """Seed DISRUPT-101..104 (is_active: False) and their AFFECTS/DIRECTLY_IMPACTS wiring."""
    for event in EVAL_DISRUPTION_EVENTS:
        node_props = {k: v for k, v in event.items() if k not in _EVAL_EVENT_WIRING_KEYS}
        client.run_write(
            "MERGE (e:DisruptionEvent {id: $id}) SET e += $props",
            {"id": event["id"], "props": node_props},
        )
        for port_id in event["affects_ports"]:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (p:Port {id: $port_id})
                MERGE (e)-[:AFFECTS]->(p)
                """,
                {"event_id": event["id"], "port_id": port_id},
            )
        for region_id in event["affects_regions"]:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (r:Region {id: $region_id})
                MERGE (e)-[:AFFECTS]->(r)
                """,
                {"event_id": event["id"], "region_id": region_id},
            )
        for supplier_id in event["directly_impacts"]:
            client.run_write(
                """
                MATCH (e:DisruptionEvent {id: $event_id}), (s:Supplier {id: $supplier_id})
                MERGE (e)-[:DIRECTLY_IMPACTS]->(s)
                """,
                {"event_id": event["id"], "supplier_id": supplier_id},
            )
    print(f"  ✓ {len(EVAL_DISRUPTION_EVENTS)} eval events (is_active: False) with wiring")


def main():
    import os

    from dotenv import load_dotenv

    from database.neo4j_client import get_client

    load_dotenv()
    print(f"URI from env: {os.getenv('NEO4J_URI')}")
    client = get_client()
    if not client.verify_connectivity():
        raise SystemExit("Cannot connect to Neo4j — check NEO4J_URI / credentials in backend/.env")
    print("Seeding SupplyChainAI digital twin (idempotent, MERGE-only)...")
    seed_constraints(client)
    seed_nodes(client)
    seed_relationships(client)
    seed_eval_events(client)
    print("Done.")
    client.close()


if __name__ == "__main__":
    main()
