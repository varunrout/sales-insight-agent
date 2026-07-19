import config
from tools.data_loader import load_sales_data
from tools.filters import apply_filters, filter_note, matching_values

_COLUMNS = {"date", "region", "sales_channel", "product_category", "customer_segment", "revenue"}
_NUMERIC = {"revenue"}


def _data():
    return load_sales_data(config.DATA_PATH, _COLUMNS, _NUMERIC)


def test_inclusive_region_filter_keeps_only_that_region():
    data = _data()
    scoped = apply_filters(data, "revenue by sales channel in EMEA")

    assert len(scoped) < len(data)
    assert set(scoped["region"].unique()) == {"EMEA"}


def test_exclusion_drops_named_region():
    data = _data()
    scoped = apply_filters(data, "revenue by region excluding LATAM")

    assert "LATAM" not in set(scoped["region"].unique())
    assert set(scoped["region"].unique()) == set(data["region"].unique()) - {"LATAM"}


def test_year_filter_restricts_to_year():
    data = _data()
    scoped = apply_filters(data, "revenue by region for 2025")

    assert set(scoped["date"].dt.year.unique()) == {2025}


def test_no_filter_returns_all_rows():
    data = _data()
    scoped = apply_filters(data, "revenue by region")

    assert len(scoped) == len(data)


def test_matching_values_finds_known_value():
    data = _data()

    assert matching_values(data, "region", "performance in emea this year") == ["EMEA"]
    assert matching_values(data, "region", "nothing named here") == []


def test_filter_note_reports_row_count():
    data = _data()

    assert f"{len(data):,} rows" in filter_note(data)
