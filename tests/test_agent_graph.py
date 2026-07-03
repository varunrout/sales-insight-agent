from agent.graph import (
    GENERIC_TOOL_FAILURE_MESSAGE,
    UNSUPPORTED_QUERY_MESSAGE,
    execute_tool,
    run_agent,
    run_agent_with_trace,
)


def test_graph_imports_successfully():
    import agent.graph as graph

    assert graph.MAX_ITERATIONS > 0


def test_run_agent_returns_string():
    answer = run_agent("What is total sales by region?")

    assert isinstance(answer, str)
    assert answer


def test_run_agent_with_trace_returns_expected_shape():
    trace = run_agent_with_trace("What is total revenue by sales channel?")

    assert isinstance(trace["answer"], str)
    assert isinstance(trace["tools_used"], list)
    assert isinstance(trace["iterations"], int)
    assert isinstance(trace["intermediate_outputs"], list)
    assert isinstance(trace["errors"], list)


def test_simple_sales_query_routes_to_analyse_data():
    trace = run_agent_with_trace("What is revenue by region?")

    assert trace["tools_used"] == ["analyse_data"]
    assert "Total revenue by region" in trace["answer"]


def test_singular_customer_query_routes_to_analyse_data():
    trace = run_agent_with_trace(
        "Which customer segment has the highest conversion rate?"
    )

    assert trace["tools_used"] == ["analyse_data"]
    assert "I can answer structured sales questions" in trace["answer"]


def test_forecast_query_routes_to_forecast():
    trace = run_agent_with_trace("Forecast revenue for the next month.")

    assert trace["tools_used"] == ["forecast"]
    assert "Forecast for revenue" in trace["answer"]


def test_chart_query_routes_to_visualise():
    trace = run_agent_with_trace("Show me a chart of gross margin by channel.")

    assert trace["tools_used"] == ["visualise"]
    assert "chart saved to" in trace["answer"]


def test_document_question_routes_to_search_documents():
    trace = run_agent_with_trace("What does the market overview say about EMEA?")

    assert trace["tools_used"] == ["search_documents"]
    assert "Top document matches:" in trace["answer"]
    assert "market_overview.md" in trace["answer"]


def test_unknown_or_unsupported_query_does_not_crash():
    trace = run_agent_with_trace("Can you make this more sparkly?")

    assert trace["tools_used"] == []
    assert trace["errors"] == []
    assert trace["answer"] == UNSUPPORTED_QUERY_MESSAGE
    assert trace["intermediate_outputs"][0]["result"] == UNSUPPORTED_QUERY_MESSAGE


def test_paragraph_does_not_route_to_visualise_by_substring():
    trace = run_agent_with_trace("Summarize this paragraph.")

    assert trace["tools_used"] == []
    assert trace["answer"] == UNSUPPORTED_QUERY_MESSAGE


def test_unknown_tool_is_handled_gracefully():
    result = execute_tool("not_a_tool", "Use an unknown tool.")

    assert result["tool"] == "not_a_tool"
    assert result["result"] is None
    assert result["error"] == "Unknown tool requested: not_a_tool"


def test_tool_error_details_are_not_exposed_in_answer(monkeypatch):
    import agent.graph as graph

    def failing_tool(query):
        raise RuntimeError("database password leaked in stack trace")

    monkeypatch.setitem(graph.TOOL_REGISTRY, "analyse_data", failing_tool)
    trace = graph.run_agent_with_trace("What is revenue by region?")

    assert trace["answer"] == GENERIC_TOOL_FAILURE_MESSAGE
    assert trace["errors"] == ["database password leaked in stack trace"]
    assert trace["intermediate_outputs"][0]["error"] == (
        "database password leaked in stack trace"
    )
    assert "database password" not in trace["answer"]


def test_iteration_limit_is_enforced(monkeypatch):
    import agent.graph as graph

    monkeypatch.setattr(graph, "MAX_ITERATIONS", 0)
    trace = graph.run_agent_with_trace("What is revenue by region?")

    assert trace["iterations"] == 0
    assert trace["errors"] == ["Iteration limit reached before completion."]
    assert "iteration limit" in trace["answer"].lower()
