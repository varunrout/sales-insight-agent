"""Load the sales dataset, from SQLite or CSV depending on the path.

The default store is SQLite (``config.DATA_PATH`` -> ``data/sales.db``), built
from the seed CSV by ``scripts/build_data.py``. Reading is dispatched by file
extension so callers and tests can still point at a plain CSV (the tests use
temporary CSV fixtures).
"""

from pathlib import Path

import pandas as pd

_SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}


def read_sales_frame(data_path: Path) -> pd.DataFrame:
    """Read the raw sales frame from a SQLite DB or a CSV. Raises on failure."""
    if Path(data_path).suffix.lower() in _SQLITE_SUFFIXES:
        from db.loader import load_sales

        return load_sales(Path(data_path))
    return pd.read_csv(data_path)


def load_sales_data(
    data_path: Path,
    required_columns: set[str],
    numeric_columns: set[str],
) -> pd.DataFrame | str:
    if not Path(data_path).exists():
        return f"Sales dataset not found at {data_path}."

    try:
        data = read_sales_frame(data_path)
    except Exception as exc:
        return f"Sales dataset could not be loaded: {exc}"

    missing_columns = required_columns.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        return f"Sales dataset is missing required columns: {missing}."

    try:
        data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
        for column in numeric_columns:
            data[column] = pd.to_numeric(data[column], errors="raise")
    except Exception as exc:
        return f"Sales dataset failed validation: {exc}"

    return data
