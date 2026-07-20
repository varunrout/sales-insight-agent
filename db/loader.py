"""SQLite sales store.

The queryable store for the structured tools is a SQLite database with a typed
``sales`` table, built from the committed synthetic seed CSV
(``config.RAW_CSV_PATH``). The database itself (``config.DATA_PATH``) is a
derived artefact and is gitignored; rebuild it deterministically with
``python -m scripts.build_data``.

There is no separate documents table: document retrieval is handled by the
Chroma vector store (see ``rag/``), which embeds the markdown in ``data/docs``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from config import DATA_PATH, RAW_CSV_PATH

TABLE_NAME = "sales"

# Explicit schema so the store is intentional rather than type-inferred.
SALES_SCHEMA = """
CREATE TABLE sales (
    id               INTEGER PRIMARY KEY,
    date             TEXT    NOT NULL,
    region           TEXT    NOT NULL,
    country          TEXT    NOT NULL,
    product_category TEXT    NOT NULL,
    product_name     TEXT    NOT NULL,
    sales_channel    TEXT    NOT NULL,
    customer_segment TEXT    NOT NULL,
    revenue          REAL    NOT NULL,
    units_sold       INTEGER NOT NULL,
    new_customers    INTEGER NOT NULL,
    discount_rate    REAL    NOT NULL,
    gross_margin     REAL    NOT NULL,
    order_count      INTEGER NOT NULL,
    marketing_spend  REAL    NOT NULL,
    conversion_rate  REAL    NOT NULL,
    campaign_flag    INTEGER NOT NULL,
    is_promo_period  INTEGER NOT NULL
);
"""

_INDEXES = (
    "CREATE INDEX idx_sales_date ON sales(date);",
    "CREATE INDEX idx_sales_region ON sales(region);",
    "CREATE INDEX idx_sales_category ON sales(product_category);",
)

_SCHEMA_COLUMNS = (
    "date",
    "region",
    "country",
    "product_category",
    "product_name",
    "sales_channel",
    "customer_segment",
    "revenue",
    "units_sold",
    "new_customers",
    "discount_rate",
    "gross_margin",
    "order_count",
    "marketing_spend",
    "conversion_rate",
    "campaign_flag",
    "is_promo_period",
)


def get_connection(db_path: Path = DATA_PATH) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path))


def build_database(csv_path: Path = RAW_CSV_PATH, db_path: Path = DATA_PATH) -> int:
    """Build the SQLite store from the seed CSV. Returns the row count."""
    frame = pd.read_csv(csv_path)
    missing = set(_SCHEMA_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Seed CSV is missing columns: {', '.join(sorted(missing))}")

    frame = frame[list(_SCHEMA_COLUMNS)].copy()
    frame["date"] = pd.to_datetime(frame["date"]).dt.strftime("%Y-%m-%d")
    for boolean_column in ("campaign_flag", "is_promo_period"):
        frame[boolean_column] = frame[boolean_column].astype(int)

    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    if Path(db_path).exists():
        Path(db_path).unlink()

    with get_connection(db_path) as connection:
        connection.execute(SALES_SCHEMA)
        for statement in _INDEXES:
            connection.execute(statement)
        frame.to_sql(TABLE_NAME, connection, if_exists="append", index=False)
        connection.commit()
    return len(frame)


def load_sales(db_path: Path = DATA_PATH) -> pd.DataFrame:
    """Load the full sales table as a DataFrame."""
    with get_connection(db_path) as connection:
        return pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", connection)
