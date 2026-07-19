import ast
from pathlib import Path

import pandas as pd

from tools import forecast as forecast_module
from tools.forecast import forecast


def test_forecast_imports_successfully():
    assert callable(forecast)


def test_revenue_forecast_works():
    result = forecast("Forecast revenue for next 30 days.")

    assert "Forecast for revenue" in result
    assert "Horizon: 30 days" in result
    assert "Future forecast rows:" in result


def test_units_sold_forecast_works():
    result = forecast("Forecast units_sold for next 4 weeks.")

    assert "Forecast for units sold" in result
    assert "Horizon: 28 days" in result


def test_new_customers_forecast_works():
    result = forecast("Forecast new_customers for next month.")

    assert "Forecast for new customers" in result
    assert "Horizon: 30 days" in result


def test_next_4_weeks_is_parsed_correctly():
    result = forecast("Forecast revenue for next 4 weeks.")

    assert "Horizon: 28 days" in result
    assert "Output frequency: weekly" in result


def test_next_30_days_is_parsed_correctly():
    result = forecast("Forecast revenue for next 30 days.")

    assert "Horizon: 30 days" in result
    assert "Output frequency: daily" in result


def test_next_4_weeks_returns_four_forecast_week_rows():
    result = forecast("Forecast revenue for next 4 weeks.")
    weekly_rows = [
        line for line in result.splitlines() if line.startswith("- Week ") and "starting" in line
    ]

    assert len(weekly_rows) == 4
    assert weekly_rows[0].startswith("- Week 1 starting 2026-01-01:")


def test_weekly_frequency_is_not_overridden_by_monday_substring():
    frequency = forecast_module._parse_output_frequency(
        "Forecast revenue for next 4 weeks starting Monday."
    )

    assert frequency == "weekly"


def test_weekday_substring_does_not_force_daily_frequency():
    frequency = forecast_module._parse_output_frequency("Forecast revenue weekly for weekdays.")

    assert frequency == "weekly"


def test_weekly_format_uses_consecutive_forecast_windows():
    future = pd.DataFrame(
        {
            "date": pd.date_range("2026-01-01", periods=28, freq="D"),
            "p10": [1.0] * 28,
            "p50": [2.0] * 28,
            "p90": [3.0] * 28,
        }
    )

    result = forecast_module._format_future_rows(future, "revenue", "weekly")
    weekly_rows = [line for line in result.splitlines() if line.startswith("- Week ")]

    assert len(weekly_rows) == 4
    assert weekly_rows[0].startswith("- Week 1 starting 2026-01-01:")
    assert weekly_rows[1].startswith("- Week 2 starting 2026-01-08:")


def test_unsupported_metric_returns_graceful_message():
    result = forecast("Forecast discount rate for next 30 days.")

    assert "I can forecast revenue, units_sold or new_customers" in result


def test_forecast_output_includes_future_periods():
    result = forecast("Forecast revenue for next 30 days.")

    assert "2026-01-01" in result
    assert "P10=" in result
    assert "P50=" in result
    assert "P90=" in result


def test_forecast_output_includes_backtest_metrics():
    result = forecast("Forecast revenue for next 30 days.")

    assert "Backtest MAE:" in result
    assert "Backtest RMSE:" in result


def test_forecast_does_not_use_eval_or_exec():
    source = Path(forecast_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec"}


def test_build_model_does_not_catch_all_exceptions():
    source = Path(forecast_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            assert node.type is not None
            if isinstance(node.type, ast.Name):
                assert node.type.id != "Exception"


def test_missing_dataset_path_is_handled_cleanly(monkeypatch):
    monkeypatch.setattr(forecast_module, "DATA_PATH", Path("missing_sales_file.csv"))

    result = forecast_module.forecast("Forecast revenue for next 30 days.")

    assert "Sales dataset not found" in result


def test_forecast_output_includes_seasonal_baseline_and_coverage():
    result = forecast("Forecast revenue for the next 30 days.")

    assert "Seasonal-naive (lag-7) MAE:" in result
    assert "Skill vs seasonal-naive:" in result
    assert "80% interval coverage:" in result


def test_evaluate_metric_returns_baseline_and_coverage():
    from tools.forecast import evaluate_metric

    outcome = evaluate_metric("revenue")

    assert isinstance(outcome, dict)
    assert outcome["model_mae"] >= 0
    assert outcome["seasonal_naive_mae"] >= 0
    assert outcome["naive_mae"] >= 0
    assert outcome["skill_vs_seasonal"] > 0
    assert 0.0 <= outcome["coverage_80"] <= 1.0
    assert outcome["n_test"] > 0


def test_evaluate_metric_rejects_unsupported_metric():
    from tools.forecast import evaluate_metric

    outcome = evaluate_metric("profit")

    assert isinstance(outcome, str)
    assert "I can forecast" in outcome


def test_forecast_respects_region_filter_scope():
    from tools.analyse_data import _apply_filters, _load_sales_data

    query = "Forecast revenue for the next 30 days in EMEA"
    data = _load_sales_data(__import__("config").DATA_PATH)
    scoped_rows = len(_apply_filters(data, query))

    result = forecast(query)

    assert "Forecast for revenue" in result
    assert f"Scope: {scoped_rows:,} rows" in result


def test_forecast_global_query_has_no_scope_note():
    result = forecast("Forecast revenue for the next 30 days.")

    assert "Forecast for revenue" in result
    assert "Scope:" not in result
