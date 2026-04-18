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
- `services/sales_detail_service.py`
- `services/sales_return_service.py`
- `services/sales_return_transaction_service.py`
- `services/purchase_return_service.py`
- `services/purchase_return_transaction_service.py`
- `services/purchase_draft_service.py`
- `services/grn_draft_service.py`
- `reports/report_service.py`

### Wired Screens

- `sales/createsales.py`
- `sales/salesdetail.py`
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
- Current backend safety net: broad SQLite-backed integration plus service-level verification across transactional, inventory, reporting, product-admin, and settings slices

### What Is Effectively Done

- Sales service extraction: pricing defaults, posting math, item normalization, transaction persistence
- Purchase service extraction: posting math, item normalization, transaction persistence
- GRN service extraction: receipt posting, billing normalization, transaction helpers
- Draft recovery extraction: Purchase Invoice and GRN now autosave recoverable draft state without posting stock, balances, or invoices early
- Purchase Order service extraction: header/line normalization, low-stock helpers, persistence helpers
- Inventory movement extraction: shared batch lookup/update, FIFO stock access, sold-batch helpers, and return-side stock restoration
- Stock adjustment extraction: row normalization, adjustment posting, batch quantity updates, product/batch loading, and audit-note shaping
- Product catalog extraction: low-stock/expired readers, barcode lookup, paginated browse listing, and search listing
- Product admin extraction: manufacturer lookup, auth user resolution, and price-change product search/update helpers
- Sales detail extraction: receipt header/item/business reads and invoice export context now live in a dedicated read service
- Accounting settings extraction: shared `accounting_settings` reads/writes for sales policies, global promo/global tax, and theme settings
- Return service extraction: settlement rules, row normalization, transaction persistence, stock reversal/update helpers
- Reports service extraction in active progress: batch reference details, opening-cost review, near-expiry, low-stock, outstanding-balance readers, chart helpers, business-name lookup, product option readers, inventory/balance-sheet/trial-balance/cash-flow/profitability snapshots, overview metric refresh helpers, and multiple reference-detail readers now delegate to `reports/report_service.py`
- `reports/mainpage.py` no longer owns direct SQL blocks for the extracted reporting slices; most remaining work there is rendering, orchestration, and a smaller set of report/read-model helpers
- Widget cleanup pass: major save flows now read more like orchestration than embedded business logic
- Sales now includes a compact quick-add product flow with opening stock from the Sales screen itself
- The project is past first-wave service extraction and is now mainly in a consolidation, read-side cleanup, and hardening phase

### Next Recommended Workstreams

1. Reports service completion
- Continue moving the remaining report-side summaries, reconciliation helpers, selector feeds, and financial/read-model queries into `reports/report_service.py`
- Keep `reports/mainpage.py` on a thin rendering/orchestration path

2. Product and detail/read services
- Continue moving remaining product browse/detail/reference helpers out of widgets
- Consider similar read-service treatment for purchase detail and other large detail/list screens

3. Broader failure-path testing
- Add more integration tests for invalid inputs, partial failures, repeated returns, and stock edge cases
- Keep expanding SQLite-backed coverage around newly extracted service domains before large new UI features land
- Keep adding lightweight guard tests for blank input, over-return, and impossible stock states so client-side failures are caught earlier

4. Stock adjustment and audit refinements
- Strengthen inventory correction tooling for client-site safety
- Consider adjustment approval / supervisor flows if needed later

5. Remaining settings and inventory/report stragglers
- Sweep any remaining direct `accounting_settings` reads/writes that bypass the shared service
- Finish the last report/product/inventory read paths still sitting directly in widgets

### Current Focus

- Keep thinning product, report, and stock-related widgets until they are mostly orchestration-only
- Continue moving report-side summaries, chart feeds, selector/read-model queries, and remaining financial snapshot providers into `reports/report_service.py`
- Favor service-first additions for new report screens, dashboard cards, and read-heavy UI flows
- Use the broadened integration suite as the baseline before each major service-layer expansion
- Treat the current phase as consolidation: finish the read/report layer, tighten failure handling, and keep the core posting flows stable
