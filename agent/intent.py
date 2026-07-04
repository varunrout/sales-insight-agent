from __future__ import annotations

from dataclasses import asdict, dataclass, field
import re
from typing import Any


INTENT_ANALYSIS = "analysis"
INTENT_VISUALISATION = "visualisation"
INTENT_FORECAST = "forecast"
INTENT_DOCUMENT_SEARCH = "document_search"
INTENT_UNSUPPORTED = "unsupported"


@dataclass(frozen=True)
class IntentStep:
    intent_type: str
    metric: str | None = None
    dimensions: list[str] = field(default_factory=list)
    filters: dict[str, list[str]] = field(default_factory=dict)
    exclusions: dict[str, list[str]] = field(default_factory=dict)
    comparison: str | None = None
    analysis_type: str | None = None
    output_type: str | None = None
    original_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ParsedIntent:
    original_query: str
    steps: list[IntentStep]
    is_compound: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_query": self.original_query,
            "steps": [step.to_dict() for step in self.steps],
            "is_compound": self.is_compound,
        }


METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "revenue": ("revenue", "sales", "turnover"),
    "units_sold": ("units sold", "units_sold", "units", "volume", "quantity"),
    "new_customers": ("new customers", "customer acquisition"),
    "gross_margin": ("gross margin", "margin"),
    "order_count": ("order count", "orders"),
    "conversion_rate": ("conversion rate", "conversion"),
    "marketing_spend": ("marketing spend", "ad spend", "spend"),
}

DIMENSION_ALIASES: dict[str, tuple[str, ...]] = {
    "region": ("region", "regions"),
    "country": ("country", "countries"),
    "product_category": ("product category", "category", "categories"),
    "product_name": ("product name", "product", "products"),
    "sales_channel": ("sales channel", "channel", "channels"),
    "customer_segment": ("customer segment", "segment", "segments"),
    "month": ("month", "monthly"),
    "quarter": ("quarter", "q1", "q2", "q3", "q4"),
    "year": ("year", "annual", "yearly"),
}

KNOWN_VALUES: dict[str, tuple[str, ...]] = {
    "region": ("North America", "EMEA", "APAC", "LATAM"),
    "sales_channel": ("Direct", "Partner", "Marketplace"),
    "customer_segment": ("Enterprise", "Mid-Market", "SMB"),
    "product_category": (
        "Analytics Platform",
        "Automation Tools",
        "Enterprise Suite",
        "Services",
    ),
}

VISUALISATION_TERMS = {
    "chart",
    "graph",
    "plot",
    "visual",
    "visualise",
    "visualize",
}

FORECAST_TERMS = {
    "forecast",
    "predict",
    "projection",
    "project",
    "future",
    "next month",
    "next quarter",
    "next 4 weeks",
    "next 30 days",
}

DOCUMENT_TERMS = {
    "docs",
    "document",
    "documents",
    "report",
    "market overview",
    "product strategy",
    "says about",
    "say about",
    "mentions",
    "mentioned",
    "brief",
    "commentary",
}


def parse_intent(query: str) -> ParsedIntent:
    parts = _split_query_steps(query)
    steps = [_parse_step(part) for part in parts]
    return ParsedIntent(
        original_query=query,
        steps=steps,
        is_compound=len(steps) > 1,
    )


def _split_query_steps(query: str) -> list[str]:
    clauses = [
        clause.strip()
        for clause in re.split(
            r"\b(?:and then|then|also)\b|"
            r"\band\b(?=\s+(?:show|chart|plot|forecast|predict|search|analyse|analyze|what does))|,",
            query,
            flags=re.IGNORECASE,
        )
        if clause.strip()
    ]
    return clauses or [query]


def _parse_step(text: str) -> IntentStep:
    normalized = text.lower()
    metric = _parse_metric(normalized)
    dimensions = _parse_dimensions(normalized)
    filters = _parse_filters(normalized)
    exclusions = _parse_exclusions(normalized)
    comparison = _parse_comparison(normalized)
    analysis_type = _parse_analysis_type(normalized, dimensions, exclusions)
    output_type = _parse_output_type(normalized)
    intent_type = _parse_intent_type(
        normalized=normalized,
        metric=metric,
        dimensions=dimensions,
        filters=filters,
        exclusions=exclusions,
        comparison=comparison,
        analysis_type=analysis_type,
        output_type=output_type,
    )

    return IntentStep(
        intent_type=intent_type,
        metric=metric,
        dimensions=dimensions,
        filters=filters,
        exclusions=exclusions,
        comparison=comparison,
        analysis_type=analysis_type,
        output_type=output_type,
        original_text=text,
    )


def _parse_metric(normalized: str) -> str | None:
    for metric, aliases in METRIC_ALIASES.items():
        if any(_contains_phrase(normalized, alias) for alias in aliases):
            return metric
    return None


def _parse_dimensions(normalized: str) -> list[str]:
    dimensions: list[str] = []
    for dimension, aliases in DIMENSION_ALIASES.items():
        if any(_contains_phrase(normalized, alias) for alias in aliases):
            dimensions.append(dimension)
    return dimensions


def _parse_filters(normalized: str) -> dict[str, list[str]]:
    filters: dict[str, list[str]] = {}
    for field_name, values in KNOWN_VALUES.items():
        matches = [
            value
            for value in values
            if _contains_phrase(normalized, value.lower())
            and value not in _excluded_values_for_field(normalized, field_name)
        ]
        if matches:
            filters[field_name] = matches
    return filters


def _parse_exclusions(normalized: str) -> dict[str, list[str]]:
    exclusions: dict[str, list[str]] = {}
    for field_name, values in KNOWN_VALUES.items():
        excluded = _excluded_values_for_field(normalized, field_name, values)
        if excluded:
            exclusions[field_name] = excluded
    return exclusions


def _excluded_values_for_field(
    normalized: str,
    field_name: str,
    values: tuple[str, ...] | None = None,
) -> list[str]:
    if values is None:
        values = KNOWN_VALUES[field_name]
    if not any(
        _contains_phrase(normalized, term)
        for term in ("excluding", "exclude", "without", "lost", "lose", "at risk")
    ):
        return []
    return [
        value
        for value in values
        if _contains_phrase(normalized, value.lower())
    ]


def _parse_comparison(normalized: str) -> str | None:
    if _contains_phrase(normalized, "q3") and (
        _contains_phrase(normalized, "q2")
        or "soft" in normalized
        or "performance" in normalized
    ):
        return "q3_vs_q2"
    if (
        _contains_phrase(normalized, "month-over-month")
        or _contains_phrase(normalized, "month over month")
        or re.search(r"\bmom\b", normalized)
    ):
        return "month_over_month"
    if _contains_phrase(normalized, "recent") and _contains_phrase(normalized, "previous"):
        return "recent_vs_previous"
    return None


def _parse_analysis_type(
    normalized: str,
    dimensions: list[str],
    exclusions: dict[str, list[str]],
) -> str | None:
    if exclusions:
        return "exclusion_impact"
    if _contains_phrase(normalized, "top"):
        return "top_n"
    if _contains_phrase(normalized, "average") or _contains_phrase(normalized, "avg"):
        return "average"
    if _contains_phrase(normalized, "soft") or _contains_phrase(normalized, "softness"):
        return "softness_diagnostic"
    if _contains_phrase(normalized, "underperforming") or _contains_phrase(
        normalized, "underperformance"
    ):
        return "underperformance"
    if (
        _contains_phrase(normalized, "exposed")
        or _contains_phrase(normalized, "risk")
        or _contains_phrase(normalized, "risks")
    ):
        if _contains_phrase(normalized, "most exposed"):
            return "concentration"
        return "risk"
    if _contains_phrase(normalized, "prioritise") or _contains_phrase(
        normalized, "prioritize"
    ):
        return "opportunity"
    if _contains_phrase(normalized, "by") and dimensions:
        return "breakdown"
    return None


def _parse_output_type(normalized: str) -> str | None:
    if any(_contains_phrase(normalized, term) for term in VISUALISATION_TERMS):
        return "chart"
    if any(_contains_phrase(normalized, term) for term in FORECAST_TERMS):
        return "forecast"
    if any(_contains_phrase(normalized, term) for term in DOCUMENT_TERMS):
        return "document_evidence"
    return "text"


def _parse_intent_type(
    *,
    normalized: str,
    metric: str | None,
    dimensions: list[str],
    filters: dict[str, list[str]],
    exclusions: dict[str, list[str]],
    comparison: str | None,
    analysis_type: str | None,
    output_type: str | None,
) -> str:
    if output_type == "forecast":
        return INTENT_FORECAST
    if output_type == "chart":
        return INTENT_VISUALISATION
    if output_type == "document_evidence":
        return INTENT_DOCUMENT_SEARCH
    if (
        metric
        or dimensions
        or filters
        or exclusions
        or comparison
        or analysis_type
        or any(
            _contains_phrase(normalized, term)
            for term in ("analyse", "analyze", "analysis", "what happened", "why")
        )
    ):
        return INTENT_ANALYSIS
    return INTENT_UNSUPPORTED


def _contains_phrase(text: str, phrase: str) -> bool:
    return bool(re.search(rf"\b{re.escape(phrase.lower())}\b", text))
