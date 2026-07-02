from collections.abc import Callable
import re
from typing import Any

from agent.state import AgentState
from tools.analyse_data import analyse_data
from tools.forecast import forecast
from tools.search_documents import search_documents
from tools.visualise import visualise


MAX_ITERATIONS = 3
UNSUPPORTED_QUERY_MESSAGE = "No supported tool route was found for this query."
GENERIC_TOOL_FAILURE_MESSAGE = (
    "I could not complete the request with the selected tool yet."
)

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


def route_tool(query: str) -> str | None:
    if _contains_any(query, FORECAST_KEYWORDS):
        return "forecast"
    if _contains_any(query, VISUALISE_KEYWORDS):
        return "visualise"
    if _contains_any(query, DOCUMENT_KEYWORDS):
        return "search_documents"
    if _contains_any(query, ANALYSIS_KEYWORDS):
        return "analyse_data"
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


def _build_final_answer(tool_result: dict[str, Any]) -> str:
    if tool_result["error"]:
        return GENERIC_TOOL_FAILURE_MESSAGE
    return str(tool_result["result"])


def run_agent(query: str) -> str:
    return run_agent_with_trace(query)["answer"]


def run_agent_with_trace(query: str) -> dict[str, Any]:
    state = _initial_state(query)

    while state["final_answer"] is None:
        if state["iterations"] >= MAX_ITERATIONS:
            state["errors"].append("Iteration limit reached before completion.")
            state["final_answer"] = "I stopped because the iteration limit was reached."
            break

        state["iterations"] += 1
        user_query = state["messages"][-1]["content"]
        tool_name = route_tool(user_query)
        state["tool_calls"].append({"name": tool_name, "query": user_query})

        tool_result = execute_tool(tool_name, user_query)
        state["tool_results"].append(tool_result)

        if tool_result["tool"]:
            state["last_tools_used"].append(tool_result["tool"])
        if tool_result["error"]:
            state["errors"].append(tool_result["error"])

        state["final_answer"] = _build_final_answer(tool_result)

    return {
        "answer": state["final_answer"] or "",
        "tools_used": state["last_tools_used"],
        "iterations": state["iterations"],
        "intermediate_outputs": state["tool_results"],
        "errors": state["errors"],
        "tool_calls": state["tool_calls"],
        "tool_results": state["tool_results"],
    }


def build_graph() -> Any:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return None

    graph = StateGraph(AgentState)

    def route_node(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        tool_name = route_tool(query)
        state["tool_calls"].append({"name": tool_name, "query": query})
        return state

    def tool_node(state: AgentState) -> AgentState:
        query = state["messages"][-1]["content"]
        tool_name = state["tool_calls"][-1]["name"]
        tool_result = execute_tool(tool_name, query)
        state["tool_results"].append(tool_result)
        if tool_result["tool"]:
            state["last_tools_used"].append(tool_result["tool"])
        if tool_result["error"]:
            state["errors"].append(tool_result["error"])
        state["iterations"] += 1
        state["final_answer"] = _build_final_answer(tool_result)
        return state

    graph.add_node("route", route_node)
    graph.add_node("tool", tool_node)
    graph.set_entry_point("route")
    graph.add_edge("route", "tool")
    graph.add_edge("tool", END)
    return graph.compile()
