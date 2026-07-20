import config
from db.loader import build_database, get_connection, load_sales
from tools.data_loader import load_sales_data

_REQUIRED = {"date", "region", "revenue", "units_sold", "new_customers"}
_NUMERIC = {"revenue", "units_sold", "new_customers"}


def test_build_database_creates_store(tmp_path):
    db_path = tmp_path / "sales.db"
    rows = build_database(config.RAW_CSV_PATH, db_path)

    assert db_path.exists()
    assert rows > 0


def test_build_database_is_deterministic(tmp_path):
    first = build_database(config.RAW_CSV_PATH, tmp_path / "a.db")
    second = build_database(config.RAW_CSV_PATH, tmp_path / "b.db")

    assert first == second


def test_sales_table_has_indexes(tmp_path):
    db_path = tmp_path / "sales.db"
    build_database(config.RAW_CSV_PATH, db_path)

    with get_connection(db_path) as connection:
        names = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type='index'")
        }

    assert any("date" in name for name in names)


def test_load_sales_returns_expected_columns(tmp_path):
    db_path = tmp_path / "sales.db"
    build_database(config.RAW_CSV_PATH, db_path)

    frame = load_sales(db_path)

    assert _REQUIRED.issubset(frame.columns)
    assert len(frame) > 0


def test_load_sales_data_reads_from_sqlite(tmp_path):
    db_path = tmp_path / "sales.db"
    build_database(config.RAW_CSV_PATH, db_path)

    result = load_sales_data(db_path, _REQUIRED, _NUMERIC)

    assert not isinstance(result, str)
    assert "date" in result.columns
    assert str(result["date"].dtype).startswith("datetime")


def test_load_sales_data_missing_db_returns_message(tmp_path):
    result = load_sales_data(tmp_path / "nope.db", _REQUIRED, _NUMERIC)

    assert isinstance(result, str)
    assert "not found" in result
