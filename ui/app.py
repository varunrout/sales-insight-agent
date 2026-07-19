from __future__ import annotations

import re
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import config
from agent.graph import run_agent_with_trace

AVAILABLE_TOOLS = [
    "analyse_data",
    "forecast",
    "visualise",
    "search_documents",
]

EXAMPLE_PROMPTS = [
    "What is revenue by region?",
    "Show a chart of revenue by sales channel.",
    "Forecast revenue for the next month.",
    "What does the market overview say about EMEA?",
    "Search the docs for EMEA risks and forecast revenue for next month.",
]


def initialise_session_state(state: MutableMapping[str, Any] | None = None) -> None:
    target_state = st.session_state if state is None else state
    target_state.setdefault("chat_history", [])
    target_state.setdefault("queued_prompt", None)


def extract_chart_paths(text: str) -> list[Path]:
    if not text:
        return []

    paths: list[Path] = []
    seen: set[str] = set()
    saved_to_matches = re.findall(r"saved to ([^\n]+?\.html)", text, flags=re.IGNORECASE)
    generic_matches = re.findall(
        r"(?<!\S)([A-Za-z]:\\[^\s]+?\.html|[^\s]+[\\/][^\s]+?\.html)",
        text,
    )

    for raw_match in saved_to_matches + generic_matches:
        cleaned = raw_match.strip().strip("`\"'.,);]")
        if not cleaned:
            continue
        normalized = str(Path(cleaned))
        if normalized in seen:
            continue
        seen.add(normalized)
        paths.append(Path(cleaned))

    return paths


def load_dataset_summary(data_path: Path | None = None) -> dict[str, Any]:
    path = data_path or config.DATA_PATH
    summary: dict[str, Any] = {
        "path": str(path),
        "row_count": None,
        "date_range": "Unavailable",
        "error": None,
    }

    if not path.exists():
        summary["error"] = "Dataset file not found."
        return summary

    try:
        data = pd.read_csv(path, parse_dates=["date"])
        summary["row_count"] = int(len(data))
        if "date" in data.columns and not data["date"].isna().all():
            summary["date_range"] = f"{data['date'].min().date()} to {data['date'].max().date()}"
        else:
            summary["date_range"] = "Date column unavailable"
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        summary["error"] = str(exc)

    return summary


def _normalise_chart_path(chart_path: Path) -> Path:
    if chart_path.is_absolute():
        return chart_path
    return Path.cwd() / chart_path


def _render_chart_outputs(text: str) -> None:
    chart_paths = extract_chart_paths(text)
    if not chart_paths:
        return

    for chart_path in chart_paths:
        resolved_path = _normalise_chart_path(chart_path)
        if not resolved_path.exists():
            st.warning(f"Chart file not found: {resolved_path}")
            continue

        try:
            html_content = resolved_path.read_text(encoding="utf-8")
            components.html(html_content, height=560, scrolling=True)
        except OSError:
            st.info(f"Open chart file: {resolved_path}")


def _format_trace_json(data: Any) -> str:
    import json

    return json.dumps(data, indent=2, default=str)


def _render_assistant_trace(trace: dict[str, Any]) -> None:
    tools_used = trace.get("tools_used", [])
    if tools_used:
        st.caption(f"Tools used: {', '.join(tools_used)}")
    else:
        st.caption("Tools used: none")

    with st.expander("Intermediate outputs", expanded=False):
        st.code(_format_trace_json(trace.get("intermediate_outputs", [])), language="json")

    errors = trace.get("errors", [])
    if errors:
        with st.expander("Errors", expanded=False):
            st.code(_format_trace_json(errors), language="json")


def _render_chat_message(message: dict[str, Any]) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            trace = message.get("trace", {})
            _render_assistant_trace(trace)
            _render_chart_outputs(message["content"])


def _render_sidebar() -> None:
    with st.sidebar:
        st.header("Tools")
        for tool_name in AVAILABLE_TOOLS:
            st.write(f"- {tool_name}")

        st.header("Dataset")
        dataset_summary = load_dataset_summary()
        st.write(f"Path: `{dataset_summary['path']}`")
        if dataset_summary["row_count"] is not None:
            st.write(f"Rows: {dataset_summary['row_count']:,}")
        st.write(f"Date range: {dataset_summary['date_range']}")
        if dataset_summary["error"]:
            st.caption(dataset_summary["error"])

        st.header("Example prompts")
        for prompt in EXAMPLE_PROMPTS:
            if st.button(prompt, key=f"example-{prompt}"):
                st.session_state["queued_prompt"] = prompt

        if st.button("Clear chat", type="secondary"):
            st.session_state["chat_history"] = []
            st.session_state["queued_prompt"] = None
            st.rerun()


def _run_query(query: str) -> dict[str, Any]:
    try:
        return run_agent_with_trace(query)
    except Exception as exc:  # pragma: no cover - defensive UI boundary
        return {
            "answer": "I couldn't process your request right now.",
            "tools_used": [],
            "intermediate_outputs": [],
            "errors": [str(exc)],
            "iterations": 0,
        }


def main() -> None:
    st.set_page_config(page_title="Sales Insight Agent", page_icon="📈", layout="wide")
    st.title("Sales Insight Agent")
    st.caption("Ask natural-language sales questions and inspect tool traces.")

    initialise_session_state()
    _render_sidebar()

    for message in st.session_state["chat_history"]:
        _render_chat_message(message)

    chat_query = st.chat_input("Ask a sales question")
    queued_query = st.session_state.pop("queued_prompt", None)
    user_query = chat_query or queued_query

    if not user_query:
        return

    user_message = {"role": "user", "content": user_query}
    st.session_state["chat_history"].append(user_message)
    _render_chat_message(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Working on your request..."):
            trace = _run_query(user_query)
        answer = str(trace.get("answer", ""))
        st.markdown(answer)
        _render_assistant_trace(trace)
        _render_chart_outputs(answer)

    st.session_state["chat_history"].append(
        {
            "role": "assistant",
            "content": answer,
            "trace": trace,
        }
    )


if __name__ == "__main__":
    main()
