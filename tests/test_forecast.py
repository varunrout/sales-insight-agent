from pathlib import Path
import ast

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


def test_missing_dataset_path_is_handled_cleanly(monkeypatch):
    monkeypatch.setattr(forecast_module, "DATA_PATH", Path("missing_sales_file.csv"))

    result = forecast_module.forecast("Forecast revenue for next 30 days.")

    assert "Sales dataset not found" in result
