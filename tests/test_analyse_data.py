from pathlib import Path
import ast

from tools import analyse_data as analyse_module
from tools.analyse_data import analyse_data


def test_analyse_data_imports():
    assert callable(analyse_data)


def test_total_revenue_by_region_works():
    result = analyse_data("What is total revenue by region?")

    assert "Total revenue by region" in result
    assert "North America" in result
    assert "$" in result


def test_north_america_ranks_highest_for_revenue_by_region():
    result = analyse_data("What is total revenue by region?")
    result_lines = result.splitlines()

    assert any(line.startswith("1. North America:") for line in result_lines)


def test_emea_partner_q3_vs_q2_returns_q3_softness():
    result = analyse_data(
        "How did EMEA Partner revenue and conversion rate perform in Q3 vs Q2?"
    )

    assert "EMEA Partner Q3 vs Q2 comparison" in result
    assert "Q3 softness detected" in result
    assert "Q2 revenue" in result
    assert "Q3 revenue" in result


def test_average_gross_margin_by_channel_shows_direct_strongest():
    result = analyse_data("What is the average gross margin by sales channel?")

    assert "Average gross margin by sales channel" in result
    assert "Strongest channel: Direct" in result
    assert "1. Direct:" in result


def test_top_products_by_revenue_works():
    result = analyse_data("Show me the top 3 products by revenue.")

    assert "Top 3 products by revenue" in result
    ranked_rows = [line for line in result.splitlines() if line[:1].isdigit()]
    assert len(ranked_rows) == 3


def test_top_products_by_units_works():
    result = analyse_data("Show me the top 4 products by units_sold.")

    assert "Top 4 products by units sold" in result
    ranked_rows = [line for line in result.splitlines() if line[:1].isdigit()]
    assert len(ranked_rows) == 4


def test_filtering_by_year_and_region_is_applied():
    result = analyse_data("What is total revenue by sales channel in APAC for 2025?")

    assert "Total revenue by sales channel" in result
    assert "2025-01-01" in result
    assert "2025-12-31" in result


def test_month_over_month_revenue_trend_works():
    result = analyse_data("Show the month-over-month revenue trend.")

    assert "Month-over-month revenue trend" in result
    assert "Recent months:" in result
    assert "MoM" in result


def test_unsupported_query_returns_graceful_message():
    result = analyse_data("Which salesperson has the best onboarding score?")

    assert "I can answer structured sales questions" in result


def test_missing_dataset_path_is_handled_cleanly(monkeypatch):
    monkeypatch.setattr(analyse_module, "DATA_PATH", Path("missing_sales_file.csv"))

    result = analyse_module.analyse_data("What is total revenue by region?")

    assert "Sales dataset not found" in result


def test_analyse_data_does_not_use_eval_or_exec():
    source = Path(analyse_module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec"}
