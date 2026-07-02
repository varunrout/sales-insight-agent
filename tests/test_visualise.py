from pathlib import Path
import ast

from tools import visualise as visualise_module
from tools.visualise import visualise


TEST_CHART_OUTPUT_PATH = Path("outputs") / "test_charts"


def _use_test_chart_output(monkeypatch) -> Path:
    monkeypatch.setattr(visualise_module, "CHART_OUTPUT_PATH", TEST_CHART_OUTPUT_PATH)
    return TEST_CHART_OUTPUT_PATH


def _chart_path_from_response(response: str) -> Path:
    return Path(response.rsplit(" saved to ", maxsplit=1)[1])


def test_visualise_imports_successfully():
    assert callable(visualise)


def test_revenue_by_region_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Show me a bar chart of revenue by region.")
    chart_path = _chart_path_from_response(response)

    assert "Revenue by region chart saved to" in response
    assert chart_path.exists()
    assert chart_path.suffix == ".html"


def test_monthly_revenue_line_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Show a line chart of monthly revenue.")
    chart_path = _chart_path_from_response(response)

    assert "Monthly revenue chart saved to" in response
    assert chart_path.exists()
    assert chart_path.name == "monthly_revenue.html"


def test_average_gross_margin_by_channel_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Chart average gross margin by sales channel.")
    chart_path = _chart_path_from_response(response)

    assert "Average gross margin by sales channel chart saved to" in response
    assert chart_path.exists()
    assert chart_path.suffix == ".html"


def test_top_products_by_revenue_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Show the top 3 products by revenue.")
    chart_path = _chart_path_from_response(response)

    assert "Top 3 products by revenue chart saved to" in response
    assert chart_path.exists()
    assert chart_path.name == "top_3_products_by_revenue.html"


def test_month_over_month_revenue_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Plot month-over-month revenue.")
    chart_path = _chart_path_from_response(response)

    assert "Month-over-month revenue chart saved to" in response
    assert chart_path.exists()
    assert chart_path.name == "month_over_month_revenue.html"


def test_top_products_by_units_chart_is_created(monkeypatch):
    _use_test_chart_output(monkeypatch)

    response = visualise("Show top 4 products by units_sold.")
    chart_path = _chart_path_from_response(response)

    assert "Top 4 products by units sold chart saved to" in response
    assert chart_path.exists()
    assert chart_path.name == "top_4_products_by_units_sold.html"


def test_unsupported_chart_request_returns_graceful_message():
    response = visualise("Create a heatmap of salesperson onboarding scores.")

    assert "I can create charts for revenue" in response


def test_missing_dataset_path_is_handled_cleanly(monkeypatch):
    monkeypatch.setattr(visualise_module, "DATA_PATH", Path("missing.csv"))

    response = visualise_module.visualise("Show me revenue by region.")

    assert "Sales dataset not found" in response


def test_visualise_does_not_use_eval_or_exec():
    source = Path(visualise_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec"}
