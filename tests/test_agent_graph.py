import inspect

from agent.graph import (
    GENERIC_TOOL_FAILURE_MESSAGE,
    MAX_TOOL_CALLS,
    UNSUPPORTED_QUERY_MESSAGE,
    execute_tool,
    plan_tool_calls,
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
    assert isinstance(trace["parsed_intent"], dict)
    assert trace["parsed_intent"]["steps"][0]["intent_type"] == "analysis"
    assert trace["parsed_intent"]["steps"][0]["metric"] == "revenue"


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


def test_planner_returns_ordered_tool_chain_for_analysis_plus_chart():
    assert plan_tool_calls("Analyse EMEA Q3 softness and show a chart of revenue by region.") == [
        "analyse_data",
        "visualise",
    ]


def test_planner_still_handles_document_plus_forecast_with_parser():
    assert plan_tool_calls("Search the docs for EMEA risks and forecast revenue for next month") == [
        "search_documents",
        "forecast",
    ]


def test_run_agent_executes_analysis_plus_visualise_chain():
    trace = run_agent_with_trace("Analyse EMEA Q3 softness and show a chart of revenue by region.")

    assert trace["tools_used"] == ["analyse_data", "visualise"]
    assert "Step 1 (analyse_data):" in trace["answer"]
    assert "Step 2 (visualise):" in trace["answer"]


def test_lost_regions_query_routes_to_analysis_and_returns_calculation():
    trace = run_agent_with_trace("How much revenue can I get if LATAM and APAC are lost regions?")

    assert trace["tools_used"] == ["analyse_data"]
    assert "Revenue impact of lost or excluded regions" in trace["answer"]
    assert "Revenue lost / revenue at risk:" in trace["answer"]
    assert "Retained revenue:" in trace["answer"]
    assert "I can answer structured sales questions" not in trace["answer"]


def test_revenue_at_risk_query_routes_to_analysis_not_documents():
    trace = run_agent_with_trace("How much revenue is at risk if LATAM and APAC are lost?")

    assert trace["tools_used"] == ["analyse_data"]
    assert "Revenue lost / revenue at risk:" in trace["answer"]


def test_emea_q3_softness_plus_chart_returns_useful_tool_outputs():
    trace = run_agent_with_trace("Analyse EMEA Q3 softness and show a chart")

    assert trace["tools_used"] == ["analyse_data", "visualise"]
    assert "Step 1 (analyse_data):" in trace["answer"]
    assert "EMEA Q3 softness analysis" in trace["answer"]
    assert "Step 2 (visualise):" in trace["answer"]
    assert "EMEA Q2 vs Q3 revenue by sales channel chart saved to" in trace["answer"]
    assert "I can answer structured sales questions" not in trace["answer"]
    assert "I can create charts for revenue" not in trace["answer"]


def test_run_agent_executes_search_documents_plus_forecast_chain():
    trace = run_agent_with_trace(
        "Search the docs for EMEA risks and forecast revenue for next month."
    )

    assert trace["tools_used"] == ["search_documents", "forecast"]
    assert "Step 1 (search_documents):" in trace["answer"]
    assert "Step 2 (forecast):" in trace["answer"]


def test_run_agent_executes_search_documents_plus_analyse_data_chain():
    trace = run_agent_with_trace(
        "What does the product strategy say, and show top products by revenue?"
    )

    assert trace["tools_used"] == ["search_documents", "analyse_data"]
    assert "Step 1 (search_documents):" in trace["answer"]
    assert "Step 2 (analyse_data):" in trace["answer"]


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


def test_partial_failure_returns_partial_answer_without_sensitive_details(monkeypatch):
    import agent.graph as graph

    def failing_search(query):
        raise RuntimeError("secret-token-123 leaked")

    monkeypatch.setitem(graph.TOOL_REGISTRY, "search_documents", failing_search)
    trace = graph.run_agent_with_trace(
        "Search the docs for EMEA risks and forecast revenue for next month."
    )

    assert trace["tools_used"] == ["search_documents", "forecast"]
    assert "I completed part of your request" in trace["answer"]
    assert "secret-token-123" not in trace["answer"]
    assert any("secret-token-123" in error for error in trace["errors"])


def test_max_tool_call_limit_is_enforced(monkeypatch):
    import agent.graph as graph

    monkeypatch.setattr(
        graph,
        "plan_tool_calls",
        lambda _: [
            "analyse_data",
            "visualise",
            "search_documents",
            "forecast",
            "analyse_data",
            "visualise",
        ],
    )
    trace = graph.run_agent_with_trace("compound query")

    assert trace["iterations"] == MAX_TOOL_CALLS
    assert len(trace["tool_calls"]) == MAX_TOOL_CALLS
    assert len(trace["intermediate_outputs"]) == MAX_TOOL_CALLS
    assert "Tool call limit reached" in trace["errors"][0]


def test_iteration_limit_is_enforced(monkeypatch):
    import agent.graph as graph

    monkeypatch.setattr(graph, "MAX_ITERATIONS", 0)
    trace = graph.run_agent_with_trace("What is revenue by region?")

    assert trace["iterations"] == 0
    assert trace["errors"] == ["Iteration limit reached before completion."]
    assert "iteration limit" in trace["answer"].lower()


def test_agent_graph_source_does_not_use_eval_or_exec():
    import agent.graph as graph

    source = inspect.getsource(graph)
    assert "eval(" not in source
    assert "exec(" not in source
