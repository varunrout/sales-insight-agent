"""Evaluation harness for sales-insight-agent.

Reports three things with committed numbers:

1. Routing accuracy - deterministic planner routes vs the expected routes in
   ``data/sample_questions.json`` (exact-order and set match).
2. Forecast skill - model backtest MAE/RMSE vs a seasonal-naive (lag-7)
   baseline on the same holdout, plus 80% interval coverage, per metric.
3. Retrieval hit-rate - whether the embedding retriever surfaces a judged
   relevant source in the top-k, over ``data/retrieval_relevance.json``.

Run:  python -m eval.run_eval

Exits non-zero if routing accuracy or retrieval hit-rate fall below their
thresholds. It does NOT fail when the forecast model loses to the baseline;
that is a finding to report, not a build break.
"""

from __future__ import annotations

import json
from pathlib import Path

from agent.graph import plan_tool_calls
from config import QUESTIONS_PATH, ROOT_DIR
from rag.retriever import retrieve_documents
from tools.forecast import evaluate_metric

RELEVANCE_PATH = ROOT_DIR / "data" / "retrieval_relevance.json"

FORECAST_METRICS = ["revenue", "units_sold", "new_customers"]
RETRIEVAL_TOP_K = 3

ROUTING_SET_MATCH_THRESHOLD = 0.80
RETRIEVAL_HIT_RATE_THRESHOLD = 0.80


def evaluate_routing() -> dict[str, float]:
    questions = json.loads(Path(QUESTIONS_PATH).read_text(encoding="utf-8"))
    exact = 0
    set_match = 0
    misses: list[str] = []
    for item in questions:
        planned = plan_tool_calls(item["question"])
        expected = item["expected_tool_route"]
        if planned == expected:
            exact += 1
        if set(planned) == set(expected):
            set_match += 1
        else:
            misses.append(f"{item['id']}: expected {expected}, got {planned}")
    total = len(questions)
    return {
        "total": total,
        "exact": exact,
        "set_match": set_match,
        "exact_accuracy": exact / total,
        "set_accuracy": set_match / total,
        "misses": misses,
    }


def evaluate_retrieval() -> dict[str, float]:
    pairs = json.loads(RELEVANCE_PATH.read_text(encoding="utf-8"))
    hits = 0
    misses: list[str] = []
    for pair in pairs:
        results = retrieve_documents(pair["query"], top_k=RETRIEVAL_TOP_K)
        retrieved = {result.source for result in results}
        if retrieved & set(pair["relevant_sources"]):
            hits += 1
        else:
            misses.append(
                f"{pair['query']!r}: expected one of "
                f"{pair['relevant_sources']}, got {sorted(retrieved)}"
            )
    total = len(pairs)
    return {
        "total": total,
        "hits": hits,
        "hit_rate": hits / total,
        "misses": misses,
    }


def evaluate_forecast() -> dict[str, dict]:
    results: dict[str, dict] = {}
    for metric in FORECAST_METRICS:
        outcome = evaluate_metric(metric)
        if isinstance(outcome, str):
            results[metric] = {"error": outcome}
        else:
            results[metric] = outcome
    return results


def _print_routing(routing: dict) -> None:
    print("== Routing ==")
    print(
        f"  exact-order accuracy : {routing['exact']}/{routing['total']} "
        f"({routing['exact_accuracy']:.0%})"
    )
    print(
        f"  set-match accuracy   : {routing['set_match']}/{routing['total']} "
        f"({routing['set_accuracy']:.0%})"
    )
    for miss in routing["misses"]:
        print(f"  miss: {miss}")


def _print_forecast(forecast: dict) -> None:
    print("== Forecast (model vs seasonal-naive, same holdout) ==")
    header = (
        f"  {'metric':14s} {'model_MAE':>12s} {'seasonal_MAE':>13s} {'skill':>7s} {'cov80':>7s}"
    )
    print(header)
    for metric, row in forecast.items():
        if "error" in row:
            print(f"  {metric:14s} {row['error']}")
            continue
        verdict = "beats" if row["skill_vs_seasonal"] < 1 else "loses"
        print(
            f"  {metric:14s} {row['model_mae']:12.2f} {row['seasonal_naive_mae']:13.2f} "
            f"{row['skill_vs_seasonal']:6.2f}x {row['coverage_80']:6.0%}  [{verdict}]"
        )


def _print_retrieval(retrieval: dict) -> None:
    print(f"== Retrieval (hit-rate@{RETRIEVAL_TOP_K}) ==")
    print(f"  hit-rate : {retrieval['hits']}/{retrieval['total']} ({retrieval['hit_rate']:.0%})")
    for miss in retrieval["misses"]:
        print(f"  miss: {miss}")


def run() -> dict:
    routing = evaluate_routing()
    forecast = evaluate_forecast()
    retrieval = evaluate_retrieval()
    return {"routing": routing, "forecast": forecast, "retrieval": retrieval}


def main() -> int:
    report = run()
    _print_routing(report["routing"])
    print()
    _print_forecast(report["forecast"])
    print()
    _print_retrieval(report["retrieval"])
    print()

    failures = []
    if report["routing"]["set_accuracy"] < ROUTING_SET_MATCH_THRESHOLD:
        failures.append(
            f"routing set-match {report['routing']['set_accuracy']:.0%} "
            f"< {ROUTING_SET_MATCH_THRESHOLD:.0%}"
        )
    if report["retrieval"]["hit_rate"] < RETRIEVAL_HIT_RATE_THRESHOLD:
        failures.append(
            f"retrieval hit-rate {report['retrieval']['hit_rate']:.0%} "
            f"< {RETRIEVAL_HIT_RATE_THRESHOLD:.0%}"
        )

    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("PASS: routing and retrieval thresholds met.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
