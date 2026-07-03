from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

from config import DOCS_PATH
from rag.ingest import DocumentChunk, ingest_documents


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

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    chunks = ingest_documents(docs_path=docs_path)
    if not chunks:
        return []

    scored_results = [
        SearchResult(
            source=chunk.source,
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            score=_score_chunk(query, query_tokens, chunk),
        )
        for chunk in chunks
    ]
    matches = [result for result in scored_results if result.score > 0]
    return sorted(matches, key=lambda result: (-result.score, result.source, result.chunk_id))[
        :top_k
    ]


def format_search_results(results: list[SearchResult]) -> str:
    if not results:
        return "No matching documents found."

    lines = ["Top document matches:"]
    for result in results:
        snippet = result.text[:240].strip()
        if len(result.text) > len(snippet):
            snippet = f"{snippet}..."
        lines.append(
            f"- {result.source} ({result.chunk_id}, score {result.score:.2f}): "
            f"{snippet}"
        )
    return "\n".join(lines)


def _score_chunk(query: str, query_tokens: set[str], chunk: DocumentChunk) -> float:
    chunk_text = chunk.text.lower()
    chunk_token_counts = _token_counts(chunk_text)
    chunk_tokens = set(chunk_token_counts)
    if not chunk_tokens:
        return 0.0

    overlap = query_tokens & chunk_tokens
    if not overlap:
        return 0.0

    term_frequency = sum(chunk_token_counts[token] for token in overlap)
    overlap_score = len(overlap) / math.sqrt(len(query_tokens))
    phrase_score = 1.5 if query.lower().strip() in chunk_text else 0.0
    source_score = _source_name_score(query_tokens, chunk.source)
    return round(overlap_score + (term_frequency * 0.08) + phrase_score + source_score, 4)


def _source_name_score(query_tokens: set[str], source: str) -> float:
    source_tokens = _tokenize(Path(source).stem.replace("_", " "))
    return len(query_tokens & source_tokens) * 0.4


def _tokenize(text: str) -> set[str]:
    return set(_token_counts(text))


def _token_counts(text: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for token in re.findall(r"\b[a-z0-9]+\b", text.lower()):
        if len(token) <= 2 or token in _STOP_WORDS:
            continue
        counts[token] = counts.get(token, 0) + 1
    return counts


_STOP_WORDS = {
    "about",
    "and",
    "are",
    "for",
    "from",
    "has",
    "into",
    "not",
    "the",
    "this",
    "that",
    "what",
    "where",
    "with",
}
