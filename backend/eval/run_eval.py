"""Eval orchestrator.

For each of the 25 scenarios:
  1. Compute ground truth via ground_truth.compute_affected_suppliers()
  2. Run the full agent society (invokes the LangGraph graph directly — no
     FastAPI/SSE layer; a separate graph instance is compiled WITHOUT
     interrupt_before so HITL never blocks)
  3. Run the single-agent baseline
  4. Compute metrics for both
  5. Write per-scenario results

Then aggregate and write eval/results/eval_results.json + eval_report.md.

The Neo4j world state (event is_active flags, supplier availability, port and
route disruption flags) is activated per scenario and restored to the demo
default (DISRUPT-001..005 active, DISRUPT-101..104 inactive) in a finally
block, even on error.

Run from the repo root:  python eval/run_eval.py
"""

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
EVAL_DIR = ROOT / "eval"
RESULTS_DIR = EVAL_DIR / "results"

# backend/ must precede eval/ on sys.path so `scenarios` resolves to the
# backend package (agents import scenarios.march_2026); eval's own scenarios.py
# is loaded below via importlib under a non-colliding name.
sys.path.insert(0, str(BACKEND))
if str(EVAL_DIR) not in sys.path:
    sys.path.append(str(EVAL_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND / ".env")

import importlib.util  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ground_truth = _load_module("eval_ground_truth", EVAL_DIR / "ground_truth.py")
eval_scenarios = _load_module("eval_scenarios", EVAL_DIR / "scenarios.py")
metrics = _load_module("eval_metrics", EVAL_DIR / "metrics.py")
baseline = _load_module("eval_baseline", EVAL_DIR / "baseline.py")

import config  # noqa: E402
from database.neo4j_client import get_client  # noqa: E402
from database.seed import (  # noqa: E402
    DISRUPTION_EVENTS,
    EVAL_DISRUPTION_EVENTS,
    PORTS,
    ROUTES,
    SUPPLIERS,
    seed_eval_events,
)
from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from agents.graph import builder  # noqa: E402
from scenarios.march_2026 import SCENARIOS as DEMO_SCENARIOS  # noqa: E402

EVAL_SCENARIOS = eval_scenarios.EVAL_SCENARIOS
TIER_LABELS = eval_scenarios.TIER_LABELS

DEMO_EVENT_IDS = [e["id"] for e in DISRUPTION_EVENTS]
EVAL_EVENT_IDS = [e["id"] for e in EVAL_DISRUPTION_EVENTS]
ALL_EVENTS = ground_truth.ALL_EVENTS

# Separate graph instance WITHOUT interrupt_before — HITL never blocks in eval.
eval_graph = builder.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# World state: derive per-scenario, apply to Neo4j, restore demo defaults
# ---------------------------------------------------------------------------


def derive_world_state(active_event_ids: list[str]) -> dict:
    """Per-scenario world state derived from the seed event wiring, so the
    Neo4j graph the agents read is internally consistent with the active
    events (the seeded flags describe the full March 2026 crisis only)."""
    active = [eid for eid in active_event_ids if eid in ALL_EVENTS]
    wirings = {eid: ground_truth.event_wiring(eid) for eid in active}

    supplier_available = {}
    for supplier in SUPPLIERS:
        unavailable = any(
            supplier["id"] in w["suppliers"]
            or (
                supplier["region_id"] in w["regions"]
                and ALL_EVENTS[eid]["severity"] == "CRITICAL"
            )
            for eid, w in wirings.items()
        )
        supplier_available[supplier["id"]] = not unavailable

    port_state = {}
    for port in PORTS:
        hits = [eid for eid, w in wirings.items() if port["id"] in w["ports"]]
        if hits:
            severity = port["disruption_severity"] or max(
                (ALL_EVENTS[eid]["severity"] for eid in hits),
                key=lambda s: {"MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}.get(s, 0),
            )
            port_state[port["id"]] = {"is_disrupted": True, "severity": severity}
        else:
            port_state[port["id"]] = {"is_disrupted": False, "severity": None}

    route_state = {}
    for route in ROUTES:
        hit = any(route["id"] in w["routes"] for w in wirings.values())
        if hit and route["is_disrupted"]:
            route_state[route["id"]] = {
                "is_disrupted": True,
                "disruption_type": route["disruption_type"],
                "transit_days_current": route["transit_days_current"],
                "freight_cost_sgd_per_unit_current": route["freight_cost_sgd_per_unit_current"],
            }
        else:
            route_state[route["id"]] = {
                "is_disrupted": False,
                "disruption_type": None,
                "transit_days_current": route["transit_days_normal"],
                "freight_cost_sgd_per_unit_current": route["freight_cost_sgd_per_unit_normal"],
            }

    return {
        "supplier_available": supplier_available,
        "port_state": port_state,
        "route_state": route_state,
    }


def apply_world_state(client, active_event_ids: list[str], world: dict) -> None:
    for event_id in ALL_EVENTS:
        client.run_write(
            "MERGE (e:DisruptionEvent {id: $id}) SET e.is_active = $active",
            {"id": event_id, "active": event_id in active_event_ids},
        )
    for supplier in SUPPLIERS:
        available = world["supplier_available"][supplier["id"]]
        reason = None
        if not available:
            reason = supplier["unavailability_reason"] or "Unavailable under active disruption events"
        client.run_write(
            "MERGE (s:Supplier {id: $id}) SET s.is_available = $available, s.unavailability_reason = $reason",
            {"id": supplier["id"], "available": available, "reason": reason},
        )
    for port in PORTS:
        state = world["port_state"][port["id"]]
        client.run_write(
            "MERGE (p:Port {id: $id}) SET p.is_disrupted = $disrupted, p.disruption_severity = $severity",
            {"id": port["id"], "disrupted": state["is_disrupted"], "severity": state["severity"]},
        )
    for route in ROUTES:
        state = world["route_state"][route["id"]]
        client.run_write(
            """
            MERGE (r:ShippingRoute {id: $id})
            SET r.is_disrupted = $disrupted, r.disruption_type = $dtype,
                r.transit_days_current = $transit, r.freight_cost_sgd_per_unit_current = $freight
            """,
            {
                "id": route["id"], "disrupted": state["is_disrupted"],
                "dtype": state["disruption_type"], "transit": state["transit_days_current"],
                "freight": state["freight_cost_sgd_per_unit_current"],
            },
        )
        client.run_write(
            """
            MATCH (:Port)-[rel:ROUTE_TO {route_id: $route_id}]->(:Port)
            SET rel.is_disrupted = $disrupted, rel.transit_days_current = $transit
            """,
            {"route_id": route["id"], "disrupted": state["is_disrupted"],
             "transit": state["transit_days_current"]},
        )


def restore_default_state(client) -> None:
    """Demo default: DISRUPT-001..005 active, 101..104 inactive; supplier,
    port, and route flags exactly as authored in the seed constants."""
    for event_id in DEMO_EVENT_IDS:
        client.run_write(
            "MERGE (e:DisruptionEvent {id: $id}) SET e.is_active = true", {"id": event_id}
        )
    for event_id in EVAL_EVENT_IDS:
        client.run_write(
            "MERGE (e:DisruptionEvent {id: $id}) SET e.is_active = false", {"id": event_id}
        )
    for supplier in SUPPLIERS:
        client.run_write(
            "MERGE (s:Supplier {id: $id}) SET s.is_available = $available, s.unavailability_reason = $reason",
            {"id": supplier["id"], "available": supplier["is_available"],
             "reason": supplier["unavailability_reason"]},
        )
    for port in PORTS:
        client.run_write(
            "MERGE (p:Port {id: $id}) SET p.is_disrupted = $disrupted, p.disruption_severity = $severity",
            {"id": port["id"], "disrupted": port["is_disrupted"],
             "severity": port["disruption_severity"]},
        )
    for route in ROUTES:
        client.run_write(
            """
            MERGE (r:ShippingRoute {id: $id})
            SET r.is_disrupted = $disrupted, r.disruption_type = $dtype,
                r.transit_days_current = $transit, r.freight_cost_sgd_per_unit_current = $freight
            """,
            {
                "id": route["id"], "disrupted": route["is_disrupted"],
                "dtype": route["disruption_type"], "transit": route["transit_days_current"],
                "freight": route["freight_cost_sgd_per_unit_current"],
            },
        )
        client.run_write(
            """
            MATCH (:Port)-[rel:ROUTE_TO {route_id: $route_id}]->(:Port)
            SET rel.is_disrupted = $disrupted, rel.transit_days_current = $transit
            """,
            {"route_id": route["id"], "disrupted": route["is_disrupted"],
             "transit": route["transit_days_current"]},
        )


# ---------------------------------------------------------------------------
# Agent society + baseline runners
# ---------------------------------------------------------------------------


def _scenario_description(active_event_ids: list[str]) -> str:
    return " ".join(ALL_EVENTS[eid]["description"] for eid in active_event_ids)


def run_agent_society(scenario: dict) -> dict:
    """Invoke the LangGraph graph directly and return the final state."""
    initial_state = {
        "scenario_id": scenario["id"],
        "event_description": _scenario_description(scenario["active_event_ids"]),
        "event_date": "2026-03-04",
        "detected_events": [], "affected_regions": [], "affected_ports": [],
        "affected_suppliers": [], "inventory_runways": {},
        "overall_risk_score": 0.0, "risk_justification": "",
        "proposed_strategies": [], "strategy_evaluations": [],
        "negotiation_rounds": [], "negotiation_resolved": False,
        "negotiation_round_count": 0, "final_recommendation": None,
        "awaiting_human_approval": False, "human_decision": None, "human_notes": None,
        "agent_messages": [],
    }
    thread = {"configurable": {"thread_id": f"eval-{scenario['id']}-{int(time.time())}"}}
    return eval_graph.invoke(initial_state, thread)


def extract_agent_predictions(state: dict) -> dict:
    affected = state.get("affected_suppliers", [])
    risk_map = {s["supplier_id"]: s["risk_level"] for s in affected}

    strategies = {s["strategy_id"]: s for s in state.get("proposed_strategies", [])}
    predicted_costs, true_costs = {}, {}
    best_material, best_revenue = None, -1.0
    for evaluation in state.get("strategy_evaluations", []):
        strategy = strategies.get(evaluation["strategy_id"])
        if strategy is None:
            continue
        predicted_costs[evaluation["strategy_id"]] = evaluation["additional_cost_sgd"]
        try:
            true_costs[evaluation["strategy_id"]] = ground_truth.compute_true_mitigation_cost(
                strategy["strategy_type"], strategy["material_id"],
                strategy.get("target_supplier_id") or "",
                strategy["quantity_units"], strategy["urgency_days"],
            )
        except Exception:
            pass
        if evaluation["revenue_protected_sgd"] > best_revenue:
            best_revenue = evaluation["revenue_protected_sgd"]
            best_material = strategy["material_id"]

    if best_material is None:
        runways = state.get("inventory_runways", {})
        if runways:
            best_material = max(
                runways, key=lambda mid: runways[mid].get("at_risk_revenue_sgd", 0.0)
            )

    return {
        "affected_set": set(risk_map),
        "risk_map": risk_map,
        "predicted_costs": predicted_costs,
        "true_costs": true_costs,
        "predicted_material": best_material,
        "agent_message_count": len(state.get("agent_messages", [])),
    }


def extract_baseline_predictions(payload: dict, material_runways: dict) -> dict:
    risk_map = {}
    for entry in payload.get("affected_suppliers", []):
        sid = entry.get("supplier_id")
        if sid:
            risk_map[sid] = entry.get("risk_level", "HIGH")

    predicted_costs, true_costs = {}, {}
    for idx, strategy in enumerate(payload.get("recommended_strategies", [])):
        key = f"baseline-{idx}"
        cost = strategy.get("estimated_additional_cost_sgd")
        if cost is None:
            continue
        predicted_costs[key] = float(cost)
        try:
            material_id = strategy["material_id"]
            urgency = material_runways.get(material_id, 14)
            true_costs[key] = ground_truth.compute_true_mitigation_cost(
                strategy.get("strategy_type", ""), material_id,
                strategy.get("target_supplier_id") or "",
                int(strategy.get("quantity_units", 0)), int(urgency),
            )
        except Exception:
            pass

    return {
        "affected_set": set(risk_map),
        "risk_map": risk_map,
        "predicted_costs": predicted_costs,
        "true_costs": true_costs,
        "predicted_material": payload.get("highest_risk_material_id"),
    }


# ---------------------------------------------------------------------------
# Scoring + reporting
# ---------------------------------------------------------------------------


def score_side(predictions: dict, truth: dict, true_material: str) -> dict:
    actual_set = {sid for sid, v in truth.items() if v["affected"]}
    actual_risk = {sid: truth[sid]["risk_level"] for sid in actual_set}
    detection = metrics.supplier_detection_metrics(predictions["affected_set"], actual_set)
    return {
        "detection": detection,
        "risk_level_accuracy": metrics.risk_level_accuracy(
            predictions["risk_map"], actual_risk
        ),
        "cost": metrics.cost_accuracy(
            predictions["predicted_costs"], predictions["true_costs"]
        ),
        "predicted_material": predictions["predicted_material"],
        "correct_material": metrics.decision_quality(
            predictions["predicted_material"], true_material
        ),
    }


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def aggregate(results: list[dict], side: str) -> dict:
    ok = [r for r in results if r.get("status") == "ok" and r.get(side)]
    pooled_errors = []
    for r in ok:
        pooled_errors.extend(r[side]["cost"]["per_strategy_errors"].values())
    return {
        "precision": _mean([r[side]["detection"]["precision"] for r in ok]),
        "recall": _mean([r[side]["detection"]["recall"] for r in ok]),
        "f1": _mean([r[side]["detection"]["f1"] for r in ok]),
        "risk_level_accuracy": _mean([r[side]["risk_level_accuracy"] for r in ok]),
        "cost_mape": round(sum(pooled_errors) / len(pooled_errors), 2) if pooled_errors else None,
        "correct_material": sum(1 for r in ok if r[side]["correct_material"]),
        "scored_scenarios": len(ok),
    }


def tier_f1(results: list[dict], side: str) -> dict:
    out = {}
    for tier, label in TIER_LABELS.items():
        rows = [
            r for r in results
            if r.get("status") == "ok" and r.get(side) and r["tier"] == tier
        ]
        out[label] = _mean([r[side]["detection"]["f1"] for r in rows])
    return out


def _fmt(value, digits=2):
    return "n/a" if value is None else f"{value:.{digits}f}"


def write_report(results: list[dict], agent_calls: int) -> str:
    agent_agg = aggregate(results, "agent")
    base_agg = aggregate(results, "baseline")
    agent_tiers = tier_f1(results, "agent")
    base_tiers = tier_f1(results, "baseline")
    n = len(results)
    failures = [r for r in results if r.get("status") != "ok"]

    lines = [
        "# Evaluation Results",
        "",
        f"Scenarios: {n} | Agent calls: ~{agent_calls} | Run date: "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        "",
        "## Headline",
        "",
        "| Metric | Agent Society | Single-Agent Baseline | Delta |",
        "|---|---|---|---|",
        f"| Supplier detection precision | {_fmt(agent_agg['precision'])} | {_fmt(base_agg['precision'])} | "
        f"{agent_agg['precision'] - base_agg['precision']:+.2f} |",
        f"| Supplier detection recall | {_fmt(agent_agg['recall'])} | {_fmt(base_agg['recall'])} | "
        f"{agent_agg['recall'] - base_agg['recall']:+.2f} |",
        f"| Supplier detection F1 | {_fmt(agent_agg['f1'])} | {_fmt(base_agg['f1'])} | "
        f"{agent_agg['f1'] - base_agg['f1']:+.2f} |",
        f"| Risk level accuracy | {_fmt(agent_agg['risk_level_accuracy'])} | "
        f"{_fmt(base_agg['risk_level_accuracy'])} | "
        f"{agent_agg['risk_level_accuracy'] - base_agg['risk_level_accuracy']:+.2f} |",
        f"| Cost estimate MAPE | {_fmt(agent_agg['cost_mape'], 1)}% | {_fmt(base_agg['cost_mape'], 1)}% | "
        + (
            f"{agent_agg['cost_mape'] - base_agg['cost_mape']:+.1f}% |"
            if agent_agg["cost_mape"] is not None and base_agg["cost_mape"] is not None
            else "n/a |"
        ),
        f"| Correct material prioritised | {agent_agg['correct_material']}/{n} | "
        f"{base_agg['correct_material']}/{n} | "
        f"{agent_agg['correct_material'] - base_agg['correct_material']:+d} |",
        "",
        "## By scenario tier",
        "",
        "| Tier | Agent F1 | Baseline F1 |",
        "|---|---|---|",
    ]
    for label in TIER_LABELS.values():
        lines.append(f"| {label} | {_fmt(agent_tiers[label])} | {_fmt(base_tiers[label])} |")

    lines += ["", "## Per-scenario detail", "",
              "| Scenario | Agent P/R/F1 | Baseline P/R/F1 | Agent FN | Baseline FN |",
              "|---|---|---|---|---|"]
    for r in results:
        if r.get("status") != "ok":
            lines.append(f"| {r['id']} ({r['name']}) | FAILED | FAILED | — | — |")
            continue
        a, b = r["agent"]["detection"], r["baseline"]["detection"] if r.get("baseline") else None
        a_str = f"{a['precision']:.2f}/{a['recall']:.2f}/{a['f1']:.2f}"
        b_str = f"{b['precision']:.2f}/{b['recall']:.2f}/{b['f1']:.2f}" if b else "n/a"
        a_fn = ", ".join(a["false_negatives"]) or "—"
        b_fn = (", ".join(b["false_negatives"]) or "—") if b else "n/a"
        lines.append(f"| {r['id']} ({r['name']}) | {a_str} | {b_str} | {a_fn} | {b_fn} |")

    lines += ["", "## Failure analysis", ""]
    weak = [r for r in results if r.get("status") == "ok" and r["agent"]["detection"]["f1"] < 0.8]
    if not weak and not failures:
        lines.append("No scenario fell below agent F1 0.8 and no scenario errored.")
    for r in weak:
        missed = r["agent"]["detection"]["false_negatives"]
        lines.append(f"- **{r['id']} ({r['name']})** — agent F1 {r['agent']['detection']['f1']:.2f}.")
        for sid in missed:
            paths = ", ".join(r["ground_truth"][sid]["reason_paths"]) or "n/a"
            lines.append(f"  - Missed `{sid}` (propagation path: {paths})")
        for sid in r["agent"]["detection"]["false_positives"]:
            lines.append(f"  - False positive `{sid}` (ground truth says unaffected)")
    for r in failures:
        lines.append(f"- **{r['id']}** — run FAILED: {r.get('error', 'unknown')[:300]}")

    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    client = get_client()
    if not client.verify_connectivity():
        raise SystemExit("Cannot connect to Neo4j — check backend/.env")

    seed_eval_events(client)  # idempotent: ensure DISRUPT-101..104 exist

    # Reproducibility: force temperature 0 on the shared Qwen helpers for the
    # duration of the eval (agents bind these function objects at import time,
    # so mutating the defaults reaches every call site).
    orig_chat_defaults = config.qwen_chat.__defaults__
    orig_json_defaults = config.qwen_chat_json.__defaults__
    config.qwen_chat.__defaults__ = (0.0,)
    config.qwen_chat_json.__defaults__ = (0.0,)

    injected_scenario_ids = []
    results = []
    total_agent_messages = 0

    try:
        for index, scenario in enumerate(EVAL_SCENARIOS, start=1):
            sid, name = scenario["id"], scenario["name"]
            active_ids = scenario["active_event_ids"]

            # Make the scenario resolvable by the (unmodified) monitoring/risk agents
            if sid not in DEMO_SCENARIOS:
                DEMO_SCENARIOS[sid] = {
                    "id": sid,
                    "name": name,
                    "description": name,
                    "trigger_date": "2026-03-04",
                    "active_event_ids": active_ids,
                    "event_description": _scenario_description(active_ids),
                }
                injected_scenario_ids.append(sid)

            truth = ground_truth.compute_affected_suppliers(active_ids)
            true_material = ground_truth.compute_highest_risk_material(active_ids)
            world = derive_world_state(active_ids)
            material_runways = {
                m["id"]: m["current_inventory_days"]
                for m in ground_truth.MATERIALS
            }

            record = {
                "id": sid, "name": name, "tier": scenario["tier"],
                "active_event_ids": active_ids, "status": "ok",
                "ground_truth": truth, "true_material": true_material,
            }

            try:
                apply_world_state(client, active_ids, world)

                state = run_agent_society(scenario)
                agent_pred = extract_agent_predictions(state)
                total_agent_messages += agent_pred["agent_message_count"]
                record["agent"] = score_side(agent_pred, truth, true_material)

                try:
                    baseline_payload = baseline.run_baseline(active_ids, world)
                    baseline_pred = extract_baseline_predictions(
                        baseline_payload, material_runways
                    )
                    record["baseline"] = score_side(baseline_pred, truth, true_material)
                except Exception:
                    record["baseline"] = None
                    record["baseline_error"] = traceback.format_exc()

                a = record["agent"]["detection"]
                b = record["baseline"]["detection"] if record["baseline"] else None
                progress = (
                    f"[{index}/{len(EVAL_SCENARIOS)}] {sid} ({name})  "
                    f"agent: P={a['precision']:.2f} R={a['recall']:.2f}"
                )
                if b:
                    progress += f" | baseline: P={b['precision']:.2f} R={b['recall']:.2f}"
                else:
                    progress += " | baseline: FAILED"
                print(progress, flush=True)

            except Exception:
                record["status"] = "failed"
                record["error"] = traceback.format_exc()
                print(f"[{index}/{len(EVAL_SCENARIOS)}] {sid} FAILED — continuing", flush=True)

            results.append(record)
            time.sleep(1.5)  # stay clear of Qwen rate limits

    finally:
        # Always restore the demo default world, injected scenarios, and temps
        try:
            restore_default_state(client)
            print("Restored demo default event state (DISRUPT-001..005 active).")
        except Exception:
            print("WARNING: failed to restore default event state:", file=sys.stderr)
            traceback.print_exc()
        for sid in injected_scenario_ids:
            DEMO_SCENARIOS.pop(sid, None)
        config.qwen_chat.__defaults__ = orig_chat_defaults
        config.qwen_chat_json.__defaults__ = orig_json_defaults

    results_path = RESULTS_DIR / "eval_results.json"
    results_path.write_text(
        json.dumps(results, indent=2, default=str), encoding="utf-8"
    )
    report = write_report(results, agent_calls=total_agent_messages)
    report_path = RESULTS_DIR / "eval_report.md"
    report_path.write_text(report, encoding="utf-8")

    print(f"\nWrote {results_path}")
    print(f"Wrote {report_path}")
    failed = sum(1 for r in results if r["status"] != "ok")
    print(f"{len(results) - failed}/{len(results)} scenarios completed.")


if __name__ == "__main__":
    main()
