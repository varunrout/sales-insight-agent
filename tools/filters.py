"""Shared query-to-dataframe filtering used by every analytics tool.

`analyse_data`, `visualise` and `forecast` must agree on scope for the same
question: if a query says "in EMEA" or "excluding LATAM", all three should
operate on the same rows. This module is the single place that turns a natural
-language query into a filtered dataframe, so the tools cannot drift apart.

Supported filters:
- year:      a four-digit 20xx in the query
- inclusive: any known value of product_category, region, sales_channel or
             customer_segment named in the query keeps only those rows
- exclusive: values after "excluding" / "except" / "without" / "exclude" are
             dropped instead
"""

from __future__ import annotations

import re

import pandas as pd

# Columns whose known values can be matched directly from the query text.
VALUE_COLUMNS = ("product_category", "region", "sales_channel", "customer_segment")

_EXCLUSION_SPLIT = re.compile(r"\b(?:excluding|except\s+for|except|without|exclude|excl)\b")


def _split_inclusion_exclusion(normalized_query: str) -> tuple[str, str]:
    parts = _EXCLUSION_SPLIT.split(normalized_query, maxsplit=1)
    inclusion_text = parts[0]
    exclusion_text = parts[1] if len(parts) > 1 else ""
    return inclusion_text, exclusion_text


def matching_values(data: pd.DataFrame, column: str, text: str) -> list[str]:
    if column not in data.columns:
        return []
    return [
        value
        for value in sorted(data[column].dropna().unique(), key=lambda item: -len(str(item)))
        if re.search(rf"\b{re.escape(str(value).lower())}\b", text)
    ]


def apply_filters(data: pd.DataFrame, query: str) -> pd.DataFrame:
    """Return the rows of ``data`` that match the scope described by ``query``."""
    filtered = data.copy()
    normalized_query = query.lower()
    inclusion_text, exclusion_text = _split_inclusion_exclusion(normalized_query)

    year_match = re.search(r"\b(20\d{2})\b", normalized_query)
    if year_match and "date" in filtered.columns:
        filtered = filtered[filtered["date"].dt.year == int(year_match.group(1))]

    # Inclusive filters. product_category is applied first, and the
    # customer_segment inclusive filter is skipped when a category matched, to
    # preserve the original analyse_data behaviour.
    matched_categories = matching_values(filtered, "product_category", inclusion_text)
    if matched_categories:
        filtered = filtered[filtered["product_category"].isin(matched_categories)]

    for column in ("region", "sales_channel", "customer_segment"):
        if column == "customer_segment" and matched_categories:
            continue
        matches = matching_values(filtered, column, inclusion_text)
        if matches:
            filtered = filtered[filtered[column].isin(matches)]

    # Exclusions: drop any named values that follow an exclusion keyword.
    if exclusion_text:
        for column in VALUE_COLUMNS:
            excluded = matching_values(filtered, column, exclusion_text)
            if excluded:
                filtered = filtered[~filtered[column].isin(excluded)]

    return filtered


def filter_note(data: pd.DataFrame) -> str:
    if data.empty or "date" not in data.columns:
        return f"Scope: {len(data):,} rows."
    start = data["date"].min().date()
    end = data["date"].max().date()
    return f"Scope: {len(data):,} rows from {start} to {end}."
