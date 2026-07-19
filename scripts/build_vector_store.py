"""Build (or rebuild) the persistent Chroma vector store for the shipped docs.

Run once after cloning, or whenever the documents change:

    python -m scripts.build_vector_store

The index is written to ``config.VECTOR_STORE_PATH`` and is gitignored; it is
rebuilt deterministically from ``data/docs``.
"""

from __future__ import annotations

from config import VECTOR_STORE_PATH
from rag.vector_store import get_collection


def main() -> None:
    collection = get_collection(rebuild=True)
    count = 0 if collection is None else collection.count()
    print(f"Built vector store at {VECTOR_STORE_PATH} with {count} chunks.")


if __name__ == "__main__":
    main()
