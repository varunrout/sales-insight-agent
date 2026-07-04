import inspect

from agent.intent import parse_intent


def test_parse_revenue_by_region():
    parsed = parse_intent("What is revenue by region?")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.metric == "revenue"
    assert step.dimensions == ["region"]
    assert step.analysis_type == "breakdown"


def test_parse_sales_alias_by_channel():
    parsed = parse_intent("What is sales by channel?")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.metric == "revenue"
    assert step.dimensions == ["sales_channel"]


def test_parse_turnover_alias():
    parsed = parse_intent("Show turnover by region")
    step = parsed.steps[0]

    assert step.metric == "revenue"
    assert step.dimensions == ["region"]


def test_parse_region_exclusions():
    parsed = parse_intent("Revenue excluding LATAM and APAC")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.metric == "revenue"
    assert step.exclusions == {"region": ["APAC", "LATAM"]}
    assert step.analysis_type == "exclusion_impact"


def test_parse_emea_q3_softness():
    parsed = parse_intent("Analyse EMEA Q3 softness")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.filters == {"region": ["EMEA"]}
    assert step.comparison == "q3_vs_q2"
    assert step.analysis_type == "softness_diagnostic"


def test_parse_visualisation_request():
    parsed = parse_intent("Show a chart of revenue by sales channel")
    step = parsed.steps[0]

    assert step.intent_type == "visualisation"
    assert step.metric == "revenue"
    assert step.dimensions == ["sales_channel"]
    assert step.output_type == "chart"


def test_parse_forecast_request():
    parsed = parse_intent("Forecast revenue for next month")
    step = parsed.steps[0]

    assert step.intent_type == "forecast"
    assert step.metric == "revenue"
    assert step.output_type == "forecast"


def test_parse_document_request():
    parsed = parse_intent("What does the market overview say about EMEA?")
    step = parsed.steps[0]

    assert step.intent_type == "document_search"
    assert step.filters == {"region": ["EMEA"]}
    assert step.output_type == "document_evidence"


def test_parse_analysis_plus_chart_compound():
    parsed = parse_intent("Analyse EMEA Q3 softness and show a chart")

    assert parsed.is_compound is True
    assert [step.intent_type for step in parsed.steps] == ["analysis", "visualisation"]
    assert parsed.steps[0].analysis_type == "softness_diagnostic"
    assert parsed.steps[1].output_type == "chart"


def test_parse_document_plus_forecast_compound():
    parsed = parse_intent("Search the docs for EMEA risks and forecast revenue for next month")

    assert parsed.is_compound is True
    assert [step.intent_type for step in parsed.steps] == ["document_search", "forecast"]
    assert parsed.steps[0].filters == {"region": ["EMEA"]}
    assert parsed.steps[1].metric == "revenue"


def test_parse_exposure_as_risk_or_concentration():
    parsed = parse_intent("Where are we most exposed?")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.analysis_type == "concentration"


def test_parse_underperforming_channel():
    parsed = parse_intent("Which channel is underperforming?")
    step = parsed.steps[0]

    assert step.intent_type == "analysis"
    assert step.analysis_type == "underperformance"
    assert step.dimensions == ["sales_channel"]


def test_summarize_paragraph_does_not_parse_as_visualisation():
    parsed = parse_intent("Summarize this paragraph")
    step = parsed.steps[0]

    assert step.intent_type == "unsupported"
    assert step.output_type == "text"


def test_momentum_does_not_parse_as_month_over_month():
    parsed = parse_intent("Plot revenue momentum by region")
    step = parsed.steps[0]

    assert step.intent_type == "visualisation"
    assert step.metric == "revenue"
    assert step.dimensions == ["region"]
    assert step.comparison is None


def test_parsed_intent_serialises_to_dict():
    parsed = parse_intent("What is revenue by region?")
    payload = parsed.to_dict()

    assert payload["original_query"] == "What is revenue by region?"
    assert payload["steps"][0]["metric"] == "revenue"
    assert payload["is_compound"] is False


def test_intent_parser_does_not_use_eval_or_exec():
    import agent.intent as intent

    source = inspect.getsource(intent)

    assert "eval(" not in source
    assert "exec(" not in source
