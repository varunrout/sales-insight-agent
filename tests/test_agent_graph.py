from agent.graph import execute_tool, run_agent, run_agent_with_trace


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
    assert isinstance(trace["errors"], list)


def test_simple_sales_query_routes_to_analyse_data():
    trace = run_agent_with_trace("What is revenue by region?")

    assert trace["tools_used"] == ["analyse_data"]
    assert "analyse_data placeholder" in trace["answer"]


def test_forecast_query_routes_to_forecast():
    trace = run_agent_with_trace("Forecast revenue for the next month.")

    assert trace["tools_used"] == ["forecast"]
    assert "forecast placeholder" in trace["answer"]


def test_chart_query_routes_to_visualise():
    trace = run_agent_with_trace("Show me a chart of gross margin by channel.")

    assert trace["tools_used"] == ["visualise"]
    assert "visualise placeholder" in trace["answer"]


def test_document_question_routes_to_search_documents():
    trace = run_agent_with_trace("What does the market overview say about EMEA?")

    assert trace["tools_used"] == ["search_documents"]
    assert "search_documents placeholder" in trace["answer"]


def test_unknown_or_unsupported_query_does_not_crash():
    trace = run_agent_with_trace("Can you make this more sparkly?")

    assert trace["tools_used"] == []
    assert trace["errors"] == []
    assert "could not route" in trace["answer"].lower()


def test_unknown_tool_is_handled_gracefully():
    result = execute_tool("not_a_tool", "Use an unknown tool.")

    assert result["tool"] == "not_a_tool"
    assert result["result"] is None
    assert result["error"] == "Unknown tool requested: not_a_tool"


def test_iteration_limit_is_enforced(monkeypatch):
    import agent.graph as graph

    monkeypatch.setattr(graph, "MAX_ITERATIONS", 0)
    trace = graph.run_agent_with_trace("What is revenue by region?")

    assert trace["iterations"] == 0
    assert trace["errors"] == ["Iteration limit reached before completion."]
    assert "iteration limit" in trace["answer"].lower()
