"""Every tool answer should end in a stated finding, not a bare table or path."""

from tools.analyse_data import analyse_data
from tools.forecast import forecast
from tools.search_documents import search_documents
from tools.visualise import visualise


def test_revenue_by_region_ends_in_a_finding():
    result = analyse_data("What is revenue by region?")

    assert "Finding:" in result
    assert result.strip().splitlines()[-1].startswith("Finding:")


def test_top_products_has_a_finding():
    assert "Finding:" in analyse_data("Top 3 products by revenue")


def test_average_margin_has_a_finding():
    assert "Finding:" in analyse_data("Average gross margin by sales channel")


def test_month_over_month_has_a_finding():
    assert "Finding:" in analyse_data("Month over month revenue")


def test_exclusion_impact_has_a_finding():
    assert "Finding:" in analyse_data("What revenue do we lose excluding LATAM and APAC?")


def test_forecast_has_a_finding():
    assert "Finding:" in forecast("Forecast revenue for the next 30 days.")


def test_search_documents_has_a_finding():
    assert "Finding:" in search_documents("EMEA Q3 softness")


def test_visualise_has_a_finding_and_still_reports_the_path():
    result = visualise("Show a chart of revenue by region")

    assert "Finding:" in result
    assert "chart saved to" in result
