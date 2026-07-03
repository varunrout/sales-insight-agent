from pathlib import Path

from ui.app import extract_chart_paths, initialise_session_state, load_dataset_summary


def test_extract_chart_paths_returns_saved_html_paths_in_order():
    text = (
        "Revenue by region chart saved to outputs/charts/revenue_by_region.html\n"
        "Monthly trend chart saved to outputs/charts/monthly_revenue.html"
    )

    paths = extract_chart_paths(text)

    assert paths == [
        Path("outputs/charts/revenue_by_region.html"),
        Path("outputs/charts/monthly_revenue.html"),
    ]


def test_extract_chart_paths_deduplicates_paths():
    text = (
        "Chart saved to outputs/charts/revenue_by_region.html\n"
        "Again: outputs/charts/revenue_by_region.html"
    )

    paths = extract_chart_paths(text)

    assert paths == [Path("outputs/charts/revenue_by_region.html")]


def test_initialise_session_state_sets_required_defaults():
    state = {}

    initialise_session_state(state)

    assert state["chat_history"] == []
    assert state["queued_prompt"] is None


def test_initialise_session_state_preserves_existing_values():
    state = {"chat_history": [{"role": "user", "content": "hello"}], "queued_prompt": "x"}

    initialise_session_state(state)

    assert state["chat_history"] == [{"role": "user", "content": "hello"}]
    assert state["queued_prompt"] == "x"


def test_load_dataset_summary_reads_row_count_and_date_range(tmp_path):
    dataset_path = tmp_path / "sample.csv"
    dataset_path.write_text(
        "date,revenue\n2024-01-01,100\n2024-01-10,200\n",
        encoding="utf-8",
    )

    summary = load_dataset_summary(dataset_path)

    assert summary["path"] == str(dataset_path)
    assert summary["row_count"] == 2
    assert summary["date_range"] == "2024-01-01 to 2024-01-10"
    assert summary["error"] is None


def test_load_dataset_summary_handles_missing_file(tmp_path):
    missing_path = tmp_path / "missing.csv"

    summary = load_dataset_summary(missing_path)

    assert summary["path"] == str(missing_path)
    assert summary["row_count"] is None
    assert summary["date_range"] == "Unavailable"
    assert summary["error"] == "Dataset file not found."
