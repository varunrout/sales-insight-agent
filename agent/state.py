from typing import Any, TypedDict


class AgentState(TypedDict):
    messages: list[dict[str, str]]
    tool_calls: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]
    iterations: int
    final_answer: str | None
    last_tools_used: list[str]
    errors: list[str]
