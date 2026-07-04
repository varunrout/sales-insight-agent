from pathlib import Path
import ast

import pandas as pd

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


def test_lost_regions_revenue_impact_works():
    result = analyse_data("How much revenue can I get if LATAM and APAC are lost regions?")

    assert "Revenue impact of lost or excluded regions" in result
    assert "Total revenue:" in result
    assert "Excluded/lost regions:" in result
    assert "LATAM" in result
    assert "APAC" in result
    assert "Revenue lost / revenue at risk:" in result
    assert "Retained revenue:" in result
    assert "Percentage retained:" in result
    assert "Percentage lost:" in result


def test_revenue_excluding_regions_works():
    result = analyse_data("Revenue excluding LATAM and APAC")

    assert "Revenue impact of lost or excluded regions" in result
    assert "Excluded/lost regions:" in result
    assert "Revenue lost / revenue at risk:" in result
    assert "Retained revenue:" in result
    assert "I can answer structured sales questions" not in result


def test_revenue_at_risk_regions_works():
    result = analyse_data("How much revenue is at risk if LATAM and APAC are lost?")

    assert "Revenue impact of lost or excluded regions" in result
    assert "Revenue lost / revenue at risk:" in result
    assert "Percentage lost:" in result


def test_emea_q3_softness_analysis_works():
    result = analyse_data("Analyse EMEA Q3 softness")

    assert "EMEA Q3 softness analysis" in result
    assert "EMEA Q2 revenue:" in result
    assert "EMEA Q3 revenue:" in result
    assert "Absolute change:" in result
    assert "Percentage change:" in result
    assert "Channel-level breakdown:" in result
    assert "Partner" in result


def test_why_emea_was_soft_in_q3_works():
    result = analyse_data("Why was EMEA soft in Q3?")

    assert "EMEA Q3 softness analysis" in result
    assert "Q3 softness detected" in result
    assert "Partner" in result


def test_product_category_filter_does_not_cross_filter_customer_segment():
    data = analyse_module._load_sales_data(analyse_module.DATA_PATH)
    expected_rows = data[data["product_category"] == "Enterprise Suite"]

    result = analyse_data("What is total revenue by sales channel for Enterprise Suite?")

    assert "Total revenue by sales channel" in result
    assert f"Scope: {len(expected_rows):,} rows" in result
    assert set(expected_rows["customer_segment"].unique()) != {"Enterprise"}


def test_month_over_month_revenue_trend_works():
    result = analyse_data("Show the month-over-month revenue trend.")

    assert "Month-over-month revenue trend" in result
    assert "Recent months:" in result
    assert "MoM" in result


def test_emea_partner_q3_vs_q2_respects_year_filter():
    data = analyse_module._load_sales_data(analyse_module.DATA_PATH)
    expected = data[
        (data["date"].dt.year == 2025)
        & (data["region"] == "EMEA")
        & (data["sales_channel"] == "Partner")
        & (data["date"].dt.quarter.isin([2, 3]))
    ]
    q2_revenue = expected[expected["date"].dt.quarter == 2]["revenue"].sum()
    q3_revenue = expected[expected["date"].dt.quarter == 3]["revenue"].sum()

    result = analyse_data("Compare EMEA Partner Q3 vs Q2 in 2025")

    assert f"Q2 revenue: ${q2_revenue:,.2f}" in result
    assert f"Q3 revenue: ${q3_revenue:,.2f}" in result


def test_emea_partner_q3_vs_q2_handles_missing_quarter():
    data = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2025-04-01"),
                "region": "EMEA",
                "sales_channel": "Partner",
                "revenue": 100.0,
                "conversion_rate": 0.05,
                "gross_margin": 0.50,
            }
        ]
    )

    result = analyse_module._emea_partner_q3_vs_q2(data)

    assert "Q3 data is missing" in result


def test_emea_partner_q3_vs_q2_handles_zero_q2_revenue():
    data = pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2025-04-01"),
                "region": "EMEA",
                "sales_channel": "Partner",
                "revenue": 0.0,
                "conversion_rate": 0.04,
                "gross_margin": 0.50,
            },
            {
                "date": pd.Timestamp("2025-07-01"),
                "region": "EMEA",
                "sales_channel": "Partner",
                "revenue": 100.0,
                "conversion_rate": 0.03,
                "gross_margin": 0.45,
            },
        ]
    )

    result = analyse_module._emea_partner_q3_vs_q2(data)

    assert "Revenue change: n/a because Q2 revenue is zero" in result


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


def test_asks_revenue_by_returns_bool():
    result = analyse_module._asks_revenue_by("total revenue by region", "region")

    assert result is True
