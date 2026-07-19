"""Semantic document retrieval over the Chroma vector store.

``retrieve_documents`` embeds the query and returns the nearest document
chunks by cosine similarity, filtered by ``MIN_SIMILARITY`` so that off-topic
queries return nothing rather than the least-bad match. The public shape
(``SearchResult``, ``retrieve_documents``, ``format_search_results``) is
unchanged from the previous lexical implementation, so downstream tools are
untouched.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from config import DOCS_PATH
from rag.vector_store import MIN_SIMILARITY, get_collection


@dataclass(frozen=True)
class SearchResult:
    source: str
    chunk_id: str
    text: str
    score: float


def retrieve_documents(
    query: str,
    top_k: int = 3,
    docs_path: Path = DOCS_PATH,
) -> list[SearchResult]:
    if top_k <= 0:
        return []
    if not query or not query.strip():
        return []

    collection = get_collection(docs_path=docs_path)
    if collection is None or collection.count() == 0:
        return []

    n_results = min(top_k, collection.count())
    response = collection.query(query_texts=[query], n_results=n_results)

    ids = response["ids"][0]
    documents = response["documents"][0]
    metadatas = response["metadatas"][0]
    distances = response["distances"][0]

    results: list[SearchResult] = []
    for chunk_id, text, metadata, distance in zip(
        ids, documents, metadatas, distances, strict=False
    ):
        similarity = 1.0 - float(distance)
        if similarity < MIN_SIMILARITY:
            continue
        results.append(
            SearchResult(
                source=str(metadata.get("source", "unknown")),
                chunk_id=str(metadata.get("chunk_id", chunk_id)),
                text=text,
                score=round(similarity, 4),
            )
        )

    results.sort(key=lambda result: (-result.score, result.source, result.chunk_id))
    return results


def format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "No matching documents found."

    lines = ["Top document matches:"]
    for result in results:
        snippet = result.text[:240].strip()
        if len(result.text) > len(snippet):
            snippet = f"{snippet}..."
        lines.append(f"- {result.source} ({result.chunk_id}, score {result.score:.2f}): {snippet}")
    return "\n".join(lines)
