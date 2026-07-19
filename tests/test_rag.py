import inspect

from config import DOCS_PATH, ROOT_DIR
from rag.ingest import chunk_text, ingest_documents, load_markdown_documents
from rag.retriever import format_search_results, retrieve_documents
from rag.vector_store import MIN_SIMILARITY


def test_rag_modules_import_successfully():
    import rag.ingest as ingest
    import rag.retriever as retriever
    import rag.vector_store as vector_store

    assert ingest.DEFAULT_CHUNK_SIZE > 0
    assert retriever.retrieve_documents
    assert vector_store.get_collection


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


def test_chunk_text_terminates_when_overlap_would_prevent_progress():
    text = "alpha beta gamma. ## Next section with enough text to continue safely."

    chunks = chunk_text(text, chunk_size=24, chunk_overlap=23)

    assert chunks
    assert len(chunks) < len(text)


def test_chunk_text_terminates_for_url_like_text_with_large_overlap():
    text = "https://example.com/" + ("commercialsalesinsight" * 5)

    chunks = chunk_text(text, chunk_size=24, chunk_overlap=23)

    assert chunks
    assert len(chunks) <= len(text)
    assert len(set(chunks)) > 1


def test_chunk_text_splits_before_markdown_header_boundary():
    text = "Intro sentence with enough text before header. ## Regional outlook follows."

    chunks = chunk_text(text, chunk_size=50, chunk_overlap=0)

    assert len(chunks) > 1
    assert chunks[0].endswith("header.")
    assert chunks[1].startswith("## Regional")
    assert all(not chunk.endswith("#") for chunk in chunks)


def test_retrieve_documents_returns_relevant_market_risk_doc():
    results = retrieve_documents("EMEA Partner Q3 risk", top_k=2)

    assert results
    assert results[0].score >= MIN_SIMILARITY
    assert results[0].source in {
        "market_overview.md",
        "quarterly_sales_report.md",
    }


def test_retrieve_documents_matches_on_meaning_not_shared_tokens():
    # No token overlap with "Q3 revenue softness"; only an embedding retriever
    # can connect "dip in the third quarter" to the quarterly report chunk.
    results = retrieve_documents("why did EMEA sales dip in the third quarter", top_k=1)

    assert len(results) == 1
    assert results[0].source == "quarterly_sales_report.md"
    assert results[0].score >= MIN_SIMILARITY


def test_retrieve_documents_returns_relevant_product_strategy_doc():
    results = retrieve_documents("product margin strategy enterprise discounting", top_k=1)

    assert len(results) == 1
    assert results[0].source == "product_strategy_brief.md"


def test_retrieve_documents_respects_top_k_and_score_order():
    results = retrieve_documents("regional pricing channel risk", top_k=2)

    assert 0 < len(results) <= 2
    assert results == sorted(
        results, key=lambda result: (-result.score, result.source, result.chunk_id)
    )


def test_retrieve_documents_below_threshold_returns_nothing():
    assert retrieve_documents("xylophone nebula marmalade", top_k=3) == []


def test_retrieve_documents_handles_empty_query():
    assert retrieve_documents("", top_k=3) == []


def test_retrieve_documents_rejects_non_positive_top_k():
    assert retrieve_documents("EMEA risk", top_k=0) == []


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


def test_format_search_results_handles_empty():
    assert format_search_results([]) == "No matching documents found."


def test_no_eval_or_exec_used():
    import rag.ingest as ingest
    import rag.retriever as retriever
    import rag.vector_store as vector_store

    source = (
        inspect.getsource(ingest) + inspect.getsource(retriever) + inspect.getsource(vector_store)
    )

    assert "eval(" not in source
    assert "exec(" not in source
