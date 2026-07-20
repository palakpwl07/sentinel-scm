"""Canned scenario definitions for the March 2026 Middle East crisis.

Only the full-impact hero scenario is exposed: it exercises multiple materials,
suppliers, and regions simultaneously. (The narrower hormuz_only and
israel_conflict_only variants were removed — the shared seeded world-state made
them score identically to the full crisis, so they added no demonstrable
contrast.) Live search covers narrower, single-event cases.
"""

SCENARIOS = {
    "march_2026_full": {
        "id": "march_2026_full",
        "name": "March 2026 Middle East Crisis — Full Impact",
        "description": "Simultaneous Strait of Hormuz closure and Red Sea blockade. First time in modern history both corridors blocked.",
        "trigger_date": "2026-03-04",
        "active_event_ids": ["DISRUPT-001", "DISRUPT-002", "DISRUPT-003", "DISRUPT-004", "DISRUPT-005"],
        "event_description": "US and Israel launched Operation Epic Fury on Feb 28 2026. Iran retaliated by closing the Strait of Hormuz on March 2. Houthi forces resumed Red Sea attacks Feb 28. QatarEnergy invoked force majeure on March 4. Jebel Ali port severely disrupted. Both primary maritime corridors from Middle East and Europe to Asia are simultaneously blocked for the first time in modern history."
    },
}
