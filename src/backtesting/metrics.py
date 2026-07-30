from collections import Counter

DEFAULT_DIFF_RANGES = [(15, 19), (20, 24), (25, 29), (30, 999)]

def compute_metrics(rows, diff_ranges=None):
    if diff_ranges is None:
        diff_ranges = DEFAULT_DIFF_RANGES

    total = len(rows)
    selected = [r for r in rows if r['selected']]
    n_selected = len(selected)

    correct_selected = sum(1 for r in selected if r['correct'] == 1)
    accuracy_selected = correct_selected / n_selected if n_selected > 0 else 0.0

    range_metrics = {}
    for lo, hi in diff_ranges:
        bucket = [r for r in selected if lo <= r['difference'] <= hi]
        n_bucket = len(bucket)
        correct_bucket = sum(1 for r in bucket if r['correct'] == 1)
        range_metrics[f"{lo}-{hi if hi < 999 else '+'}"] = {
            "count": n_bucket,
            "correct": correct_bucket,
            "accuracy": round(correct_bucket / n_bucket, 4) if n_bucket > 0 else 0.0,
        }

    baseline_correct = sum(1 for r in rows if r['actual_code'] == "home")
    baseline_accuracy = baseline_correct / total if total > 0 else 0.0

    draws = sum(1 for r in rows if r['actual_code'] == "draw")
    coverage = n_selected / total if total > 0 else 0.0

    leagues = {}
    for r in rows:
        league = r['league']
        if league not in leagues:
            leagues[league] = {"total": 0, "selected": 0, "correct": 0}
        leagues[league]["total"] += 1
        if r['selected']:
            leagues[league]["selected"] += 1
            if r['correct'] == 1:
                leagues[league]["correct"] += 1

    league_metrics = {}
    for code, v in leagues.items():
        league_metrics[code] = {
            "total": v["total"],
            "selected": v["selected"],
            "coverage": round(v["selected"] / v["total"], 4) if v["total"] > 0 else 0.0,
            "accuracy": round(v["correct"] / v["selected"], 4) if v["selected"] > 0 else 0.0,
        }

    return {
        "n_matches": total,
        "n_selected": n_selected,
        "coverage": round(coverage, 4),
        "accuracy": round(accuracy_selected, 4),
        "baseline_home": round(baseline_accuracy, 4),
        "draw_rate": round(draws / total, 4) if total > 0 else 0,
        "by_diff": range_metrics,
        "by_league": league_metrics,
    }


def print_report(metrics):
    print(f"  Matches:    {metrics['n_matches']}")
    print(f"  Selected:   {metrics['n_selected']} ({metrics['coverage']*100:.1f}%)")
    print(f"  Accuracy:   {metrics['accuracy']*100:.1f}%")
    print(f"  Home wins:  {metrics['baseline_home']*100:.1f}% (baseline)")
    print(f"  Draw rate:  {metrics['draw_rate']*100:.1f}%")
    print(f"\n  --- By diff range ---")
    for label, v in metrics["by_diff"].items():
        print(f"    {label:>6}: {v['count']:>4} sel  {v['correct']:>4} corr  {v['accuracy']*100:5.1f}%")
    print(f"\n  --- By league ---")
    for code, v in metrics["by_league"].items():
        print(f"    {code}: {v['selected']:>4}/{v['total']:>4} ({v['coverage']*100:.1f}%)  acc: {v['accuracy']*100:.1f}%")
    print()
