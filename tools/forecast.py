import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error

import config
from tools.data_loader import load_sales_data


TOOL_NAME = "forecast"
DATA_PATH = config.DATA_PATH

REQUIRED_COLUMNS = {"date", "revenue", "units_sold", "new_customers"}
NUMERIC_COLUMNS = {"revenue", "units_sold", "new_customers"}
SUPPORTED_METRICS = {"revenue", "units_sold", "new_customers"}

UNSUPPORTED_MESSAGE = (
    "I can forecast revenue, units_sold or new_customers for future daily or "
    "weekly horizons such as next 30 days, next month or next 4 weeks."
)


def forecast(query: str) -> str:
    metric = _parse_metric(query)
    if metric is None:
        return UNSUPPORTED_MESSAGE

    data = _load_sales_data(DATA_PATH)
    if isinstance(data, str):
        return data

    horizon_days = _parse_horizon_days(query)
    output_frequency = _parse_output_frequency(query)
    series = _aggregate_daily(data, metric)

    if len(series) < 90:
        return "Not enough historical data to produce a reliable forecast."

    model_result = _fit_backtest_model(series, metric)
    future = _forecast_future(
        series=series,
        metric=metric,
        model=model_result["model"],
        residuals=model_result["residuals"],
        horizon_days=horizon_days,
    )
    display_rows = _format_future_rows(future, metric, output_frequency)

    metric_label = metric.replace("_", " ")
    return "\n".join(
        [
            f"Forecast for {metric_label}",
            f"Horizon: {horizon_days} days",
            f"Output frequency: {output_frequency}",
            f"Backtest MAE: {_format_number(model_result['mae'])}",
            f"Backtest RMSE: {_format_number(model_result['rmse'])}",
            "Future forecast rows:",
            display_rows,
        ]
    )


def _load_sales_data(data_path: Path) -> pd.DataFrame | str:
    return load_sales_data(data_path, REQUIRED_COLUMNS, NUMERIC_COLUMNS)


def _parse_metric(query: str) -> str | None:
    normalized_query = query.lower()
    if "new customers" in normalized_query or "new_customers" in normalized_query:
        return "new_customers"
    if "unit" in normalized_query or "units_sold" in normalized_query:
        return "units_sold"
    if "revenue" in normalized_query or "sales" in normalized_query:
        return "revenue"
    return None


def _parse_horizon_days(query: str) -> int:
    normalized_query = query.lower()
    days_match = re.search(r"\bnext\s+(\d{1,3})\s+days?\b", normalized_query)
    if days_match:
        return max(1, min(int(days_match.group(1)), 180))

    weeks_match = re.search(r"\bnext\s+(\d{1,2})\s+weeks?\b", normalized_query)
    if weeks_match:
        return max(7, min(int(weeks_match.group(1)) * 7, 180))

    if "next month" in normalized_query:
        return 30
    if "next quarter" in normalized_query:
        return 90
    return 30


def _parse_output_frequency(query: str) -> str:
    normalized_query = query.lower()
    if "daily" in normalized_query or "day" in normalized_query:
        return "daily"
    if "weekly" in normalized_query or "week" in normalized_query:
        return "weekly"
    return "daily"


def _aggregate_daily(data: pd.DataFrame, metric: str) -> pd.DataFrame:
    daily = (
        data.groupby("date", as_index=False)[metric]
        .sum()
        .sort_values("date")
        .reset_index(drop=True)
    )
    all_dates = pd.date_range(daily["date"].min(), daily["date"].max(), freq="D")
    daily = daily.set_index("date").reindex(all_dates, fill_value=0)
    daily.index.name = "date"
    return daily.reset_index()


def _add_features(series: pd.DataFrame, metric: str) -> pd.DataFrame:
    featured = series.copy()
    featured["lag_1"] = featured[metric].shift(1)
    featured["lag_7"] = featured[metric].shift(7)
    featured["rolling_7"] = featured[metric].shift(1).rolling(7).mean()
    featured["rolling_28"] = featured[metric].shift(1).rolling(28).mean()
    featured["day_of_week"] = featured["date"].dt.dayofweek
    featured["month"] = featured["date"].dt.month
    featured["week_of_year"] = featured["date"].dt.isocalendar().week.astype(int)
    featured["time_index"] = np.arange(len(featured))
    return featured.dropna().reset_index(drop=True)


def _feature_columns() -> list[str]:
    return [
        "lag_1",
        "lag_7",
        "rolling_7",
        "rolling_28",
        "day_of_week",
        "month",
        "week_of_year",
        "time_index",
    ]


def _build_model():
    try:
        return HistGradientBoostingRegressor(max_iter=160, random_state=42)
    except Exception:
        return RandomForestRegressor(n_estimators=120, random_state=42, n_jobs=1)


def _fit_backtest_model(series: pd.DataFrame, metric: str) -> dict[str, object]:
    featured = _add_features(series, metric)
    test_size = min(60, max(28, len(featured) // 5))
    train = featured.iloc[:-test_size]
    test = featured.iloc[-test_size:]
    features = _feature_columns()

    model = _build_model()
    model.fit(train[features], train[metric])
    predictions = np.maximum(model.predict(test[features]), 0)
    residuals = test[metric].to_numpy() - predictions

    final_model = _build_model()
    final_model.fit(featured[features], featured[metric])

    return {
        "model": final_model,
        "mae": float(mean_absolute_error(test[metric], predictions)),
        "rmse": float(np.sqrt(np.mean((test[metric].to_numpy() - predictions) ** 2))),
        "residuals": residuals,
    }


def _forecast_future(
    series: pd.DataFrame,
    metric: str,
    model,
    residuals: np.ndarray,
    horizon_days: int,
) -> pd.DataFrame:
    history = series[["date", metric]].copy()
    future_rows = []
    q10, q90 = np.quantile(residuals, [0.10, 0.90])

    for _ in range(horizon_days):
        next_date = history["date"].max() + pd.Timedelta(days=1)
        feature_row = _next_feature_row(history, metric, next_date)
        p50 = max(float(model.predict(feature_row[_feature_columns()])[0]), 0)
        p10 = max(p50 + float(q10), 0)
        p90 = max(p50 + float(q90), p10)

        future_rows.append(
            {
                "date": next_date,
                "p10": p10,
                "p50": p50,
                "p90": p90,
            }
        )
        history = pd.concat(
            [history, pd.DataFrame([{"date": next_date, metric: p50}])],
            ignore_index=True,
        )

    return pd.DataFrame(future_rows)


def _next_feature_row(history: pd.DataFrame, metric: str, next_date: pd.Timestamp) -> pd.DataFrame:
    values = history[metric]
    row = {
        "lag_1": values.iloc[-1],
        "lag_7": values.iloc[-7],
        "rolling_7": values.iloc[-7:].mean(),
        "rolling_28": values.iloc[-28:].mean(),
        "day_of_week": next_date.dayofweek,
        "month": next_date.month,
        "week_of_year": int(next_date.isocalendar().week),
        "time_index": len(history),
    }
    return pd.DataFrame([row])


def _format_future_rows(future: pd.DataFrame, metric: str, output_frequency: str) -> str:
    if output_frequency == "weekly":
        display = (
            future.assign(week_start=future["date"].dt.to_period("W").dt.start_time)
            .groupby("week_start", as_index=False)[["p10", "p50", "p90"]]
            .sum()
            .rename(columns={"week_start": "period"})
        )
    else:
        display = future.rename(columns={"date": "period"})

    rows = []
    for row in display.head(12).itertuples(index=False):
        rows.append(
            f"- {row.period.date()}: P10={_format_number(row.p10)}, "
            f"P50={_format_number(row.p50)}, P90={_format_number(row.p90)}"
        )
    if len(display) > 12:
        rows.append(f"... {len(display) - 12} more future periods")
    return "\n".join(rows)


def _format_number(value: float) -> str:
    return f"{value:,.2f}"
