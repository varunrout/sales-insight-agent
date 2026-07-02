import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sample_sales.csv"
DOCS_PATH = ROOT / "data" / "docs"
QUESTIONS_PATH = ROOT / "data" / "sample_questions.json"

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

QUESTION_TYPES = {"structured", "forecast", "visualisation", "document", "multi-step"}


def _read_sales_rows():
    with DATA_PATH.open(newline="", encoding="utf-8") as sales_file:
        return list(csv.DictReader(sales_file))


def test_sample_sales_csv_exists():
    assert DATA_PATH.exists()


def test_required_columns_exist():
    rows = _read_sales_rows()
    assert rows
    assert REQUIRED_COLUMNS.issubset(rows[0].keys())


def test_dates_parse_and_cover_at_least_18_months():
    rows = _read_sales_rows()
    parsed_dates = [datetime.strptime(row["date"], "%Y-%m-%d").date() for row in rows]
    min_date = min(parsed_dates)
    max_date = max(parsed_dates)
    month_span = (max_date.year - min_date.year) * 12 + max_date.month - min_date.month + 1

    assert min_date < max_date
    assert month_span >= 18


def test_metric_columns_are_numeric():
    rows = _read_sales_rows()

    for row in rows[:250]:
        for column in NUMERIC_COLUMNS:
            float(row[column])


def test_docs_contains_at_least_three_markdown_documents():
    markdown_docs = list(DOCS_PATH.glob("*.md"))
    assert len(markdown_docs) >= 3


def test_sample_questions_cover_expected_route_types():
    with QUESTIONS_PATH.open(encoding="utf-8") as questions_file:
        questions = json.load(questions_file)

    assert isinstance(questions, list)
    assert questions
    assert QUESTION_TYPES.issubset({question.get("type") for question in questions})

    for question in questions:
        assert isinstance(question.get("question"), str)
        assert isinstance(question.get("expected_tool_route"), list)
        assert question["expected_tool_route"]
