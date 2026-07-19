import re
from collections.abc import Callable
from typing import Any

from agent.intent import IntentStep, parse_intent
from agent.state import AgentState
from tools.analyse_data import analyse_data
from tools.forecast import forecast
from tools.search_documents import search_documents
from tools.visualise import visualise

MAX_ITERATIONS = 5
MAX_TOOL_CALLS = 5
UNSUPPORTED_QUERY_MESSAGE = "No supported tool route was found for this query."
GENERIC_TOOL_FAILURE_MESSAGE = "I could not complete the request with the selected tool yet."

ToolFunction = Callable[[str], str]

TOOL_REGISTRY: dict[str, ToolFunction] = {
    "analyse_data": analyse_data,
    "forecast": forecast,
    "visualise": visualise,
    "search_documents": search_documents,
}

FORECAST_KEYWORDS = {
    "forecast",
    "predict",
    "projection",
    "project",
    "future",
    "next week",
    "next month",
    "next quarter",
    "next year",
    "next 30 days",
    "next 4 weeks",
}

VISUALISE_KEYWORDS = {
    "chart",
    "graph",
    "plot",
    "visual",
    "visualise",
    "visualize",
    "bar chart",
    "line chart",
    "pie chart",
}

DOCUMENT_KEYWORDS = {
    "document",
    "docs",
    "report",
    "brief",
    "market overview",
    "product strategy",
    "commentary",
    "mentions",
    "say about",
    "risk",
    "risks",
}

ANALYSIS_KEYWORDS = {
    "analyse",
    "analyze",
    "analysis",
    "soft",
    "softness",
    "performance",
    "happened",
    "lost",
    "excluding",
    "without",
    "sales",
    "revenue",
    "margin",
    "gross margin",
    "units",
    "customer",
    "customers",
    "orders",
    "region",
    "channel",
    "product",
}


def _initial_state(query: str) -> AgentState:
    return {
        "messages": [{"role": "user", "content": query}],
        "tool_calls": [],
        "tool_results": [],
        "iterations": 0,
        "final_answer": None,
        "last_tools_used": [],
        "errors": [],
    }


def _query_tokens(query: str) -> set[str]:
    return set(re.findall(r"\b\w+\b", query.lower()))


def _contains_any(query: str, keywords: set[str]) -> bool:
    normalized_query = query.lower()
    tokens = _query_tokens(query)

    for keyword in keywords:
        normalized_keyword = keyword.lower()
        if " " in normalized_keyword:
            if re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized_query):
                return True
        elif normalized_keyword in tokens:
            return True
    return False


def _is_revenue_exclusion_or_risk_clause(clause: str) -> bool:
    normalized_clause = clause.lower()
    if "revenue" not in normalized_clause and "sales" not in normalized_clause:
        return False
    return any(
        phrase in normalized_clause
        for phrase in (
            "lost region",
            "lost regions",
            "lost",
            "lose ",
            "excluding",
            "exclude",
            "without",
            "at risk",
        )
    )


def _split_query_steps(query: str) -> list[str]:
    clauses = [
        clause.strip()
        for clause in re.split(r"\b(?:and then|then|and|also)\b|,", query, flags=re.IGNORECASE)
        if clause.strip()
    ]
    return clauses or [query]


def _route_clause_tool(clause: str) -> str | None:
    if _contains_any(clause, FORECAST_KEYWORDS):
        return "forecast"
    if _contains_any(clause, VISUALISE_KEYWORDS):
        return "visualise"
    if _is_revenue_exclusion_or_risk_clause(clause):
        return "analyse_data"
    if _contains_any(clause, DOCUMENT_KEYWORDS):
        return "search_documents"
    if _contains_any(clause, ANALYSIS_KEYWORDS):
        return "analyse_data"
    return None


def _tool_for_intent_step(step: IntentStep) -> str | None:
    if step.intent_type == "analysis":
        return "analyse_data"
    if step.intent_type == "visualisation":
        return "visualise"
    if step.intent_type == "forecast":
        return "forecast"
    if step.intent_type == "document_search":
        return "search_documents"
    return None


def plan_tool_calls(query: str) -> list[str]:
    planned: list[str] = []
    parsed_intent = parse_intent(query)
    for step in parsed_intent.steps:
        tool_name = _tool_for_intent_step(step)
        if tool_name and tool_name not in planned:
            planned.append(tool_name)
    return planned


def _limit_tool_plan(planned_tools: list[str]) -> tuple[list[str], str | None]:
    if len(planned_tools) <= MAX_TOOL_CALLS:
        return planned_tools, None
    return (
        planned_tools[:MAX_TOOL_CALLS],
        f"Tool call limit reached. Truncated plan to {MAX_TOOL_CALLS} calls.",
    )


def _format_successful_outputs(tool_results: list[dict[str, Any]]) -> str:
    successful_results = [
        result
        for result in tool_results
        if result["tool"] and not result["error"] and result["result"] is not None
    ]

    if not successful_results:
        return ""
    if len(successful_results) == 1:
        return str(successful_results[0]["result"])

    lines = []
    for index, result in enumerate(successful_results, start=1):
        lines.append(f"Step {index} ({result['tool']}):\n{result['result']}")
    return "\n\n".join(lines)


def _build_final_answer(tool_results: list[dict[str, Any]]) -> str:
    if not tool_results:
        return UNSUPPORTED_QUERY_MESSAGE

    successful_output_text = _format_successful_outputs(tool_results)
    failed_steps = [result for result in tool_results if result["error"]]

    if successful_output_text and not failed_steps:
        return successful_output_text
    if successful_output_text and failed_steps:
        return (
            f"{successful_output_text}\n\n"
            "I completed part of your request, but one or more steps could not be completed."
        )
    if failed_steps:
        return GENERIC_TOOL_FAILURE_MESSAGE
    return UNSUPPORTED_QUERY_MESSAGE


def _execute_planned_tools(state: AgentState, planned_tools: list[str]) -> None:
    user_query = state["messages"][-1]["content"]
    for tool_name in planned_tools:
        if state["iterations"] >= MAX_ITERATIONS:
            state["errors"].append("Iteration limit reached before completion.")
            break

        state["iterations"] += 1
        state["tool_calls"].append({"name": tool_name, "query": user_query})

        tool_result = execute_tool(tool_name, user_query)
        state["tool_results"].append(tool_result)

        if tool_result["tool"]:
            state["last_tools_used"].append(tool_result["tool"])
        if tool_result["error"]:
            state["errors"].append(tool_result["error"])


def route_tool(query: str) -> str | None:
    planned = plan_tool_calls(query)
    if planned:
        return planned[0]
    return None


def execute_tool(tool_name: str | None, query: str) -> dict[str, Any]:
    if tool_name is None:
        return {
            "tool": None,
            "result": UNSUPPORTED_QUERY_MESSAGE,
            "error": None,
        }

    tool = TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {
            "tool": tool_name,
            "result": None,
            "error": f"Unknown tool requested: {tool_name}",
        }

    try:
        return {"tool": tool_name, "result": tool(query), "error": None}
    except Exception as exc:  # pragma: no cover - defensive stub boundary
        return {"tool": tool_name, "result": None, "error": str(exc)}


def run_agent(query: str) -> str:
    return run_agent_with_trace(query)["answer"]


def run_agent_with_trace(query: str) -> dict[str, Any]:
    state = _initial_state(query)
    user_query = state["messages"][-1]["content"]
    parsed_intent = parse_intent(user_query)
    planned_tools, plan_warning = _limit_tool_plan(plan_tool_calls(user_query))
    if plan_warning:
        state["errors"].append(plan_warning)

    if not planned_tools:
        state["tool_calls"].append({"name": None, "query": user_query})
        state["tool_results"].append(
            {
                "tool": None,
                "result": UNSUPPORTED_QUERY_MESSAGE,
                "error": None,
            }
        )
    else:
        _execute_planned_tools(state, planned_tools)

    if state["iterations"] >= MAX_ITERATIONS and len(state["tool_results"]) < len(planned_tools):
        state["final_answer"] = "I stopped because the iteration limit was reached."
    else:
        state["final_answer"] = _build_final_answer(state["tool_results"])

    return {
        "answer": state["final_answer"] or "",
        "tools_used": state["last_tools_used"],
        "iterations": state["iterations"],
        "intermediate_outputs": state["tool_results"],
        "errors": state["errors"],
        "tool_calls": state["tool_calls"],
        "tool_results": state["tool_results"],
        "parsed_intent": parsed_intent.to_dict(),
    }
