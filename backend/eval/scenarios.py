"""The 25 eval scenarios — 4 tiers isolating propagation paths, compounds,
full cascades, and novel events that never appear in the demo story."""

_SHORT = {
    "DISRUPT-001": "Israel conflict",
    "DISRUPT-002": "Red Sea attacks",
    "DISRUPT-003": "Hormuz closure",
    "DISRUPT-004": "Qatar force majeure",
    "DISRUPT-005": "Jebel Ali disruption",
    "DISRUPT-101": "Kaohsiung typhoon",
    "DISRUPT-102": "PenangChip fire",
    "DISRUPT-103": "Taiwan Strait closure",
    "DISRUPT-104": "Shanghai congestion",
}


def _named(scenario: dict) -> dict:
    if "name" not in scenario:
        scenario["name"] = " + ".join(_SHORT[e] for e in scenario["active_event_ids"])
    return scenario


EVAL_SCENARIOS = [_named(s) for s in [
    # ---- Tier 1: single events (5) — isolates each propagation path ----
    {"id": "EVAL-01", "tier": 1, "name": "Israel conflict only", "active_event_ids": ["DISRUPT-001"]},
    {"id": "EVAL-02", "tier": 1, "name": "Red Sea attacks only", "active_event_ids": ["DISRUPT-002"]},
    {"id": "EVAL-03", "tier": 1, "name": "Hormuz closure only", "active_event_ids": ["DISRUPT-003"]},
    {"id": "EVAL-04", "tier": 1, "name": "QatarEnergy force majeure", "active_event_ids": ["DISRUPT-004"]},
    {"id": "EVAL-05", "tier": 1, "name": "Jebel Ali disruption only", "active_event_ids": ["DISRUPT-005"]},
    # ---- Tier 2: pairs (10) — compound / overlapping impact ----
    {"id": "EVAL-06", "tier": 2, "active_event_ids": ["DISRUPT-001", "DISRUPT-002"]},
    {"id": "EVAL-07", "tier": 2, "active_event_ids": ["DISRUPT-001", "DISRUPT-003"]},
    {"id": "EVAL-08", "tier": 2, "active_event_ids": ["DISRUPT-001", "DISRUPT-004"]},
    {"id": "EVAL-09", "tier": 2, "active_event_ids": ["DISRUPT-001", "DISRUPT-005"]},
    {"id": "EVAL-10", "tier": 2, "active_event_ids": ["DISRUPT-002", "DISRUPT-003"]},
    {"id": "EVAL-11", "tier": 2, "active_event_ids": ["DISRUPT-002", "DISRUPT-004"]},
    {"id": "EVAL-12", "tier": 2, "active_event_ids": ["DISRUPT-002", "DISRUPT-005"]},
    {"id": "EVAL-13", "tier": 2, "active_event_ids": ["DISRUPT-003", "DISRUPT-004"]},
    {"id": "EVAL-14", "tier": 2, "active_event_ids": ["DISRUPT-003", "DISRUPT-005"]},
    {"id": "EVAL-15", "tier": 2, "active_event_ids": ["DISRUPT-004", "DISRUPT-005"]},
    # ---- Tier 3: triples (5) — full cascade ----
    {"id": "EVAL-16", "tier": 3, "active_event_ids": ["DISRUPT-001", "DISRUPT-002", "DISRUPT-003"]},
    {"id": "EVAL-17", "tier": 3, "active_event_ids": ["DISRUPT-003", "DISRUPT-004", "DISRUPT-005"]},
    {"id": "EVAL-18", "tier": 3, "active_event_ids": ["DISRUPT-001", "DISRUPT-003", "DISRUPT-004"]},
    {"id": "EVAL-19", "tier": 3, "active_event_ids": ["DISRUPT-002", "DISRUPT-003", "DISRUPT-005"]},
    {"id": "EVAL-20", "tier": 3, "active_event_ids": ["DISRUPT-001", "DISRUPT-002", "DISRUPT-005"]},
    # ---- Tier 4: novel events (5) — generalisation beyond the seeded story ----
    {"id": "EVAL-21", "tier": 4, "name": "Typhoon closes Kaohsiung", "active_event_ids": ["DISRUPT-101"]},
    {"id": "EVAL-22", "tier": 4, "name": "Fire at PenangChip", "active_event_ids": ["DISRUPT-102"]},
    {"id": "EVAL-23", "tier": 4, "name": "Taiwan Strait closure", "active_event_ids": ["DISRUPT-103"]},
    {"id": "EVAL-24", "tier": 4, "name": "Shanghai port congestion", "active_event_ids": ["DISRUPT-104"]},
    {"id": "EVAL-25", "tier": 4, "name": "Typhoon + Taiwan Strait", "active_event_ids": ["DISRUPT-101", "DISRUPT-103"]},
]]

TIER_LABELS = {
    1: "Single event (5)",
    2: "Event pairs (10)",
    3: "Event triples (5)",
    4: "Novel events (5)",
}
