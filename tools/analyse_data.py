import re
from collections.abc import Iterable
from pathlib import Path

import pandas as pd

import config
from tools.data_loader import load_sales_data

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

    normalized_query = query.lower()

    if _asks_lost_or_excluded_region_revenue(normalized_query):
        return _lost_or_excluded_region_revenue(data, query)

    filtered = _apply_filters(data, query)

    if _is_emea_partner_q3_vs_q2(normalized_query):
        return _emea_partner_q3_vs_q2(filtered)
    if _asks_emea_q3_softness(normalized_query):
        return _emea_q3_softness(filtered)
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
    return load_sales_data(data_path, REQUIRED_COLUMNS, NUMERIC_COLUMNS)


def _apply_filters(data: pd.DataFrame, query: str) -> pd.DataFrame:
    filtered = data.copy()
    normalized_query = query.lower()

    year_match = re.search(r"\b(20\d{2})\b", normalized_query)
    if year_match:
        filtered = filtered[filtered["date"].dt.year == int(year_match.group(1))]

    matched_product_categories = _matching_values(filtered, "product_category", normalized_query)
    if matched_product_categories:
        filtered = filtered[filtered["product_category"].isin(matched_product_categories)]

    for column in ("region", "sales_channel", "customer_segment"):
        if column == "customer_segment" and matched_product_categories:
            continue
        filtered = _filter_by_known_values(filtered, column, normalized_query)

    return filtered


def _matching_values(data: pd.DataFrame, column: str, normalized_query: str) -> list[str]:
    return [
        value
        for value in sorted(data[column].dropna().unique(), key=lambda item: -len(str(item)))
        if re.search(rf"\b{re.escape(str(value).lower())}\b", normalized_query)
    ]


def _filter_by_known_values(data: pd.DataFrame, column: str, normalized_query: str) -> pd.DataFrame:
    matches = _matching_values(data, column, normalized_query)
    if not matches:
        return data
    return data[data[column].isin(matches)]


def _regions_in_query(data: pd.DataFrame, query: str) -> list[str]:
    normalized_query = query.lower()
    return _matching_values(data, "region", normalized_query)


def _asks_lost_or_excluded_region_revenue(normalized_query: str) -> bool:
    has_revenue_context = "revenue" in normalized_query or "sales" in normalized_query
    has_exclusion_context = any(
        phrase in normalized_query
        for phrase in (
            "lost region",
            "lost regions",
            "lose ",
            "lost",
            "excluding",
            "exclude",
            "without",
            "at risk",
        )
    )
    return has_revenue_context and has_exclusion_context


def _asks_revenue_by(normalized_query: str, dimension: str) -> bool:
    return "revenue" in normalized_query and bool(
        re.search(rf"\bby\s+{re.escape(dimension)}\b", normalized_query)
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


def _asks_emea_q3_softness(normalized_query: str) -> bool:
    if "emea" not in normalized_query or "q3" not in normalized_query:
        return False
    return any(
        term in normalized_query
        for term in (
            "soft",
            "softness",
            "performance",
            "what happened",
            "why",
            "q3 vs q2",
            "vs q2",
            "q2 revenue",
        )
    )


def _parse_top_n(query: str, default: int = 5) -> int:
    match = re.search(r"\btop\s+(\d{1,2})\b", query.lower())
    if not match:
        return default
    return max(1, min(int(match.group(1)), 20))


def _format_money(value: float) -> str:
    return f"${value:,.2f}"


def _format_percent(value: float) -> str:
    return f"{value:.1%}"


def _format_signed_money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def _filter_note(data: pd.DataFrame) -> str:
    start = data["date"].min().date()
    end = data["date"].max().date()
    return f"Scope: {len(data):,} rows from {start} to {end}."


def _format_ranked_rows(title: str, rows: Iterable[tuple[str, float]], formatter) -> str:
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


def _lost_or_excluded_region_revenue(data: pd.DataFrame, query: str) -> str:
    if data.empty:
        return "No sales records matched the requested filters."

    regions = _regions_in_query(data, query)
    if not regions:
        return "No excluded or lost regions were found in the question."

    total_revenue = data["revenue"].sum()
    excluded_revenue = data[data["region"].isin(regions)]["revenue"].sum()
    retained_revenue = total_revenue - excluded_revenue
    percent_lost = 0 if total_revenue == 0 else excluded_revenue / total_revenue
    percent_retained = 0 if total_revenue == 0 else retained_revenue / total_revenue
    region_breakdown = (
        data[data["region"].isin(regions)]
        .groupby("region", as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    rows = list(region_breakdown[["region", "revenue"]].itertuples(index=False, name=None))

    return "\n".join(
        [
            "Revenue impact of lost or excluded regions",
            _filter_note(data),
            f"Total revenue: {_format_money(total_revenue)}",
            f"Excluded/lost regions: {', '.join(regions)}",
            f"Revenue lost / revenue at risk: {_format_money(excluded_revenue)}",
            f"Retained revenue: {_format_money(retained_revenue)}",
            f"Percentage retained: {_format_percent(percent_retained)}",
            f"Percentage lost: {_format_percent(percent_lost)}",
            _format_ranked_rows("Excluded region revenue:", rows, _format_money),
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
    rows = list(grouped[["sales_channel", "gross_margin"]].itertuples(index=False, name=None))
    return "\n".join(
        [
            "Average gross margin by sales channel",
            _filter_note(data),
            f"Strongest channel: {strongest['sales_channel']} at "
            f"{_format_percent(strongest['gross_margin'])}.",
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


def _emea_q3_softness(data: pd.DataFrame) -> str:
    scoped = data[(data["region"] == "EMEA") & (data["date"].dt.quarter.isin([2, 3]))].copy()
    if scoped.empty:
        return "No EMEA Q2 or Q3 records were found."

    scoped["quarter"] = "Q" + scoped["date"].dt.quarter.astype(str)
    available_quarters = set(scoped["quarter"].unique())
    missing_quarters = {"Q2", "Q3"}.difference(available_quarters)
    if missing_quarters:
        missing = ", ".join(sorted(missing_quarters))
        return f"Cannot compare EMEA Q3 vs Q2 because {missing} data is missing."

    quarterly = scoped.groupby("quarter", as_index=False)["revenue"].sum()
    values = quarterly.set_index("quarter")
    q2_revenue = values.loc["Q2", "revenue"]
    q3_revenue = values.loc["Q3", "revenue"]
    absolute_change = q3_revenue - q2_revenue
    percent_change = None if q2_revenue == 0 else absolute_change / q2_revenue
    percent_change_text = (
        "n/a because Q2 revenue is zero"
        if percent_change is None
        else _format_percent(percent_change)
    )

    channel = (
        scoped.groupby(["sales_channel", "quarter"], as_index=False)["revenue"]
        .sum()
        .pivot(index="sales_channel", columns="quarter", values="revenue")
        .fillna(0)
    )
    channel["absolute_change"] = channel["Q3"] - channel["Q2"]
    channel["percentage_change"] = channel.apply(
        lambda row: None if row["Q2"] == 0 else row["absolute_change"] / row["Q2"],
        axis=1,
    )
    channel = channel.sort_values("absolute_change")
    contributor = channel.iloc[0]
    contributor_name = str(contributor.name)
    contributor_text = (
        f"{contributor_name} was the largest negative channel contributor."
        if contributor["absolute_change"] < 0
        else "No channel posted a negative Q3 revenue change."
    )
    if contributor_name == "Partner" and contributor["absolute_change"] < 0:
        contributor_text = "Partner was the largest negative channel contributor."

    lines = [
        "EMEA Q3 softness analysis",
        "Q3 softness detected" if q3_revenue < q2_revenue else "No Q3 revenue softness detected",
        f"EMEA Q2 revenue: {_format_money(q2_revenue)}",
        f"EMEA Q3 revenue: {_format_money(q3_revenue)}",
        f"Absolute change: {_format_signed_money(absolute_change)}",
        f"Percentage change: {percent_change_text}",
        "Channel-level breakdown:",
    ]
    for channel_name, row in channel.iterrows():
        pct_text = (
            "n/a"
            if pd.isna(row["percentage_change"])
            else _format_percent(row["percentage_change"])
        )
        lines.append(
            f"- {channel_name}: Q2 {_format_money(row['Q2'])}, "
            f"Q3 {_format_money(row['Q3'])}, "
            f"change {_format_signed_money(row['absolute_change'])} ({pct_text})"
        )
    lines.append(contributor_text)
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
    available_quarters = set(scoped["quarter"].unique())
    missing_quarters = {"Q2", "Q3"}.difference(available_quarters)
    if missing_quarters:
        missing = ", ".join(sorted(missing_quarters))
        return f"Cannot compare EMEA Partner Q3 vs Q2 because {missing} data is missing."

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
    revenue_change = None if q2_revenue == 0 else (q3_revenue - q2_revenue) / q2_revenue
    conversion_change = q3_conversion - q2_conversion
    softness = (
        "Q3 softness detected" if q3_revenue < q2_revenue else "No Q3 revenue softness detected"
    )
    revenue_change_text = (
        "n/a because Q2 revenue is zero"
        if revenue_change is None
        else _format_percent(revenue_change)
    )

    return "\n".join(
        [
            "EMEA Partner Q3 vs Q2 comparison",
            softness,
            f"Q2 revenue: {_format_money(q2_revenue)}",
            f"Q3 revenue: {_format_money(q3_revenue)}",
            f"Revenue change: {revenue_change_text}",
            f"Q2 conversion rate: {_format_percent(q2_conversion)}",
            f"Q3 conversion rate: {_format_percent(q3_conversion)}",
            f"Conversion rate change: {conversion_change:.2%} points",
        ]
    )
