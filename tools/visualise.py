import re
from pathlib import Path

import pandas as pd
import plotly.express as px

import config


TOOL_NAME = "visualise"
DATA_PATH = config.DATA_PATH
CHART_OUTPUT_PATH = config.CHART_OUTPUT_PATH

REQUIRED_COLUMNS = {
    "date",
    "region",
    "product_category",
    "product_name",
    "sales_channel",
    "revenue",
    "units_sold",
    "gross_margin",
}

NUMERIC_COLUMNS = {"revenue", "units_sold", "gross_margin"}

UNSUPPORTED_MESSAGE = (
    "I can create charts for revenue by region, product category or sales "
    "channel; monthly revenue; month-over-month revenue; average gross margin "
    "by sales channel; and top products by revenue or units sold."
)


def visualise(query: str) -> str:
    data = _load_sales_data(DATA_PATH)
    if isinstance(data, str):
        return data

    normalized_query = query.lower()

    if _asks_month_over_month_revenue(normalized_query):
        return _monthly_revenue_chart(data, month_over_month=True)
    if _asks_monthly_revenue(normalized_query):
        return _monthly_revenue_chart(data, month_over_month=False)
    if _asks_average_margin_by_channel(normalized_query):
        return _average_gross_margin_by_channel_chart(data)
    if _asks_top_products_by_units(normalized_query):
        return _top_products_chart(data, "units_sold", query)
    if _asks_top_products_by_revenue(normalized_query):
        return _top_products_chart(data, "revenue", query)
    if _asks_revenue_by(normalized_query, "region"):
        return _revenue_bar_chart(data, "region")
    if _asks_revenue_by(normalized_query, "product category"):
        return _revenue_bar_chart(data, "product_category")
    if _asks_revenue_by(normalized_query, "sales channel") or _asks_revenue_by(
        normalized_query, "channel"
    ):
        return _revenue_bar_chart(data, "sales_channel")

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


def _asks_revenue_by(normalized_query: str, dimension: str) -> bool:
    return "revenue" in normalized_query and bool(
        re.search(rf"\bby\s+{re.escape(dimension)}\b", normalized_query)
    )


def _asks_monthly_revenue(normalized_query: str) -> bool:
    return "revenue" in normalized_query and (
        "monthly" in normalized_query
        or "month by month" in normalized_query
        or "by month" in normalized_query
    )


def _asks_month_over_month_revenue(normalized_query: str) -> bool:
    return "revenue" in normalized_query and (
        "month-over-month" in normalized_query
        or "month over month" in normalized_query
        or "mom" in normalized_query
    )


def _asks_average_margin_by_channel(normalized_query: str) -> bool:
    return (
        "gross margin" in normalized_query
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
        and ("units" in normalized_query or "units_sold" in normalized_query)
    )


def _parse_top_n(query: str, default: int = 5) -> int:
    match = re.search(r"\btop\s+(\d{1,2})\b", query.lower())
    if not match:
        return default
    return max(1, min(int(match.group(1)), 20))


def _save_chart(fig, filename: str, description: str) -> str:
    CHART_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
    chart_path = CHART_OUTPUT_PATH / filename
    fig.write_html(chart_path, include_plotlyjs="cdn", full_html=True)
    return f"{description} chart saved to {chart_path}"


def _revenue_bar_chart(data: pd.DataFrame, dimension: str) -> str:
    grouped = (
        data.groupby(dimension, as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )
    label = dimension.replace("_", " ")
    fig = px.bar(
        grouped,
        x=dimension,
        y="revenue",
        title=f"Revenue by {label}",
        labels={dimension: label.title(), "revenue": "Revenue"},
    )
    return _save_chart(
        fig,
        f"revenue_by_{dimension}.html",
        f"Revenue by {label}",
    )


def _monthly_revenue_chart(data: pd.DataFrame, month_over_month: bool) -> str:
    monthly = (
        data.assign(month=data["date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False)["revenue"]
        .sum()
        .sort_values("month")
    )
    if month_over_month:
        monthly["mom_revenue_change"] = monthly["revenue"].pct_change().fillna(0)
        fig = px.line(
            monthly,
            x="month",
            y="mom_revenue_change",
            title="Month-over-month revenue change",
            labels={"month": "Month", "mom_revenue_change": "MoM revenue change"},
        )
        return _save_chart(
            fig,
            "month_over_month_revenue.html",
            "Month-over-month revenue",
        )

    fig = px.line(
        monthly,
        x="month",
        y="revenue",
        title="Monthly revenue",
        labels={"month": "Month", "revenue": "Revenue"},
    )
    return _save_chart(fig, "monthly_revenue.html", "Monthly revenue")


def _average_gross_margin_by_channel_chart(data: pd.DataFrame) -> str:
    grouped = (
        data.groupby("sales_channel", as_index=False)["gross_margin"]
        .mean()
        .sort_values("gross_margin", ascending=False)
    )
    fig = px.bar(
        grouped,
        x="sales_channel",
        y="gross_margin",
        title="Average gross margin by sales channel",
        labels={
            "sales_channel": "Sales Channel",
            "gross_margin": "Average Gross Margin",
        },
    )
    return _save_chart(
        fig,
        "average_gross_margin_by_sales_channel.html",
        "Average gross margin by sales channel",
    )


def _top_products_chart(data: pd.DataFrame, metric: str, query: str) -> str:
    top_n = _parse_top_n(query)
    grouped = (
        data.groupby("product_name", as_index=False)[metric]
        .sum()
        .sort_values(metric, ascending=False)
        .head(top_n)
    )
    metric_label = metric.replace("_", " ")
    fig = px.bar(
        grouped,
        x="product_name",
        y=metric,
        title=f"Top {top_n} products by {metric_label}",
        labels={"product_name": "Product", metric: metric_label.title()},
    )
    return _save_chart(
        fig,
        f"top_{top_n}_products_by_{metric}.html",
        f"Top {top_n} products by {metric_label}",
    )
