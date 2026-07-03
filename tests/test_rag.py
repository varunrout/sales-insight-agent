import inspect

from config import DOCS_PATH, ROOT_DIR
from rag.ingest import chunk_text, ingest_documents, load_markdown_documents
from rag.retriever import format_search_results, retrieve_documents


def test_rag_modules_import_successfully():
    import rag.ingest as ingest
    import rag.retriever as retriever

    assert ingest.DEFAULT_CHUNK_SIZE > 0
    assert retriever.retrieve_documents


def test_load_markdown_documents_finds_docs():
    documents = load_markdown_documents(DOCS_PATH)

    assert len(documents) >= 3
    assert {path.name for path, _ in documents} >= {
        "market_overview.md",
        "product_strategy_brief.md",
        "quarterly_sales_report.md",
    }


def test_ingest_documents_returns_chunks_with_metadata():
    chunks = ingest_documents(DOCS_PATH, chunk_size=500, chunk_overlap=80)

    assert chunks
    assert {chunk.source for chunk in chunks} >= {
        "market_overview.md",
        "product_strategy_brief.md",
        "quarterly_sales_report.md",
    }
    assert all(chunk.chunk_id for chunk in chunks)
    assert all(chunk.text for chunk in chunks)
    assert all(chunk.metadata["source_path"] for chunk in chunks)


def test_chunk_text_is_deterministic_and_overlapping():
    text = " ".join(f"sentence {index}." for index in range(100))

    first = chunk_text(text, chunk_size=120, chunk_overlap=30)
    second = chunk_text(text, chunk_size=120, chunk_overlap=30)

    assert first == second
    assert len(first) > 1


def test_retrieve_documents_returns_relevant_market_risk_doc():
    results = retrieve_documents("EMEA Partner Q3 risk", top_k=2)

    assert results
    assert results[0].score > 0
    assert results[0].source in {
        "market_overview.md",
        "quarterly_sales_report.md",
    }
    assert "EMEA" in results[0].text


def test_retrieve_documents_returns_relevant_product_strategy_doc():
    results = retrieve_documents("product margin strategy enterprise discounting", top_k=1)

    assert len(results) == 1
    assert results[0].source == "product_strategy_brief.md"


def test_retrieve_documents_respects_top_k_and_score_order():
    results = retrieve_documents("regional pricing channel risk", top_k=2)

    assert len(results) <= 2
    assert results == sorted(results, key=lambda result: (-result.score, result.source, result.chunk_id))


def test_retrieve_documents_handles_empty_query():
    assert retrieve_documents("", top_k=3) == []


def test_retrieve_documents_handles_missing_docs_path():
    missing_path = ROOT_DIR / "data" / "_missing_docs_for_test"

    assert load_markdown_documents(missing_path) == []
    assert ingest_documents(missing_path) == []
    assert retrieve_documents("EMEA risk", docs_path=missing_path) == []


def test_format_search_results_is_human_readable():
    results = retrieve_documents("market overview EMEA", top_k=1)
    formatted = format_search_results(results)

    assert "Top document matches:" in formatted
    assert results[0].source in formatted


def test_no_eval_or_exec_used():
    import rag.ingest as ingest
    import rag.retriever as retriever

    source = inspect.getsource(ingest) + inspect.getsource(retriever)

    assert "eval(" not in source
    assert "exec(" not in source
