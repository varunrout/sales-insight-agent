# Demo script (5-10 minutes)

Use this flow for recruiter/interviewer walkthroughs.

## 1) Start the app

```bash
streamlit run ui/app.py
```

Explain that the app is local-first and deterministic, and currently does not call an LLM.

## 2) Ask: revenue by region

Prompt:

`What is revenue by region?`

Narrate that this is routed to `analyse_data` and returns a structured summary.

## 3) Ask: chart question

Prompt:

`Show a chart of revenue by sales channel.`

Narrate that the chart is generated as local HTML and rendered in-app (with file fallback if needed).

## 4) Ask: document question

Prompt:

`What does the market overview say about EMEA?`

Narrate that this hits `search_documents` over sample business docs.

## 5) Ask: forecast question

Prompt:

`Forecast revenue for the next month.`

Narrate that forecasting runs over the synthetic sales dataset and returns forecast rows.

## 6) Ask: multi-step compound question

Prompt:

`Search the docs for EMEA risks and forecast revenue for next month.`

Narrate that the deterministic planner chains tools in sequence for one answer.

Optional second compound prompt:

`Analyse EMEA Q3 softness and show a chart of revenue by region.`

## 7) Show trace and intermediate outputs

For one or two responses, open:

- **Tools used**
- **Intermediate outputs** expander
- **Errors** expander (if present)

Highlight transparent, inspectable execution rather than black-box responses.
