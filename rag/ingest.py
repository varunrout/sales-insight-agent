from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from config import DOCS_PATH


DEFAULT_CHUNK_SIZE = 900
DEFAULT_CHUNK_OVERLAP = 150


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    source: str
    text: str
    metadata: dict[str, str]


def load_markdown_documents(docs_path: Path = DOCS_PATH) -> list[tuple[Path, str]]:
    """Load markdown documents from the configured docs directory."""
    docs_dir = Path(docs_path)
    if not docs_dir.exists() or not docs_dir.is_dir():
        return []

    documents: list[tuple[Path, str]] = []
    for path in sorted(docs_dir.glob("*.md")):
        if path.is_file():
            text = path.read_text(encoding="utf-8").strip()
            if text:
                documents.append((path, text))
    return documents


def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    normalized = _normalize_whitespace(text)
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        previous_start = start
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            end = _nearest_boundary(normalized, start, end, chunk_overlap)

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(normalized):
            break
        start = max(0, end - chunk_overlap)
        if start <= previous_start:
            start = end

    return chunks


def ingest_documents(
    docs_path: Path = DOCS_PATH,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []
    for path, text in load_markdown_documents(docs_path):
        document_chunks = chunk_text(
            text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        for index, chunk in enumerate(document_chunks, start=1):
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{path.stem}-{index}",
                    source=path.name,
                    text=chunk,
                    metadata={
                        "source_path": str(path),
                        "chunk_index": str(index),
                    },
                )
            )
    return chunks


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _nearest_boundary(
    text: str,
    start: int,
    proposed_end: int,
    minimum_boundary: int,
) -> int:
    boundary_window = text[start:proposed_end]
    header_boundary = boundary_window.rfind("## ")
    if header_boundary > minimum_boundary:
        return start + header_boundary

    sentence_boundary = max(
        boundary_window.rfind(". "),
        boundary_window.rfind("? "),
        boundary_window.rfind("! "),
    )
    if sentence_boundary > minimum_boundary:
        return start + sentence_boundary + 1

    word_boundary = boundary_window.rfind(" ")
    if word_boundary > minimum_boundary:
        return start + word_boundary

    return proposed_end
