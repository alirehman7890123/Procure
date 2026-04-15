# Service Layer Plan

This project is ready to move core business logic out of UI widgets and into reusable service modules.

## Goals

- Make core pharmacy rules testable without opening screens
- Reduce duplication between Sales, Purchase, GRN, Returns, and Reports
- Centralize database-heavy business flows
- Improve reliability on client systems

## Priority Order

1. Sales pricing/defaults service
- Resolve sales discount/tax policies
- Resolve global promo/global tax defaults
- Resolve customer header pricing defaults
- Keep UI focused on rendering and user interaction

2. Sales posting service
- Validate sales header
- Validate sale rows
- Insert sales header
- Insert sales items
- Allocate FIFO batches
- Insert customer transaction
- Return a structured result for UI and PDF/export flows

3. Purchase posting service
- Validate purchase header
- Validate purchase rows
- Save purchase header
- Save purchase items
- Create stock batches
- Post supplier transaction

4. GRN posting service
- Validate PO receipt rows
- Save GRN
- Save GRN billing/purchase bill
- Create stock batches
- Update PO status

5. Purchase order service
- Validate PO header
- Validate PO rows
- Save purchase order header
- Save purchase order lines
- Centralize low-stock/reorder helpers

6. Return services
- Sales return settlement and customer transaction rules
- Purchase return settlement and supplier transaction rules
- Return item validation and stock reversal helpers

7. Pricing rules service
- Shared discount/tax calculators
- Header/line allocation helpers
- Purchase landing-cost distribution helpers

8. Inventory movement service
- Batch in/out posting
- Opening stock corrections
- FIFO helpers
- Cost backfill helpers
- Stock integrity checks

9. Accounting settings service
- Global discount/tax settings
- Theme settings
- Shared accounting/policy reads and writes

10. Reports service
- Profit/loss aggregation
- Stock valuation aggregation
- Unknown-cost reconciliation
- Tax/discount audit summaries

## Guardrails

- UI widgets should not own business rules
- Services may use Qt SQL initially, but should avoid UI dependencies
- New services should return plain dictionaries/results
- Every extraction should leave the app working before the next one starts
- Add tests around pure helpers and critical posting flows as modules stabilize

## Current Status

### Implemented Service Modules

- `services/sales_defaults_service.py`
- `services/sales_posting_service.py`
- `services/sales_items_service.py`
- `services/sales_transaction_service.py`
- `services/purchase_posting_service.py`
- `services/purchase_items_service.py`
- `services/purchase_transaction_service.py`
- `services/grn_posting_service.py`
- `services/grn_transaction_service.py`
- `services/purchase_order_service.py`
- `services/inventory_movement_service.py`
- `services/stock_adjustment_service.py`
- `services/accounting_settings_service.py`
- `services/product_catalog_service.py`
- `services/product_admin_service.py`
- `services/sales_return_service.py`
- `services/sales_return_transaction_service.py`
- `services/purchase_return_service.py`
- `services/purchase_return_transaction_service.py`

### Wired Screens

- `sales/createsales.py`
- `purchase/addpurchase.py`
- `purchase/create_grn.py`
- `purchase/add_po.py`
- `salesreturn/create_sales_return.py`
- `purchasereturn/create_purchase_return.py`
- `product/productlist.py` (inventory adjustment flow)
- `product/productlist.py` (inventory adjustment flow and catalog browse/search/stock alert reads)
- `product/productlist.py` (inventory adjustment, catalog browse/search, and price/admin helpers)
- `reports/mainpage.py` (report readers and selector/chart data progressively delegating to report service)
- `business/discount_settings.py`
- `business/tax_settings.py`
- `business/theme_settings.py`
- `utilities/app_theme.py`

### Verification Coverage In Place

- Pure service tests for Sales, Purchase, GRN, PO, Returns, Inventory Movement, Stock Adjustment, and Accounting Settings
- SQLite-backed backend integration coverage for:
  - Sales
  - Purchase
  - GRN
  - Purchase Order
  - Sales Return
  - Purchase Return
  - Inventory Adjustment
  - Product Catalog query behavior
  - Product Admin price-change behavior
- Current backend safety net: growing SQLite-backed integration plus service-level verification across transactional, inventory, reporting, and product-admin slices

### What Is Effectively Done

- Sales service extraction: pricing defaults, posting math, item normalization, transaction persistence
- Purchase service extraction: posting math, item normalization, transaction persistence
- GRN service extraction: receipt posting, billing normalization, transaction helpers
- Purchase Order service extraction: header/line normalization, low-stock helpers, persistence helpers
- Inventory movement extraction: shared batch lookup/update, FIFO stock access, sold-batch helpers, and return-side stock restoration
- Stock adjustment extraction: row normalization, adjustment posting, batch quantity updates, product/batch loading, and audit-note shaping
- Product catalog extraction: low-stock/expired readers, barcode lookup, paginated browse listing, and search listing
- Product admin extraction: manufacturer lookup, auth user resolution, and price-change product search/update helpers
- Accounting settings extraction: shared `accounting_settings` reads/writes for sales policies, global promo/global tax, and theme settings
- Return service extraction: settlement rules, row normalization, transaction persistence, stock reversal/update helpers
- Reports cleanup in progress: batch reference details, opening-cost review, near-expiry, low-stock, outstanding-balance readers, chart helpers, business-name lookup, product option readers, and multiple reference-detail readers now delegate to `reports/report_service.py`
- `reports/mainpage.py` no longer owns direct SQL blocks for the extracted reporting slices; its remaining work is mostly rendering and orchestration
- Widget cleanup pass: major save flows now read more like orchestration than embedded business logic

### Next Recommended Workstreams

1. Inventory movement service
- Centralize shared batch in/out logic now duplicated across purchase, sales, GRN, and returns
- Move FIFO and stock restoration behavior behind one reusable module

2. Stock adjustment and audit workflows
- Add SQLite-backed integration coverage for inventory adjustment
- Strengthen inventory correction tooling for client-site safety
- Consider adjustment approval / supervisor flows if needed later

3. Accounting settings service
- Finish sweeping remaining direct `accounting_settings` reads/writes
- Keep Sales, theme/application startup, and Business settings aligned on one shared settings backend

4. Product and reports read services
- Continue moving product browsing, reference lookups, and inventory read models out of widgets
- Keep `product/productlist.py` and `reports/mainpage.py` on thin orchestration-only paths
- Continue shifting any remaining summary/read-model helpers into dedicated services before adding new report UI

5. Reports service
- Continue moving valuation, profit/loss, unknown-cost, reconciliation, and reference-detail logic out of report widgets

6. Broader failure-path testing
- Add more integration tests for invalid inputs, partial failures, repeated returns, and stock edge cases
- Keep expanding SQLite-backed coverage around newly extracted service domains before large new UI features land
- Keep adding lightweight guard tests for blank input, over-return, and impossible stock states so client-side failures are caught earlier

### Current Focus

- Keep thinning product, report, and stock-related widgets until they are mostly orchestration-only
- Finish the remaining accounting-settings and inventory/audit straggler reads so shared services fully own those domains
- Continue moving report-side summaries, chart feeds, and selector/read-model queries into `reports/report_service.py`
- Favor service-first additions for any new report screens or dashboard cards so `mainpage.py` stays thin
- Use the broadened integration suite as the baseline before each major service-layer expansion
