# sales-insight-agent project plan

## Purpose

This document turns the issue backlog into an orderly implementation plan for `sales-insight-agent`.

The repo is intended to become a portfolio-grade agentic AI assistant for commercial sales analytics. The finished system should let a user ask natural-language business questions and have the agent decide whether to:

- analyse structured sales data
- forecast future metrics
- create a chart
- search business documents
- combine multiple tools in sequence

The work should be delivered in dependency-safe PRs so every stage leaves the repository in a runnable, testable state.

## Current repo reading

The current README is a short placeholder. The real project specification is contained in Issues #1 to #10.

The issues define a strong target architecture:

```text
User -> Streamlit UI -> LangGraph Agent -> Tool Router
                                      -> analyse_data
                                      -> forecast
                                      -> visualise
                                      -> search_documents
```

The system has four core tools:

```text
analyse_data       structured sales analysis over CSV data
forecast           scikit-learn gradient-boosting time-series forecasting
visualise          Plotly chart generation
search_documents   RAG-backed document retrieval
```

The final product layer is:

```text
Streamlit chat UI
README
architecture diagram
demo notebook
```

## Work-order principles

Use these principles while implementing the issues.

### 1. Build thin vertical foundations before deep features

Do not start with the most impressive feature. First make the repo installable, runnable and testable. Then make the agent call stub tools. Then replace stubs with real tools one by one.

### 2. Keep the agent honest

The agent should not pretend to know things it has not retrieved or calculated. Tool outputs should be passed back into the final answer, and failures should return useful messages rather than stack traces.

### 3. Prefer safe analytical functions over arbitrary code execution

Issue #3 suggests LLM-generated pandas operations. That is useful but risky. The safer implementation path is to expose controlled analytical operations and let the LLM map user intent to those operations. This keeps the portfolio project robust and easier to explain.

### 4. Make the dataset business-realistic

The sample data should be synthetic, but it should feel like a commercial sales dataset. It needs enough dimensions to support interesting analysis, charts and forecasts.

Recommended columns:

```text
date
region
country
product_category
product_name
sales_channel
customer_segment
revenue
units_sold
new_customers
discount_rate
gross_margin
order_id
```

### 5. Make RAG useful, not decorative

The documents in `data/docs/` should contain information that is not already in the CSV. That lets the final agent combine quantitative and qualitative evidence.

Example:

```text
CSV: EMEA revenue declined in Q3.
Document: EMEA decline was linked to delayed enterprise renewals, pricing pressure and lower conversion from outbound campaigns.
```

### 6. Every PR should have an acceptance gate

A PR is not done because files exist. It is done when there is a command, test or example query proving the feature works.

## Dependency graph

```text
Issue #1
  -> Issue #2
      -> Issue #3
      -> Issue #5
      -> Issue #4
      -> Issue #6
          -> Issue #7
              -> Issue #8
                  -> Issue #9
                      -> Issue #10
```

More practically:

```text
Foundation
  -> Agent skeleton
      -> Structured data tool
      -> Visualisation tool
      -> Forecasting tool
      -> RAG backend
          -> RAG tool
              -> Multi-step reasoning
                  -> Streamlit UI
                      -> Final README and demo notebook
```

## Recommended PR sequence

| PR | Issues | Theme | Why this order |
|---:|---|---|---|
| PR 1 | #1 | Repo foundation | Everything depends on folder structure, dependencies, config and sample data |
| PR 2 | #2 | LangGraph skeleton | Establishes the agent spine before real tool logic |
| PR 3 | #3 | Sales analysis tool | First real business capability |
| PR 4 | #5 | Visualisation tool | Makes sales analysis visible and prepares for UI rendering |
| PR 5 | #4 | Forecasting tool | Adds the strongest data science component after stable data exists |
| PR 6 | #6 | RAG ingestion and retriever | Creates document intelligence independently before agent wiring |
| PR 7 | #7 | Document search tool | Wires RAG into the agent as a callable tool |
| PR 8 | #8 | Multi-step reasoning | Requires all tools to exist first |
| PR 9 | #9 | Streamlit UI | Presents the working backend through a user interface |
| PR 10 | #10 | README, architecture and demo notebook | Final polish after the implementation is real |

## PR 1: Repo scaffolding and environment setup

Related issue: #1

### Goal

Set up the project foundation so every later issue can build cleanly.

### Scope

Create the folder structure, dependency list, environment template, config file and sample data contract.

### Deliverables

```text
agent/
tools/
rag/
data/
data/docs/
ui/
notebooks/
tests/
config.py
requirements.txt
.env.example
.gitignore
README.md
```

### Implementation details

Create `requirements.txt` with:

```text
langgraph
langchain
langchain-core
langchain-anthropic
chromadb
pandas
numpy
scikit-learn
streamlit
plotly
python-dotenv
scikit-learn
pytest
sentence-transformers
```

Create `.env.example` with the required Anthropic credential placeholder.

Create `.gitignore`:

```text
.env
.venv/
__pycache__/
.pytest_cache/
.ipynb_checkpoints/
rag/chroma_db/
outputs/
models/
*.pyc
```

Create `config.py` with shared paths and model settings:

```text
MODEL_NAME
MODEL_TEMPERATURE
DATA_PATH
DOCS_PATH
VECTOR_STORE_PATH
CHART_OUTPUT_PATH
MODEL_OUTPUT_PATH
```

Generate `data/sample_sales.csv` with realistic synthetic daily sales data.

Create `tests/test_data_contract.py` to verify:

- file exists
- required columns exist
- date column can be parsed
- numeric metric columns are numeric
- dataset has enough rows for trend and forecast tests

### Acceptance gate

```bash
pip install -r requirements.txt
pytest
```

### Do not include yet

- real LangGraph logic
- forecasting models
- RAG ingestion
- Streamlit app

### Suggested branch

```text
setup/repo-foundation
```

### Suggested commit message

```text
setup: scaffold sales insight agent repository
```

## PR 2: LangGraph agent skeleton

Related issue: #2

### Goal

Build the core agent graph that orchestrates tool use.

### Scope

Create a runnable LangGraph agent with stub tools. The purpose is to prove the control flow before implementing full business logic.

### Deliverables

```text
agent/state.py
agent/graph.py
agent/prompts.py
tools/analyse_data.py
tools/forecast.py
tools/visualise.py
tools/search_documents.py
tests/test_agent_graph.py
```

### Implementation details

Define `AgentState` with:

```text
messages
tool_calls
tool_results
iterations
final_answer
last_tools_used
errors
```

Create nodes:

```text
call_llm
execute_tools
should_continue
format_final_answer
```

Tool stubs should return predictable strings.

Example:

```text
analyse_data("What is total revenue?") -> "analyse_data stub response"
forecast("revenue", 4, "W") -> "forecast stub response"
visualise("bar", "revenue", "region") -> "visualise stub response"
search_documents("growth targets") -> "search_documents stub response"
```

Add an entry point:

```text
run_agent(query: str) -> str
```

Also expose a richer result for the UI later:

```text
run_agent_with_trace(query: str) -> dict
```

Suggested trace shape:

```text
answer
tools_used
iterations
intermediate_outputs
errors
```

### Acceptance gate

The following should run without errors:

```python
from agent.graph import run_agent

print(run_agent("What is total revenue?"))
```

Tests should confirm:

- graph compiles
- `run_agent` returns a string
- unknown tools are handled gracefully
- iteration limit exists, even if not fully used yet

### Do not include yet

- real pandas analysis
- real forecasting
- real RAG
- Streamlit UI

### Suggested branch

```text
agent/langgraph-skeleton
```

### Suggested commit message

```text
agent: add LangGraph skeleton with stub tools
```

## PR 3: Structured sales analysis tool

Related issue: #3

### Goal

Give the agent a real structured-data analysis capability.

### Scope

Implement `analyse_data` over `data/sample_sales.csv`.

### Deliverables

```text
tools/analyse_data.py
tests/test_analyse_data.py
```

### Recommended design

Use a controlled intent-based analytics layer rather than arbitrary LLM-generated pandas code.

Recommended functions:

```text
load_sales_data()
summarise_total_metric(metric)
group_metric_by_dimension(metric, dimension)
top_n_by_metric(metric, dimension, n)
monthly_trend(metric)
filter_data(date_range, region, category, channel, segment)
format_table(df)
```

The tool should support:

- total revenue
- revenue by region
- revenue by product category
- revenue by sales channel
- units sold by category
- new customers by channel
- top products by revenue
- top products by units sold
- month-over-month trend
- quarter-level filtering

### Example supported questions

```text
What is the total revenue by region?
Which 5 products have the highest sales volume this quarter?
Show me the month-over-month revenue trend.
Which sales channel generated the most revenue?
What is revenue by customer segment?
```

### Output format

Return markdown-friendly strings:

```text
Summary:
Total revenue was £X.

Breakdown:
| region | revenue |
|---|---:|
| North | £X |
| South | £Y |

Interpretation:
The North region contributed the largest share of revenue.
```

### Error handling

Return friendly responses for:

- unsupported metric
- unsupported dimension
- missing data
- invalid date range
- malformed query

Do not return raw stack traces.

### Acceptance gate

Tests should verify the three issue examples:

```text
"What is the total revenue by region?"
"Which 5 products have the highest sales volume this quarter?"
"Show me the month-over-month revenue trend"
```

Also test:

- invalid metric
- invalid dimension
- execution time below 3 seconds on sample data

### Suggested branch

```text
tools/analyse-data
```

### Suggested commit message

```text
tools: implement structured sales analysis
```

## PR 4: Visualisation tool

Related issue: #5

### Goal

Allow the agent to generate interactive charts on demand.

### Scope

Implement `visualise` using Plotly and save charts as HTML files.

### Deliverables

```text
tools/visualise.py
outputs/charts/
tests/test_visualise.py
```

### Implementation details

Function signature:

```text
visualise(chart_type: str, metric: str, group_by: str | None = None, title: str | None = None) -> str
```

Supported chart types:

```text
bar
line
scatter
pie
```

Recommended chart logic:

```text
bar     grouped metric by categorical dimension
line    metric over date or month
pie     metric share by category/channel/region
scatter relationship between two numeric fields
```

Recommended defaults:

```text
bar chart: revenue by region
line chart: revenue over time
pie chart: revenue by product_category
scatter chart: discount_rate vs revenue
```

The function should return:

```text
chart_path
short summary
```

Example:

```text
Created chart: outputs/charts/revenue_by_region.html

Summary:
Revenue is highest in the North region, followed by EMEA and South.
```

### Acceptance gate

Tests should verify:

- each supported chart type creates a valid `.html` file
- returned file path exists
- invalid chart types return friendly errors
- missing columns return friendly errors

### Suggested branch

```text
tools/visualise
```

### Suggested commit message

```text
tools: add Plotly visualisation tool
```

## PR 5: Forecasting tool

Related issue: #4

### Goal

Add a real data science capability through time-series forecasting.

### Scope

Implement `forecast` for key sales metrics using chronological validation and uncertainty bands.

### Deliverables

```text
tools/forecast.py
models/
tests/test_forecast.py
```

### Supported metrics

```text
revenue
units_sold
new_customers
```

### Feature engineering

Use the sales dataset aggregated to the requested frequency.

Features:

```text
lag_1
lag_7
lag_14
lag_28
rolling_mean_7
rolling_mean_14
rolling_mean_28
rolling_std_7
day_of_week
month
quarter
is_weekend
trend_index
```

For weekly or monthly forecasts, adapt lags to the aggregation grain.

### Modelling approach

Use scikit-learn's HistGradientBoostingRegressor with a chronological train/test split, compared against a seasonal-naive baseline on the same holdout.

Minimum output:

```text
forecast_period
p10
p50
p90
metric
frequency
validation_rmse
validation_mape
```

Uncertainty can be implemented through one of:

```text
quantile regression models
bootstrap residual bands
simple residual-based interval as a first pass
```

### Example supported questions

```text
Forecast revenue for the next 4 weeks.
What will units sold look like over the next quarter?
Forecast new customers for the next 30 days.
```

### Acceptance gate

Tests should verify:

- chronological split is respected
- no future data leakage
- output includes P10, P50 and P90
- cold-start run completes under 10 seconds
- invalid metric returns friendly error

### Suggested branch

```text
tools/forecasting
```

### Suggested commit message

```text
tools: add sales forecasting
```

## PR 6: RAG ingestion and retriever

Related issue: #6

### Goal

Build the document ingestion and retrieval layer that powers document search.

### Scope

Implement ChromaDB-backed retrieval over sample business documents.

### Deliverables

```text
rag/ingest.py
rag/retriever.py
data/docs/quarterly_sales_report.md
data/docs/product_strategy_brief.md
data/docs/market_overview.md
tests/test_retriever.py
```

### Sample document strategy

Documents should contain qualitative business context that is not in the CSV.

Recommended content:

```text
quarterly_sales_report.md
- revenue commentary
- region-level performance
- growth targets
- headcount cost notes
- risks and opportunities

product_strategy_brief.md
- product priorities
- margin pressure
- customer segment strategy
- channel investment

market_overview.md
- market risks
- competitor pressure
- pricing sensitivity
- regional demand trends
```

### Ingestion details

`rag/ingest.py` should:

- load PDF, TXT and Markdown from `data/docs/`
- chunk documents with chunk size 500 and overlap 50
- embed chunks using sentence-transformers or Anthropic embeddings
- persist vectors to `rag/chroma_db/`
- include metadata:
  - source filename
  - chunk index
  - character offset

### Retrieval details

`rag/retriever.py` should expose:

```text
retrieve(query: str, k: int = 5) -> list[dict]
```

Each result should include:

```text
text
source
score
chunk_index
```

### Acceptance gate

Run:

```bash
python -m rag.ingest
```

Then verify:

```python
from rag.retriever import retrieve

retrieve("What was said about EMEA risks?", k=5)
```

Tests should verify:

- ingestion runs without error
- vector store persists
- retrieval returns relevant chunks
- retrieval latency is reasonable for sample docs

### Suggested branch

```text
rag/ingestion-retrieval
```

### Suggested commit message

```text
rag: add document ingestion and retrieval
```

## PR 7: Document search tool

Related issue: #7

### Goal

Wire the RAG pipeline into the agent as `search_documents`.

### Scope

Implement `tools/search_documents.py` and register it with the LangGraph tool list.

### Deliverables

```text
tools/search_documents.py
tests/test_search_documents.py
```

### Implementation details

Function signature:

```text
search_documents(query: str, k: int = 5) -> str
```

It should call:

```text
rag.retriever.retrieve(query, k)
```

Format output with:

```text
source document
relevance score
confidence label
short text snippet
```

Confidence bands:

```text
score >= 0.70  high confidence
score >= 0.40  medium confidence
score < 0.40   low confidence
```

Low-confidence results should be flagged or filtered.

### Example supported questions

```text
What does the quarterly report say about headcount costs?
Find any mentions of the EMEA region in our sales documents.
What were the key risks highlighted in the market overview?
```

### Acceptance gate

Tests should verify:

- returns formatted source-attributed results
- filters or flags weak matches
- handles empty vector store clearly
- agent can route document questions to this tool

### Suggested branch

```text
tools/search-documents
```

### Suggested commit message

```text
tools: connect document search to RAG retriever
```

## PR 8: Multi-step reasoning and self-correction

Related issue: #8

### Goal

Make the agent handle complex questions that require multiple tools.

### Scope

Update the LangGraph graph to support tool chaining, retries, reflection and partial answers.

### Deliverables

```text
agent/graph.py
agent/router.py
agent/reflection.py
tests/test_multistep_agent.py
```

### Capabilities

Add:

```text
iteration limit of 5 tool calls per query
tool result memory
tool retry up to 2 times
reflection check after tool execution
partial answer on timeout
clear trace of tools used
```

### Example query 1

```text
Compare last quarter's revenue to the forecast, then show me a chart of the gap.
```

Expected flow:

```text
analyse_data -> forecast -> visualise -> final answer
```

### Example query 2

```text
Find what the sales report says about EMEA, then pull the actual numbers for that region.
```

Expected flow:

```text
search_documents -> analyse_data -> final answer
```

### Self-correction behaviour

If a tool returns an error, the agent should retry with a corrected input.

Example:

```text
Tool error: unsupported metric "sales"
Retry: use metric "revenue"
```

### Acceptance gate

Tests should verify:

- multi-step query uses at least 2 tools
- iteration limit is respected
- self-correction fires on simulated tool error
- timeout returns a partial answer rather than crashing
- final answer references actual tool outputs

### Suggested branch

```text
agent/multistep-reasoning
```

### Suggested commit message

```text
agent: add multi-step reasoning and self-correction
```

## PR 9: Streamlit chat UI

Related issue: #9

### Goal

Create the user-facing interface for the agent.

### Scope

Build a clean Streamlit chat app that exposes the agent to non-technical users.

### Deliverables

```text
ui/app.py
tests/test_ui_smoke.py
```

### UI requirements

Main panel:

```text
chat message history
user input with st.chat_input
assistant responses as markdown
spinner while agent runs
inline Plotly chart rendering
```

Sidebar:

```text
tools used in the last query
dataset row count
dataset date range
available columns
clear conversation button
```

### Chart rendering

The UI should detect `.html` chart paths returned by the `visualise` tool and render them using Streamlit HTML components.

### Acceptance gate

Run the Streamlit app from the repo root and manually test:

```text
Ask: Show me a bar chart of revenue by region.
Expected: agent response plus inline chart.
```

Also verify:

- conversation history persists during the session
- clear conversation button works
- sidebar updates with tools used
- dataset info displays correctly

### Suggested branch

```text
ui/streamlit-chat
```

### Suggested commit message

```text
ui: add Streamlit chat interface
```

## PR 10: README, architecture diagram and demo notebook

Related issue: #10

### Goal

Package the completed project so it tells a clear portfolio story.

### Scope

Finalize README, architecture diagram and demo notebook after the product works.

### Deliverables

```text
README.md
notebooks/demo.ipynb
```

### README requirements

The final README should include:

```text
one-line description
problem statement
solution overview
architecture diagram
feature list
tech stack
quick start
example queries
folder structure
implementation roadmap
future improvements
```

The architecture diagram should be embedded as Mermaid.

### Demo notebook requirements

Create `notebooks/demo.ipynb` with five examples:

```text
1. Simple data query: What is total revenue by region?
2. Forecast: Forecast revenue for the next 4 weeks.
3. Chart: Show a bar chart of units sold by product category.
4. Document search: What does the quarterly report say about growth targets?
5. Multi-step: Compare actual vs forecast revenue, then chart the difference.
```

Each section should show:

```text
input query
tools used
intermediate output
final answer
```

### Acceptance gate

Verify:

- README renders correctly on GitHub
- Mermaid diagram renders
- notebook runs top-to-bottom
- example queries match implemented capabilities
- no broken links or fake screenshots

### Suggested branch

```text
docs/final-readme-demo
```

### Suggested commit message

```text
docs: finalize README and demo notebook
```

## Definition of done for the whole project

The project is complete when the local setup, tests, RAG ingestion and Streamlit app all run successfully.

The final app should support these queries:

```text
What is total revenue by region?
Which products generated the most revenue this quarter?
Forecast revenue for the next 4 weeks.
Show me a line chart of monthly revenue.
What does the quarterly report say about EMEA risks?
Compare actual revenue to forecast revenue and chart the gap.
```

The final README should allow a reviewer to understand:

- what the project does
- why it matters commercially
- how the agent works
- what tools are available
- how to run the project
- what the project demonstrates about data science and agentic AI

## Future improvements after Issue #10

After the current issue set is complete, good extensions would be:

### 1. SQL backend

Replace or supplement the CSV with SQLite or DuckDB.

Why it helps:

```text
Makes the project feel closer to real analytics workflows.
```

### 2. Evaluation suite

Add a small benchmark of natural-language questions and expected tool routes.

Why it helps:

```text
Shows discipline around agent reliability.
```

### 3. Authentication and deployment

Deploy the Streamlit app with environment variables and secrets management.

Why it helps:

```text
Turns the repo from a local demo into a shareable product.
```

### 4. Cost and latency tracking

Log LLM calls, tool latency and total response time.

Why it helps:

```text
Shows production awareness.
```

### 5. Business insight cards

Have the final answer include a structured insight card:

```text
finding
evidence
recommendation
confidence
next question to ask
```

Why it helps:

```text
Makes outputs more decision-ready for commercial users.
```

## Recommended first Codex instruction

Use this for the first implementation PR:

```text
Implement PR 1 for varunrout/sales-insight-agent.

Scope:
- Complete repo scaffolding from Issue #1.
- Add project folders: agent, tools, rag, data, data/docs, ui, notebooks and tests.
- Add requirements.txt with required packages.
- Add .env.example with the required Anthropic API credential placeholder.
- Add .gitignore excluding .env, __pycache__, .pytest_cache, rag/chroma_db, outputs and models.
- Add config.py with shared settings for model name, temperature, data paths and vector store path.
- Generate a realistic synthetic sales dataset at data/sample_sales.csv with daily sales rows across regions, product categories, channels, customer segments, revenue, units_sold and new_customers.
- Keep README aligned with the roadmap but do not mark unbuilt features as complete.
- Add tests/test_data_contract.py that verifies the sample dataset exists and has required columns.

Acceptance:
- pip install -r requirements.txt works.
- pytest runs successfully.
- Folder structure matches Issue #1.
```

## Final positioning

The final project should be positioned as:

```text
A portfolio-grade agentic AI sales analytics assistant that turns sales data and business documents into analysis, forecasts, charts and decision-ready answers through a Streamlit chat interface.
```

The important thing is to avoid making it feel like a generic chatbot. It should feel like a commercial analytics product with clear data science, agentic reasoning, retrieval and UI layers.
