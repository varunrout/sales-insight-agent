# Data Foundation

## `sample_sales.csv`

`sample_sales.csv` is a realistic synthetic commercial sales dataset for the future sales insight agent. It contains 8,772 rows of daily sales records from 2024-01-01 through 2025-12-31.

The dataset grain is one daily record per region and sales channel, with product, country and customer segment attributes included on each row. It is designed to support later structured analysis, forecasting, visualisation and multi-step agent evaluation without requiring real customer data.

Key columns include:

- `date`
- `region`
- `country`
- `product_category`
- `product_name`
- `sales_channel`
- `customer_segment`
- `revenue`
- `units_sold`
- `new_customers`
- `discount_rate`
- `gross_margin`
- `order_count`
- `marketing_spend`
- `conversion_rate`
- `campaign_flag`
- `is_promo_period`

## Business Patterns

The synthetic data encodes several commercial patterns:

- North America is the highest-revenue and most stable region.
- EMEA has recurring Q3 softness linked to Partner channel weakness.
- APAC is the fastest-growing region but has lower blended margin.
- LATAM is smaller and more volatile.
- Direct channel has the strongest gross margin profile.
- Marketplace is promotion-sensitive and responds more sharply during campaign windows.
- Enterprise products have lower unit volume but higher average order value.

## Documents

The `data/docs` directory contains source documents for later document search and RAG work:

- `quarterly_sales_report.md` gives regional and channel performance commentary that aligns with the CSV trends.
- `product_strategy_brief.md` describes product portfolio positioning, margin strategy and promotion guidance.
- `market_overview.md` covers regional outlook, pricing risk and channel risk.

## Sample Questions

`sample_questions.json` contains example questions with expected future tool routes. These questions will be used later to evaluate routing behavior across structured analysis, forecasting, visualisation, document search and multi-step workflows.
