import re
from pathlib import Path
from typing import Iterable

import pandas as pd

import config


TOOL_NAME = "analyse_data"
DATA_PATH = config.DATA_PATH

REQUIRED_COLUMNS = {
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
}

NUMERIC_COLUMNS = {
    "revenue",
    "units_sold",
    "new_customers",
    "discount_rate",
    "gross_margin",
    "order_count",
    "marketing_spend",
    "conversion_rate",
}

FILTER_COLUMNS = {
    "region": "region",
    "sales_channel": "sales_channel",
    "product_category": "product_category",
    "customer_segment": "customer_segment",
}

UNSUPPORTED_MESSAGE = (
    "I can answer structured sales questions about revenue by region, product "
    "category or sales channel; average gross margin by channel; top products; "
    "month-over-month revenue trend; and EMEA Partner Q3 vs Q2."
)


def analyse_data(query: str) -> str:
    data = _load_sales_data(DATA_PATH)
    if isinstance(data, str):
        return data

    filtered = _apply_filters(data, query)
    normalized_query = query.lower()

    if _is_emea_partner_q3_vs_q2(normalized_query):
        return _emea_partner_q3_vs_q2(data)
    if _asks_month_over_month(normalized_query):
        return _month_over_month_revenue(filtered)
    if _asks_average_margin_by_channel(normalized_query):
        return _average_gross_margin_by_channel(filtered)
    if _asks_top_products_by_units(normalized_query):
        return _top_products(filtered, "units_sold", query)
    if _asks_top_products_by_revenue(normalized_query):
        return _top_products(filtered, "revenue", query)
    if _asks_revenue_by(normalized_query, "region"):
        return _total_revenue_by(filtered, "region")
    if _asks_revenue_by(normalized_query, "product category"):
        return _total_revenue_by(filtered, "product_category")
    if _asks_revenue_by(normalized_query, "sales channel") or _asks_revenue_by(
        normalized_query, "channel"
    ):
        return _total_revenue_by(filtered, "sales_channel")

    return UNSUPPORTED_MESSAGE


def _load_sales_data(data_path: Path) -> pd.DataFrame | str:
    if not data_path.exists():
        return f"Sales dataset not found at {data_path}."

    try:
        data = pd.read_csv(data_path)
    except Exception as exc:
        return f"Sales dataset could not be loaded: {exc}"

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        return f"Sales dataset is missing required columns: {missing}."

    try:
        data["date"] = pd.to_datetime(data["date"], format="%Y-%m-%d", errors="raise")
        for column in NUMERIC_COLUMNS:
            data[column] = pd.to_numeric(data[column], errors="raise")
    except Exception as exc:
        return f"Sales dataset failed validation: {exc}"

    return data


def _apply_filters(data: pd.DataFrame, query: str) -> pd.DataFrame:
    filtered = data.copy()
    normalized_query = query.lower()

    year_match = re.search(r"\b(20\d{2})\b", normalized_query)
    if year_match:
        filtered = filtered[filtered["date"].dt.year == int(year_match.group(1))]

    for column in FILTER_COLUMNS.values():
        filtered = _filter_by_known_values(filtered, column, normalized_query)

    return filtered


def _filter_by_known_values(
    data: pd.DataFrame, column: str, normalized_query: str
) -> pd.DataFrame:
    matches = [
        value
        for value in sorted(data[column].dropna().unique(), key=lambda item: -len(str(item)))
        if re.search(rf"\b{re.escape(str(value).lower())}\b", normalized_query)
    ]
    if not matches:
        return data
    return data[data[column].isin(matches)]


def _asks_revenue_by(normalized_query: str, dimension: str) -> bool:
    return "revenue" in normalized_query and re.search(
        rf"\bby\s+{re.escape(dimension)}\b", normalized_query
    )


def _asks_average_margin_by_channel(normalized_query: str) -> bool:
    return (
        "gross margin" in normalized_query
        and ("average" in normalized_query or "avg" in normalized_query)
        and ("channel" in normalized_query or "sales channel" in normalized_query)
    )


def _asks_top_products_by_revenue(normalized_query: str) -> bool:
    return (
        "top" in normalized_query
        and "product" in normalized_query
        and "revenue" in normalized_query
    )


def _asks_top_products_by_units(normalized_query: str) -> bool:
    return (
        "top" in normalized_query
        and "product" in normalized_query
        and ("units" in normalized_query or "volume" in normalized_query)
    )


def _asks_month_over_month(normalized_query: str) -> bool:
    return (
        "month-over-month" in normalized_query
        or "month over month" in normalized_query
        or "mom" in normalized_query
    ) and "revenue" in normalized_query


def _is_emea_partner_q3_vs_q2(normalized_query: str) -> bool:
    return all(term in normalized_query for term in ["emea", "partner", "q3", "q2"])


def _parse_top_n(query: str, default: int = 5) -> int:
    match = re.search(r"\btop\s+(\d{1,2})\b", query.lower())
    if not match:
        return default
    return max(1, min(int(match.group(1)), 20))


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _filter_note(data: pd.DataFrame) -> str:
    start = data["date"].min().date()
    end = data["date"].max().date()
    return f"Scope: {len(data):,} rows from {start} to {end}."


def _format_ranked_rows(
    title: str, rows: Iterable[tuple[str, float]], formatter
) -> str:
    lines = [title]
    for rank, (label, value) in enumerate(rows, start=1):
        lines.append(f"{rank}. {label}: {formatter(value)}")
    return "\n".join(lines)


def _total_revenue_by(data: pd.DataFrame, dimension: str) -> str:
    if data.empty:
        return "No sales records matched the requested filters."

    grouped = (
        data.groupby(dimension, as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    label = dimension.replace("_", " ")
    rows = list(grouped[[dimension, "revenue"]].itertuples(index=False, name=None))
    return "\n".join(
        [
            f"Total revenue by {label}",
            _filter_note(data),
            _format_ranked_rows("Results:", rows, _format_money),
        ]
    )


def _average_gross_margin_by_channel(data: pd.DataFrame) -> str:
    if data.empty:
        return "No sales records matched the requested filters."

    grouped = (
        data.groupby("sales_channel", as_index=False)["gross_margin"]
        .mean()
        .sort_values("gross_margin", ascending=False)
    )
    strongest = grouped.iloc[0]
    rows = list(
        grouped[["sales_channel", "gross_margin"]].itertuples(index=False, name=None)
    )
    return "\n".join(
        [
            "Average gross margin by sales channel",
            _filter_note(data),
            f"Strongest channel: {strongest['sales_channel']} at {_format_percent(strongest['gross_margin'])}.",
            _format_ranked_rows("Results:", rows, _format_percent),
        ]
    )


def _top_products(data: pd.DataFrame, metric: str, query: str) -> str:
    if data.empty:
        return "No sales records matched the requested filters."

    top_n = _parse_top_n(query)
    grouped = (
        data.groupby("product_name", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
        .head(top_n)
    )
    formatter = _format_money if metric == "revenue" else lambda value: f"{value:,.0f}"
    metric_label = metric.replace("_", " ")
    rows = list(grouped[["product_name", metric]].itertuples(index=False, name=None))
    return "\n".join(
        [
            f"Top {top_n} products by {metric_label}",
            _filter_note(data),
            _format_ranked_rows("Results:", rows, formatter),
        ]
    )


def _month_over_month_revenue(data: pd.DataFrame) -> str:
    if data.empty:
        return "No sales records matched the requested filters."

    monthly = (
        data.assign(month=data["date"].dt.to_period("M").astype(str))
        .groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    monthly["mom_change"] = monthly["revenue"].pct_change()
    recent = monthly.tail(6)

    lines = ["Month-over-month revenue trend", _filter_note(data), "Recent months:"]
    for row in recent.itertuples(index=False):
        change = "n/a" if pd.isna(row.mom_change) else _format_percent(row.mom_change)
        lines.append(f"- {row.month}: {_format_money(row.revenue)} ({change} MoM)")
    return "\n".join(lines)


def _emea_partner_q3_vs_q2(data: pd.DataFrame) -> str:
    scoped = data[
        (data["region"] == "EMEA")
        & (data["sales_channel"] == "Partner")
        & (data["date"].dt.quarter.isin([2, 3]))
    ].copy()
    if scoped.empty:
        return "No EMEA Partner Q2 or Q3 records were found."

    scoped["quarter"] = "Q" + scoped["date"].dt.quarter.astype(str)
    comparison = scoped.groupby("quarter", as_index=False).agg(
        revenue=("revenue", "sum"),
        conversion_rate=("conversion_rate", "mean"),
        gross_margin=("gross_margin", "mean"),
    )
    values = comparison.set_index("quarter")
    q2_revenue = values.loc["Q2", "revenue"]
    q3_revenue = values.loc["Q3", "revenue"]
    q2_conversion = values.loc["Q2", "conversion_rate"]
    q3_conversion = values.loc["Q3", "conversion_rate"]
    revenue_change = (q3_revenue - q2_revenue) / q2_revenue
    conversion_change = q3_conversion - q2_conversion
    softness = "Q3 softness detected" if q3_revenue < q2_revenue else "No Q3 revenue softness detected"

    return "\n".join(
        [
            "EMEA Partner Q3 vs Q2 comparison",
            softness,
            f"Q2 revenue: {_format_money(q2_revenue)}",
            f"Q3 revenue: {_format_money(q3_revenue)}",
            f"Revenue change: {_format_percent(revenue_change)}",
            f"Q2 conversion rate: {_format_percent(q2_conversion)}",
            f"Q3 conversion rate: {_format_percent(q3_conversion)}",
            f"Conversion rate change: {conversion_change:.2%} points",
        ]
    )
