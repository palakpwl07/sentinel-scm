"""Canned scenario definitions for the March 2026 Middle East crisis."""

SCENARIOS = {
    "march_2026_full": {
        "id": "march_2026_full",
        "name": "March 2026 Middle East Crisis — Full Impact",
        "description": "Simultaneous Strait of Hormuz closure and Red Sea blockade. First time in modern history both corridors blocked.",
        "trigger_date": "2026-03-04",
        "active_event_ids": ["DISRUPT-001", "DISRUPT-002", "DISRUPT-003", "DISRUPT-004", "DISRUPT-005"],
        "event_description": "US and Israel launched Operation Epic Fury on Feb 28 2026. Iran retaliated by closing the Strait of Hormuz on March 2. Houthi forces resumed Red Sea attacks Feb 28. QatarEnergy invoked force majeure on March 4. Jebel Ali port severely disrupted. Both primary maritime corridors from Middle East and Europe to Asia are simultaneously blocked for the first time in modern history."
    },
    "hormuz_only": {
        "id": "hormuz_only",
        "name": "Strait of Hormuz Closure Only",
        "description": "Hormuz closed, Red Sea operational. Gulf suppliers and Qatar affected.",
        "trigger_date": "2026-03-02",
        "active_event_ids": ["DISRUPT-003", "DISRUPT-004", "DISRUPT-005"],
        "event_description": "IRGC declares Strait of Hormuz closed March 2. QatarEnergy force majeure. Jebel Ali disrupted. European Suez route still operational."
    },
    "israel_conflict_only": {
        "id": "israel_conflict_only",
        "name": "Israel Conflict — Supplier Offline",
        "description": "Israeli suppliers unavailable, Gulf routes intact.",
        "trigger_date": "2026-02-28",
        "active_event_ids": ["DISRUPT-001", "DISRUPT-002"],
        "event_description": "US-Israel Operation Epic Fury. Israeli suppliers offline. Houthi Red Sea attacks resumed. European Suez route disrupted."
    },
}
