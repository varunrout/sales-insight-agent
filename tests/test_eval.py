from eval.run_eval import (
    evaluate_forecast,
    evaluate_retrieval,
    evaluate_routing,
    run,
)


def test_evaluate_routing_scores_all_questions():
    routing = evaluate_routing()

    assert routing["total"] == 7
    assert 0.0 <= routing["exact_accuracy"] <= 1.0
    assert 0.0 <= routing["set_accuracy"] <= 1.0
    assert routing["set_match"] >= routing["exact"]


def test_evaluate_forecast_reports_baseline_and_coverage():
    forecast = evaluate_forecast()

    for metric in ("revenue", "units_sold", "new_customers"):
        row = forecast[metric]
        assert "error" not in row
        assert row["model_mae"] >= 0
        assert row["seasonal_naive_mae"] >= 0
        assert row["skill_vs_seasonal"] > 0
        assert 0.0 <= row["coverage_80"] <= 1.0


def test_evaluate_retrieval_meets_threshold():
    retrieval = evaluate_retrieval()

    assert retrieval["total"] >= 5
    assert retrieval["hit_rate"] >= 0.8


def test_run_returns_all_three_sections():
    report = run()

    assert set(report) == {"routing", "forecast", "retrieval"}
