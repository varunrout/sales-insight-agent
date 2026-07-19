# Architecture

This document describes the current deterministic, local-first architecture of `sales-insight-agent`.

## System view

```mermaid
flowchart TD
    U[User] --> UI[Streamlit UI ui/app.py]
    UI --> AG[run_agent_with_trace]
    AG --> PL[Deterministic keyword planner]
    PL --> T1[analyse_data]
    PL --> T2[forecast]
    PL --> T3[visualise]
    PL --> T4[search_documents]

    T1 --> DS[data/sample_sales.csv]
    T2 --> DS
    T3 --> DS
    T3 --> CH[outputs/charts/*.html]

    T4 --> RR[Embedding retriever]
    RR --> VS[Chroma vector store rag/chroma_db]
    VS --> DOCS[data/docs/*.md]

    T1 --> R[Trace + final answer]
    T2 --> R
    T3 --> R
    T4 --> R
    R --> UI
```

## Runtime flow

1. Streamlit receives a user question via `st.chat_input`.
2. UI calls `run_agent_with_trace(query)`.
3. The deterministic planner selects an ordered tool list from:
   - `analyse_data`
   - `forecast`
   - `visualise`
   - `search_documents`
4. Tools execute sequentially (bounded by iteration and tool-call limits).
5. A trace object is returned with:
   - `answer`
   - `tools_used`
   - `intermediate_outputs`
   - `errors`
   - `iterations`
6. UI renders final answer, trace details, and chart HTML output when present.

## Data boundaries

- Structured analytics and forecasting use `data/sample_sales.csv`.
- Document retrieval embeds the business documents under `data/docs` with `all-MiniLM-L6-v2` and stores them in a persistent Chroma vector store at `rag/chroma_db`. Queries are answered by cosine nearest-neighbour search with a calibrated similarity floor (see `docs/modeling/retrieval_threshold.md`); this is semantic retrieval, not token overlap.
- Charts are generated to local files under `outputs/charts`.

## Design constraints

- Deterministic keyword routing for repeatable outputs (no LLM in the run path).
- Local-first operation.
- The embedding model is downloaded and cached on first use; the vector store is built by `python -m scripts.build_vector_store` and is gitignored.
