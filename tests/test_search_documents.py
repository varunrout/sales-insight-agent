import inspect

from tools.search_documents import search_documents


def test_search_documents_imports_successfully():
    import tools.search_documents as search_tool

    assert search_tool.TOOL_NAME == "search_documents"
    assert search_tool.search_documents


def test_search_documents_returns_emea_q3_context():
    result = search_documents("EMEA Q3 softness")

    assert "Top document matches:" in result
    assert "EMEA" in result
    assert "Q3" in result
    assert "quarterly_sales_report.md" in result or "market_overview.md" in result


def test_search_documents_returns_product_strategy_context():
    result = search_documents("product strategy")

    assert "Top document matches:" in result
    assert "product_strategy_brief.md" in result


def test_search_documents_handles_no_match_gracefully():
    result = search_documents("xylophone nebula marmalade")

    assert result == "No matching documents found for that question."


def test_search_documents_handles_missing_docs_gracefully(monkeypatch):
    import tools.search_documents as search_tool

    def no_results(query):
        return []

    monkeypatch.setattr(search_tool, "retrieve_documents", no_results)

    result = search_tool.search_documents("EMEA Q3")

    assert result == "No matching documents found for that question."


def test_search_documents_hides_retriever_errors(monkeypatch):
    import tools.search_documents as search_tool

    def failing_retrieve(query):
        raise RuntimeError("sensitive stack trace details")

    monkeypatch.setattr(search_tool, "retrieve_documents", failing_retrieve)

    result = search_tool.search_documents("market overview")

    assert "could not search" in result
    assert "sensitive stack trace" not in result


def test_no_eval_or_exec_used():
    import tools.search_documents as search_tool

    source = inspect.getsource(search_tool)

    assert "eval(" not in source
    assert "exec(" not in source
