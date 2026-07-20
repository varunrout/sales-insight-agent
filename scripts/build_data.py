"""Build the SQLite sales store from the seed CSV.

    python -m scripts.build_data

Writes ``config.DATA_PATH`` (data/sales.db), which is gitignored and rebuilt
deterministically from the committed seed at ``config.RAW_CSV_PATH``.
"""

from __future__ import annotations

from config import DATA_PATH
from db.loader import build_database


def main() -> None:
    rows = build_database()
    print(f"Built SQLite sales store at {DATA_PATH} with {rows} rows.")


if __name__ == "__main__":
    main()
