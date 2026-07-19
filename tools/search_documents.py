from rag.retriever import format_search_results, retrieve_documents

TOOL_NAME = "search_documents"


def search_documents(query: str) -> str:
    try:
        results = retrieve_documents(query)
    except Exception:
        return (
            "I could not search the document library right now. "
            "Please try again after the documents are available."
        )

    if not results:
        return "No matching documents found for that question."

    top = results[0]
    finding = (
        f"Finding: the closest evidence is {top.source} (relevance {top.score:.2f}); start there."
    )
    return f"Document search results for: {query}\n{format_search_results(results)}\n{finding}"
