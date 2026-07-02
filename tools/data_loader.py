from pathlib import Path

import pandas as pd


def load_sales_data(
    data_path: Path,
    required_columns: set[str],
    numeric_columns: set[str],
) -> pd.DataFrame | str:
    if not data_path.exists():
        return f"Sales dataset not found at {data_path}."

    try:
        data = pd.read_csv(data_path)
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
