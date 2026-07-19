# Retrieval similarity threshold

The document retriever (`rag/retriever.py`) embeds each query with
`all-MiniLM-L6-v2` (via Chroma's default ONNX embedding function) and ranks the
document chunks by cosine similarity. Because a nearest-neighbour search always
returns *something*, a query about nothing in the corpus would otherwise return
the least-bad chunk. To avoid that, results below a similarity floor
(`MIN_SIMILARITY`) are dropped and the tool reports "no matching documents".

## Calibration

Measured against the shipped corpus (`data/docs`, 15 chunks), top-1 cosine
similarity for genuine vs. off-topic queries:

| Query | Top-1 similarity | On topic |
|---|---|---|
| regional pricing channel risk | 0.627 | yes |
| product margin strategy enterprise discounting | 0.640 | yes |
| market overview EMEA | 0.576 | yes |
| why did EMEA sales dip in the third quarter | 0.587 | yes |
| EMEA Partner Q3 risk | 0.543 | yes |
| product strategy | 0.434 | yes |
| EMEA Q3 softness | 0.377 | yes |
| Q3 | 0.264 | yes |
| the and for | 0.146 | no |
| asdkfj qwerty zzz | 0.122 | no |
| xylophone nebula marmalade | 0.097 | no |

Genuine queries score >= 0.26; off-topic queries score <= 0.15. The threshold is
set to **0.20**, which separates the two groups with margin. It is a single
tunable constant (`rag.vector_store.MIN_SIMILARITY`); raise it to be stricter.

## Why embeddings over lexical overlap

The previous retriever scored by token overlap, so it could only match a query
to a chunk that reused its words. The embedding retriever matches on meaning:
"why did EMEA sales dip in the third quarter" retrieves the "EMEA Q3 revenue
softness" chunk (similarity 0.587) despite sharing almost no literal tokens
("dip" vs "softness", "third quarter" vs "Q3"), which the lexical scorer scored
at zero.
