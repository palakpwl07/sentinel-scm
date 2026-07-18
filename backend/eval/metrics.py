"""Metrics: precision/recall/F1, risk-level accuracy, cost MAPE, decision quality."""


def supplier_detection_metrics(predicted: set[str], actual: set[str]) -> dict:
    """
    predicted: supplier_ids the system flagged as affected
    actual:    supplier_ids ground truth says are affected
    Returns {precision, recall, f1, true_positives, false_positives, false_negatives}.
    Empty-set edge case: if both empty, precision = recall = f1 = 1.0.
    """
    tp = sorted(predicted & actual)
    fp = sorted(predicted - actual)
    fn = sorted(actual - predicted)

    if not predicted and not actual:
        precision = recall = f1 = 1.0
    else:
        precision = len(tp) / len(predicted) if predicted else 0.0
        recall = len(tp) / len(actual) if actual else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
    }


def risk_level_accuracy(predicted: dict, actual: dict) -> float:
    """
    Of the correctly-identified suppliers, what fraction got the right risk level?
    Only scores true positives — a supplier missed entirely is already penalised
    by recall; double-counting it here would be dishonest.

    predicted / actual: {supplier_id: risk_level}
    """
    true_positives = set(predicted) & set(actual)
    if not true_positives:
        return 1.0
    correct = sum(1 for sid in true_positives if predicted[sid] == actual[sid])
    return round(correct / len(true_positives), 4)


def cost_accuracy(predicted_costs: dict, true_costs: dict) -> dict:
    """
    Mean absolute percentage error between cost estimates and independently
    computed true costs. Skips strategies where true_cost == 0 (undefined
    percentage error) and reports the skipped count separately.

    predicted_costs / true_costs: {strategy_key: cost_sgd}
    Returns {mape, per_strategy_errors, skipped}.
    """
    per_strategy_errors = {}
    skipped = 0
    for key in predicted_costs:
        if key not in true_costs:
            skipped += 1
            continue
        true_cost = true_costs[key]
        if true_cost == 0:
            skipped += 1
            continue
        error_pct = abs(predicted_costs[key] - true_cost) / abs(true_cost) * 100.0
        per_strategy_errors[key] = round(error_pct, 2)

    mape = (
        round(sum(per_strategy_errors.values()) / len(per_strategy_errors), 2)
        if per_strategy_errors
        else None
    )
    return {"mape": mape, "per_strategy_errors": per_strategy_errors, "skipped": skipped}


def decision_quality(predicted_material: str, true_material: str) -> bool:
    """Did the system prioritise the highest revenue-at-risk material?"""
    return predicted_material == true_material
