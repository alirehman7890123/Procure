# Trend And Forecast Plan

This note defines a practical rollout path for sales and product trend analytics in `medic`.

The goal is not to ship "AI prediction" first. The goal is to ship reliable, explainable trend guidance that helps with:

- reorder planning
- seasonal item awareness
- sales direction visibility
- dashboard/report decision support

## Product Goal

Support two analytics scopes:

1. Business sales trend
   Shows how total sales move over time and where the short-term direction is heading.
2. Product demand trend
   Shows how one selected product is behaving over time, whether demand is rising/falling, and whether the item looks seasonal or volatile.

This should be presented as:

- trend
- moving average
- comparison
- forecast hint
- confidence / caution note

Not as guaranteed prediction.

## Recommended First Release

Ship the feature in 3 phases.

### Phase 1: Trend Analytics

Current implementation status:

- implemented on `reports/mainpage.py` inside the overview card as `Trend & Forecast`
- supports `Overall Sales` and `Product Trend`
- supports `30`, `60`, and `90` day ranges
- uses daily aggregation
- includes a rolling 7-day moving average
- includes previous-window comparison
- includes a short forecast badge
- includes a cautious product same-window-last-year note when history exists

Still deferred to later phases:

- weekly/monthly bucket switching
- longer `180` / `365` day views
- reorder suggestion wording
- fuller seasonal classification
- stockout-aware confidence reduction

Build:

- business sales trend chart
- selected product sales trend chart
- period selection: `7`, `30`, `60`, `90`, `180`, `365` days
- daily / weekly aggregation
- moving average overlay
- previous-window comparison

Output examples:

- `Sales up 12% vs previous 30 days`
- `Product demand stable in last 8 weeks`
- `Average daily units: 14.2`

### Phase 2: Forecast Hint

Current implementation status:

- forecast horizon selector for `7`, `14`, and `30` days
- weighted recent-average forecast with trend bias
- projected extension line on the chart
- forecast range / band display
- confidence label and caution note
- product reorder-cover suggestion note

Still deferred inside Phase 2:

- explicit forecast range wording in weeks / months for long horizons
- stockout-adjusted forecast confidence
- export/print formatting for the forecast panel

Build:

- short-term forecast extension for next `7`, `14`, `30` days
- weighted recent average
- trend-adjusted projection
- reorder suggestion note

Output examples:

- `Expected 95 to 110 units in next 14 days`
- `Suggested reorder cover: 3 weeks`

### Phase 3: Seasonal Detection

Current implementation status:

- same-window-last-year comparison is now blended into product trend notes
- repeating same-month spike detection uses up to 24 months of monthly product history
- product demand classification can now upgrade to `Seasonal`
- seasonal items reduce forecast certainty from the strongest confidence tier

Still deferred inside Phase 3:

- stockout-window detection to reduce confidence when sales history is demand-suppressed
- stronger quarter-level seasonality checks
- explicit seasonal watchlist across multiple products
- separate UI for monthly history drill-down

Build:

- same-month-last-year comparison
- repeating monthly spike detection
- classification:
  - `Stable`
  - `Rising`
  - `Declining`
  - `Volatile`
  - `Seasonal`
  - `Insufficient history`

Output examples:

- `Possible seasonal item: stronger demand seen in same quarter last year`
- `Demand spike likely not seasonal; recent short-term jump only`

## Data Sources

### Business Sales Trend

Use:

- `sales.creation_date`
- `sales.total`
- optionally `salesreturn.total` for net sales view

Base metrics:

- gross sales by day
- returns by day
- net sales by day
- invoice count by day
- average invoice value by day

### Product Demand Trend

Use:

- `salesitem.product_id`
- `salesitem.qty_sold`
- `sales.creation_date`
- default `price_pack.pack_size` for display conversions

Base metrics:

- units sold by day
- units sold by week
- revenue by day / week
- average daily units
- average weekly units

### Supporting Risk Signals

Use:

- `batch.quantity_remaining`
- `sold_batch`
- stock movement / stockout windows if available later

These are important because low sales during stockouts should not be treated as low demand.

## Query Layer

Add new read helpers to `reports/report_service.py`.

Recommended helpers:

### Business-Level Helpers

- `get_sales_trend_rows(days=30, metric="net_sales", bucket="day")`
- `get_sales_trend_summary(days=30)`
- `get_sales_previous_window_comparison(days=30)`
- `get_sales_forecast_hint(days=30, forecast_days=14)`

### Product-Level Helpers

- `get_product_trend_rows(product_id, days=90, bucket="day")`
- `get_product_trend_summary(product_id, days=90)`
- `get_product_previous_window_comparison(product_id, days=30)`
- `get_product_same_period_last_year(product_id, days=30)`
- `get_product_forecast_hint(product_id, lookback_days=90, forecast_days=14)`
- `classify_product_demand_pattern(product_id)`

### Seasonality Helpers

- `get_product_monthly_history(product_id, months=24)`
- `detect_product_seasonality(product_id, min_months=12)`

## Aggregation Strategy

Use simple aggregation rules first.

### Daily

Best for:

- `7`, `30`, `60`, `90` day views

### Weekly

Best for:

- `90`, `180`, `365` day product trend views
- smoothing noisy low-volume items

### Monthly

Best for:

- seasonality checks
- same-month-last-year comparisons

## Forecast Logic

Do not start with ML.

Use explainable methods first.

### Basic Forecast Formula

For short-term product forecast:

`forecast = 0.6 * avg(last_14_days) + 0.3 * avg(last_30_days) + 0.1 * avg(previous_same_weekday_pattern)`

For business sales:

`forecast = weighted_recent_average + trend_adjustment`

### Trend Adjustment

Compute a recent slope over the last 14 to 30 days.

If slope is:

- strongly positive: modestly lift forecast
- strongly negative: modestly reduce forecast
- flat: keep weighted average

Cap the trend effect so a short spike does not create absurd projections.

### Forecast Safety Rules

- do not forecast long horizons for low-history items
- cap growth / decline adjustment
- if sparse sales history, show low confidence
- if product was out of stock for much of the window, show caution

## Seasonality Detection

Seasonality should only be suggested when enough history exists.

### Minimum History

- less than `6 months`: no seasonality detection
- `6 to 11 months`: weak hints only
- `12+ months`: seasonal comparison allowed
- `18 to 24 months`: stronger seasonal classification

### Signals To Check

- repeated spikes in the same month or quarter
- same-month-last-year demand meaningfully above baseline
- recurring high variance with time-of-year pattern

### Simple First Rule

Mark as `Possible Seasonal` if:

- at least `12 months` history exists
- same month last year was materially above median monthly demand
- current period also shows elevated demand

Do not mark seasonal from one isolated spike.

## Demand Classification Rules

Suggested first version:

- `Stable`
  - low variance, flat slope
- `Rising`
  - positive slope, recent average above previous window
- `Declining`
  - negative slope, recent average below previous window
- `Volatile`
  - large week-to-week variance without stable seasonal pattern
- `Seasonal`
  - recurring same-period spikes with enough history
- `Insufficient history`
  - too few data points

## UI Options

### Option A: New Trend Report Page

Recommended long-term.

Create a report page with:

- scope selector:
  - `Overall Sales`
  - `Product Trend`
- product search box when `Product Trend` is selected
- range selector
- bucket selector: `Day / Week / Month`
- chart area
- summary badges
- forecast card
- seasonal note

This fits better in `reports/mainpage.py` than the dashboard.

### Option B: Dashboard Mini Widget

Good as a quick summary only.

Add:

- short sales trend chart
- one selected "watch product" trend
- badge text such as `Rising`, `Stable`, `Seasonal`

Use dashboard only for summary, not deep analysis.

### Recommended UX

Dashboard:

- summary trend
- top items
- optional "watch product"

Reports page:

- full trend and forecast interface

## Product Selection UX

For product trend:

- searchable product selector
- optional quick picks:
  - top sellers
  - low stock items
  - seasonal watchlist later

When a product is selected, show:

- historical demand chart
- sold units
- revenue
- moving average
- previous-window comparison
- forecast
- seasonality note

## Stockout Awareness

Raw sales are not always raw demand.

If the product was stocked out, low sales may mean:

- no stock available
- missed demand

So later phases should add:

- stockout flag on the chart
- `Forecast confidence reduced due to stockout periods`

This can begin as a caution note before full stockout-adjusted forecasting is added.

## Confidence Labels

Every forecast should include a confidence note.

Suggested rules:

- `High confidence`
  - enough history, low volatility, no major stockout distortion
- `Medium confidence`
  - decent history, some variability
- `Low confidence`
  - sparse history, erratic item, or stockout distortion

## Output Examples

### Overall Sales

- `Net sales up 9.4% vs previous 30 days`
- `7-day moving average: 42,850 PKR`
- `Projected next 14 days: 580k to 620k PKR`

### Product Trend

- `Average 12.6 units/day in last 30 days`
- `Demand rising vs previous window`
- `Possible seasonal item: winter-strength pattern`
- `Projected next 14 days: 175 to 190 units`

## Suggested Build Order

1. Add report-service daily and weekly sales trend queries
2. Add product-level trend query
3. Add moving average computation helper
4. Add previous-window comparison helper
5. Add basic forecast helper
6. Add first trend report UI
7. Add same-month-last-year comparison
8. Add seasonality classification
9. Add stockout caution note

## Recommended File Placement

Read logic:

- `reports/report_service.py`

UI:

- initially `reports/mainpage.py`
- later consider `features/dashboard/` or `features/reports/` if that feature is formalized

If the reporting area is later feature-migrated, this can become:

- `features/reports/services/trend_forecast_service.py`
- `features/reports/ui/trend_forecast_page.py`

## What Not To Do First

- no opaque ML model
- no long-horizon forecast for weak-history products
- no seasonality label with less than 12 months of history
- no confidence-free forecast number
- no dashboard overcrowding

## First Deliverable Recommendation

Build this first:

1. `Sales Trend & Forecast` report page
2. `Product Trend` mode on the same page
3. Range selector up to `90 days` for daily trend, `365 days` for weekly/monthly product views
4. Moving average
5. Previous-window comparison
6. Short forecast hint

That gives immediate value without overpromising.

## Success Criteria

This feature is successful when:

- users can quickly see whether sales are rising or falling
- users can inspect one product’s historical demand clearly
- seasonal items are flagged cautiously, not guessed wildly
- forecast output is understandable and explainable
- the feature helps reorder timing rather than confusing it
