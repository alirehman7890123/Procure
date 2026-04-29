# Service Layer Plan

This project is no longer in the "should we extract services?" stage.
It is already in a mixed architecture state:

- Core transaction flows have meaningful service extraction.
- Many CRUD, detail, and reporting screens still own SQL and validation.
- Services are mostly UI-free, but they still depend directly on `QSqlQuery`.

The goal of this plan is to finish the split deliberately, without destabilizing billing, stock, or reporting.

## Current Position

### What Is In Good Shape

- Sales posting and pricing flows are largely service-driven.
- Purchase, GRN, PO, and returns have meaningful service extraction.
- Product list/catalog reads and inventory adjustment flows already use services.
- Accounting settings and theme settings are moving through shared services.
- Payroll has started using service modules for read/write helpers.

### What Is Still UI-Heavy

- Product add/edit/detail save flows
- Transaction list/detail screens
- Remaining reporting and dashboard queries
- Some deeper user/admin screens
- Some business/admin shell edges

### Architectural Reality

- The app already has a service layer.
- The app does not yet have a clean repository/data-access layer.
- Services still use Qt SQL directly, so business logic is not yet framework-independent.
- There is no visible committed `tests/` suite in the repo at the moment, even though the codebase is ready for one.

## Guardrails

- UI widgets should orchestrate user interaction, not own business rules.
- Validation that affects correctness should move to services.
- Services should return plain dictionaries/results or raise clear exceptions.
- New extractions should avoid `QMessageBox`, widget imports, or screen state coupling.
- Keep each extraction vertical: move one screen/domain at a time and leave the app working.
- Prefer reusing existing service modules before creating new ones.
- Once a service area stabilizes, add tests before widening that area further.

## Completed Or Mostly Completed Service Areas

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
- `services/payroll_service.py`
- `services/payroll_posting_service.py`
- `services/customer_service.py`
- `services/supplier_service.py`
- `services/employee_service.py`
- `services/party_transaction_service.py`
- `reports/report_service.py` as an active extraction target

## Screens Already Using Services

- `sales/createsales.py`
- `sales/salesdetail.py`
- `purchase/addpurchase.py`
- `purchase/create_grn.py`
- `purchase/add_po.py`
- `salesreturn/create_sales_return.py`
- `purchasereturn/create_purchase_return.py`
- `customer/addcustomer.py`
- `customer/customerdetail.py`
- `customer/customerlist.py`
- `supplier/addsupplier.py`
- `supplier/supplierdetail.py`
- `supplier/supplierlist.py`
- `employee/addemployee.py`
- `employee/employeedetails.py`
- `employee/employeelist.py`
- `product/productlist.py`
- `transaction/customertransactionlist.py`
- `transaction/customer_transaction_detail.py`
- `transaction/suppliertransactionlist.py`
- `transaction/supplier_transaction_detail.py`
- `transaction/createcustomertransaction.py`
- `transaction/createsuppliertransaction.py`
- `purchase/purchaselist.py`
- `purchase/purchasedetail.py`
- `purchase/po_list.py`
- `purchase/po_detail.py`
- `purchase/grn_list.py`
- `purchase/grn_detail.py`
- `purchase/add_po.py`
- `purchase/create_grn.py`
- `dashboard/dashboard.py`
- `dashboard/daily_session.py`
- `expense/addexpense.py`
- `expense/expenselist.py`
- `expense/expensedetail.py`
- `userprofile/adduser.py`
- `userprofile/userslist.py`
- `userprofile/userdetail.py`
- `userprofile/userprofile.py`
- `userprofile/changepassword.py`
- `business/business.py`
- `business/discount_settings.py`
- `business/tax_settings.py`
- `business/theme_settings.py`
- `utilities/app_theme.py`
- payroll screens using `payroll_service` and `payroll_posting_service`

## Priority Roadmap

### Phase 1: CRUD Service Extraction

Goal: remove direct SQL and validation from the most common maintenance screens.

Status: completed for customer, supplier, and employee first-pass CRUD extraction.

Target domains:

1. Customer
- Create `customer_service.py`
- Move customer validation, insert, update, and discount/tax group lookup logic
- Thin `customer/addcustomer.py` and `customer/customerdetail.py`

2. Supplier
- Create `supplier_service.py`
- Move supplier insert/update/detail/list helpers
- Thin `supplier/addsupplier.py`, `supplier/supplierdetail.py`, `supplier/supplierlist.py`

3. Employee
- Create or extend employee-focused service helpers
- Move employee create/update/detail/list rules out of widgets
- Keep payroll-specific logic separate from core employee CRUD

Phase 1 outcome:

- `customer_service.py` now owns customer validation, create/update flows, group-option reads, group creation, detail reads, transaction-history reads, and list reads
- `supplier_service.py` now owns supplier validation, create flow, detail reads, and list reads
- `employee_service.py` now owns employee validation, create flow, detail reads, list reads, and role-option normalization for the CRUD screens
- Customer, supplier, and employee widgets are now substantially thinner and mostly orchestrate UI concerns

### Phase 2: Product Write-Side Cleanup

Goal: pull product creation and editing logic out of widgets.

Target files:

- `product/addproduct.py`
- `product/productdetail.py`
- `product/productlist.py`

Work:

- Move product validation to service helpers
- Move product create/update flows to service functions
- Move manufacturer lookup/creation into shared services
- Move product list, search, barcode lookup, and catalog data reads through shared read services
- Keep media handling through `product_media_service.py`
- Keep price/admin behavior coordinated with `product_admin_service.py`

Status:

- `services/product_write_service.py` now owns the main product create/update flows, product detail read helpers, admin password verification, imported-row persistence, manufacturer creation, and shared option loading
- `product/addproduct.py` and `product/productdetail.py` no longer own direct SQL for their product write-side flows
- `product/productlist.py` already used `product_catalog_service` for listing/search, and now also routes master-catalog data loading through a service helper instead of merging CSV/manufacturer data inside the widget
- Product screens are now substantially thinner, but adjacent product reporting/list utilities can still be tightened further over time

### Phase 3: Read/Detail Service Sweep

Goal: make large detail/list screens mostly rendering and orchestration only.

Status: started with customer/supplier transaction read extraction.

Target areas:

- purchase detail/list screens
- transaction list/detail screens
- customer history/detail reads
- supplier detail/history reads
- user/admin read models where useful

Work:

- Move multi-query read blocks into dedicated read services
- Standardize list/detail payload shapes
- Keep widgets responsible for filters, table rendering, and navigation only

Current progress:

- `services/party_transaction_service.py` now owns customer/supplier transaction list reads, transaction detail reads, balance-list reads, transaction dashboard summary reads, transaction-form context reads, transaction payload preparation, transaction save helpers, and internal reconciliation posting helpers
- `transaction/customertransactionlist.py`, `transaction/customer_transaction_detail.py`, `transaction/suppliertransactionlist.py`, and `transaction/supplier_transaction_detail.py` now consume service payloads instead of issuing direct SQL
- `transaction/showcustomertransactions.py`, `transaction/showsuppliertransactions.py`, and `transaction/showdetails.py` now consume shared service helpers instead of owning direct SQL and duplicated reconciliation logic
- `transaction/createcustomertransaction.py` and `transaction/createsuppliertransaction.py` now consume shared service helpers for form loading, balance math, excess-handling rules, and transaction persistence
- `services/purchase_transaction_service.py` now also owns purchase list reads, purchase detail reads, purchase item reads, and purchase due-date updates for the invoice screens
- `purchase/purchaselist.py` and `purchase/purchasedetail.py` now consume purchase service helpers instead of issuing direct SQL
- `services/purchase_order_service.py` now also owns PO list reads, PO detail reads, PO line/GRN history reads, PO print payload reads, and PO close helpers for the purchasing screens
- `purchase/po_list.py` and `purchase/po_detail.py` now consume purchase-order service helpers instead of issuing direct SQL
- `services/grn_transaction_service.py` now also owns GRN list reads, GRN detail reads, GRN line reads, and GRN health-check counts for the receipt screens
- `purchase/grn_list.py` and `purchase/grn_detail.py` now consume GRN service helpers instead of issuing direct SQL
- `services/purchase_order_service.py` now also owns supplier option reads/creation and PO print payload reads used by `purchase/add_po.py`
- `services/grn_transaction_service.py` now also owns open-PO option reads, PO supplier/rep context reads, PO receipt-line reads, next-GRN numbering, and PO receipt-status recomputation used by `purchase/create_grn.py`
- `purchase/add_po.py` and `purchase/create_grn.py` now delegate their remaining purchase/PO/GRN query-heavy form loading to services instead of issuing direct SQL
- `services/expense_service.py` now owns expense payload validation, current-user resolution, expense create, expense list rows, and expense detail reads including payment-display shaping
- `expense/addexpense.py`, `expense/expenselist.py`, and `expense/expensedetail.py` now consume expense service helpers instead of owning direct expense/auth SQL
- `services/user_service.py` now owns user payload validation, password hashing/creation, username checks, user list/detail reads, profile reads, profile updates, and password-change verification/update logic
- `userprofile/adduser.py`, `userprofile/userslist.py`, `userprofile/userdetail.py`, `userprofile/userprofile.py`, and `userprofile/changepassword.py` now consume shared user service helpers instead of owning direct auth SQL
- `services/business_service.py` now owns business profile reads, business-name lookup, and business profile updates for the settings page and shell
- `business/business.py` and the business-name shell lookup in `utilities/mylogin.py` now consume shared business service helpers instead of owning direct business-table SQL
- The next natural continuation is the remaining business/admin shell edges, or a service-hardening pass around the extracted modules

### Phase 4: Reports And Dashboard Completion

Goal: finish the read-heavy extraction already underway.

Target files:

- `reports/mainpage.py`
- `dashboard/dashboard.py`
- remaining report-linked detail screens

Work:

- Continue moving direct SQL into `reports/report_service.py`
- Add dashboard-focused read helpers if needed
- Keep chart preparation close to the service layer when it is business-derived

Current progress:

- `reports/report_service.py` now owns dashboard helpers for low-stock rows, expiry rows, reminder queue base rows, today-session sales/return rows, and hourly/monthly sales chart series
- `reports/report_service.py` also now owns dashboard login-history reads, latest-login lookup, reminder-state table persistence helpers, admin password verification, and backup-status/log view shaping helpers
- `services/daily_session_service.py` now owns shared daily-session reads/writes for open session lookup, carry-forward/opening cash, cash-flow summaries, open/close posting, and session history rows
- `dashboard/dashboard.py` and `dashboard/daily_session.py` now consume service-layer session helpers alongside the earlier alert, history, backup, and chart extractions
- `dashboard/dashboard.py` no longer owns direct SQL queries in its current dashboard flows; the remaining work there is mostly UI orchestration and optional helper consolidation

### Phase 5: Service Hardening

Goal: make the extracted layer safer and easier to change.

Work:

- Add tests for extracted service functions
- Cover failure paths: invalid input, partial writes, stock underflow, duplicate actions
- Standardize exception messages and result payloads
- Reduce duplication between service modules

### Phase 6: Repository Boundary

Goal: prepare the codebase for future multi-counter or backend migration work.

Work:

- Introduce shared query helpers or repository modules under `services/` or `repositories/`
- Start separating business rules from raw `QSqlQuery`
- Keep this incremental; do not rewrite everything at once

### Phase 7: Feature Architecture Migration

Goal: move from screen/layer ownership toward feature ownership.

Why this matters:

- The current codebase is organized mostly by screen/domain folders plus a shared `services/` layer.
- That is already better than widget-owned SQL, but one feature is still spread across multiple top-level directories.
- Feature architecture is the next step that makes ownership, testing, and future backend migration easier.

Target direction:

- `features/admin/` for users, profile, business settings, theme/tax/discount settings
- `features/finance/` for transactions, expenses, financial close
- `features/purchase/` for purchase, PO, GRN, purchase return
- `features/sales/` for sales, returns, held sales
- `features/inventory/` for product, stock, media, catalog helpers
- `features/dashboard/` for dashboard and report-facing operational summaries

Migration rules:

- Do not do a big-bang folder rewrite.
- Move one feature slice at a time.
- Stabilize service boundaries first, then move package ownership.
- Use compatibility imports or thin adapters during migration.
- Move base widgets and navigation wiring last for each feature.

Recommended first feature-architecture slice:

1. `admin`
2. `finance`
3. `purchase`
4. `sales`
5. `inventory`

Supporting note:

- See `features/README.md` for the intended package direction and migration pattern.

Current progress:

- `features/admin/` has been created as the first feature package scaffold
- `features/admin/services/` has now been reduced to a lightweight placeholder package; the old bridge modules have been removed and shared admin/business logic lives directly under `medic.services.*`
- `features/admin/ui/` now contains the real `BusinessWidget`, `ProfileWidget`, `ChangePasswordWidget`, `UserListWidget`, `UserDetailWidget`, `DiscountSettingsWidget`, `TaxSettingsWidget`, `ThemeSettingsWidget`, `BaseProfileWidget`, and `BaseBusinessWidget` implementations, with package-level exports in place
- `features/admin/ui/*.py` and the business-name shell lookup in `utilities/mylogin.py` now call shared admin/business logic directly through `medic.services.user_service` and `medic.services.business_service`, so the admin UI no longer depends on the feature service bridges for its active code paths
- the app shell wiring in `utilities/mylogin.py` now resolves admin/business UI through the `features.admin.ui` path
- the old `userprofile/*` and `business/*` compatibility shim modules have now been removed, so `features/admin/ui` is the sole internal owner for admin/profile/business screens and base widgets
- The next `admin` migration step is now less about ownership cleanup and more about optional polish: normalizing any remaining packaging-facing import edges and keeping the feature boundary light
- `features/finance/` has now been created as the second feature package scaffold
- `features/finance/services/` has now been reduced to a lightweight placeholder package; the old bridge modules have been removed and shared finance logic lives directly under `medic.services.*`
- `features/finance/ui/base_transactions.py`, `features/finance/ui/base_expenses.py`, and `features/finance/ui/base_financial_close.py` now own the feature-level base widgets for the first finance slice
- `features/finance/ui/transaction_hub.py`, `features/finance/ui/customer_transactions.py`, and `features/finance/ui/supplier_transactions.py` now own the main transaction hub plus the customer/supplier overview screens
- `features/finance/ui/create_customer_transaction.py`, `features/finance/ui/create_supplier_transaction.py`, `features/finance/ui/customer_transaction_list.py`, `features/finance/ui/supplier_transaction_list.py`, `features/finance/ui/customer_transaction_detail.py`, and `features/finance/ui/supplier_transaction_detail.py` now own the transaction create/list/detail flow
- `features/finance/ui/add_expense.py`, `features/finance/ui/expense_list.py`, and `features/finance/ui/expense_detail.py` now own the expense add/list/detail flow, and `features/finance/ui/base_expenses.py` now points at those feature-owned screens
- `features/finance/ui/financial_close_page.py`, `features/finance/ui/financial_close_list.py`, and `features/finance/ui/financial_quarter_summary.py` now own the financial-close workflow/history/quarter-summary flow, and `features/finance/ui/base_financial_close.py` now points at those feature-owned screens
- `features/finance/ui/daily_session.py` now owns the daily-session screen, and the dashboard shell now imports it through the finance feature path
- `features/finance/ui/` now uses shared finance logic directly through `medic.services.party_transaction_service`, `medic.services.expense_service`, `medic.services.financial_closing_service`, and `medic.services.daily_session_service`, so the active finance UI no longer depends on the feature service bridges for its main code paths
- `features/finance/ui` is now the sole internal owner for the finance base widgets, transaction flow screens, expense screens, financial-close screens, and daily-session screen; the old `transaction/*`, `expense/*`, `financialclose/*`, and `dashboard/daily_session.py` compatibility shims have now been removed
- `utilities/mylogin.py` now imports transaction, expense, and financial close entry widgets through the `features.finance.ui` path
- `features/purchase/` has now been created as the third feature package scaffold
- `features/purchase/services/` has now been reduced to a lightweight placeholder package; the old bridge modules have been removed and shared purchasing logic lives directly under `medic.services.*`
- `features/purchase/ui/base_purchase.py`, `features/purchase/ui/base_po.py`, and `features/purchase/ui/base_grn.py` now own the feature-level base widgets for the first purchase slice
- `features/purchase/ui/add_purchase.py`, `features/purchase/ui/purchase_list.py`, and `features/purchase/ui/purchase_detail.py` now own the main purchase invoice flow
- `features/purchase/ui/add_po.py`, `features/purchase/ui/po_list.py`, and `features/purchase/ui/po_detail.py` now own the purchase-order create/list/detail flow, and `features/purchase/ui/base_po.py` now points at those feature-owned screens
- `features/purchase/ui/create_grn.py`, `features/purchase/ui/grn_list.py`, and `features/purchase/ui/grn_detail.py` now own the GRN create/list/detail flow, and `features/purchase/ui/base_grn.py` now points at those feature-owned screens
- `features/purchase/ui/` now uses shared purchasing logic directly through `medic.services.purchase_posting_service`, `medic.services.purchase_items_service`, `medic.services.purchase_transaction_service`, `medic.services.purchase_order_service`, `medic.services.grn_posting_service`, `medic.services.grn_transaction_service`, and the related draft helpers, so the active purchase UI no longer depends on the feature service bridges for its main code paths
- `features/purchase/ui` is now the sole internal owner for the purchase base widgets, purchase invoice screens, purchase-order screens, and GRN screens; the old `purchase/*` compatibility shims for those flows have now been removed
- `utilities/mylogin.py` now imports purchase, PO, and GRN entry widgets through the `features.purchase.ui` path
- `features/inventory/` has now been created as the fourth feature package scaffold
- `features/inventory/services/` has now been reduced to a lightweight placeholder package; the old bridge modules have been removed and shared inventory logic lives directly under `medic.services.*`
- `features/inventory/ui/base_inventory.py` now owns the feature-level base widget for the first inventory slice
- `features/inventory/ui/add_product.py`, `features/inventory/ui/product_list.py`, and `features/inventory/ui/product_detail.py` now own the main product create/list/detail flow
- `features/inventory/ui/` now uses shared product and stock logic directly through `medic.services.product_write_service`, `medic.services.product_catalog_service`, `medic.services.product_admin_service`, `medic.services.product_media_service`, and `medic.services.stock_adjustment_service`, with only the shared prescription-schema helper still coming from outside the inventory feature, so the active inventory UI no longer depends on the feature service bridges for its main code paths
- `features/inventory/ui` is now the sole internal owner for the inventory base widget and product add/list/detail screens; the old `product/*` compatibility shims have now been removed
- `utilities/mylogin.py` now imports the product entry widget through the `features.inventory.ui` path
- `features/sales/` has now been created as the fifth feature package scaffold
- `features/sales/services/` has now been reduced to a lightweight placeholder package; the old bridge modules have been removed and shared sales logic lives directly under `medic.services.*`
- `features/sales/ui/base_sales.py` now owns the feature-level base widget for the first sales slice
- `features/sales/ui/create_sales.py`, `features/sales/ui/receipt_list.py`, and `features/sales/ui/sales_detail.py` now own the main sales create/list/detail flow
- `features/sales/ui/create_sales.py` now resolves its local pricing helper through the feature path
- `features/sales/ui/receipt_list.py` now delegates its invoice list/search/barcode reads to `medic.services.sales_detail_service`, both invoice export read paths in `features/sales/ui/create_sales.py` now flow through that service, the sales customer/manufacturer helper flows have been moved there too, the held-sale list/detail/item reads now also flow through that service, the hold-sale persistence path now runs through `medic.services.sales_transaction_service`, the salesman lookup / credit-position read / customer-transaction persistence plus sales header/prescription persistence are now service-backed, and the sales item posting/FIFO allocation orchestration now also runs through `medic.services.sales_transaction_service`; the main remaining sales consolidation gap is the residual helper/query logic still living around `features/sales/ui/create_sales.py`
- `features/sales/ui/` now follows the same direct-to-`medic.services` pattern as the other stable feature areas: active sales screens call shared logic through `medic.services.product_media_service`, `medic.services.accounting_settings_service`, `medic.services.sales_defaults_service`, `medic.services.sales_detail_service`, `medic.services.sales_posting_service`, `medic.services.sales_items_service`, and `medic.services.sales_transaction_service`, while still owning the feature-level UI flow locally
- `features/sales/ui` is now the sole internal owner for the sales base widget and the main sales create/list/detail screens; the old `sales/basesales.py`, `sales/createsales.py`, `sales/receiptlist.py`, and `sales/salesdetail.py` compatibility shims have now been removed
- `utilities/mylogin.py` now imports the sales entry widget through the `features.sales.ui` path
- repo-internal test and shell imports that were still pointing through shim modules have now been redirected to feature-owned module paths, so the remaining shims are primarily legacy compatibility entry points rather than active internal dependencies
- feature package `__init__.py`, `ui/__init__.py`, and `services/__init__.py` files for `admin`, `finance`, `purchase`, `inventory`, and `sales` have now been reduced to lightweight export metadata so importing one feature package no longer eagerly imports the whole feature tree
- several startup-heavy base widgets now lazy-load their child screens instead of importing and constructing full sub-flows at module import time, including `dashboard/base_dashboard_page.py`, `features/finance/ui/base_transactions.py`, `features/finance/ui/base_expenses.py`, `features/purchase/ui/base_purchase.py`, `features/purchase/ui/base_po.py`, `features/purchase/ui/base_grn.py`, `features/inventory/ui/base_inventory.py`, `features/sales/ui/base_sales.py`, `features/admin/ui/base_profile.py`, and `features/admin/ui/base_business.py`
- the first screen-level import-thinning pass is now also in place for high-traffic feature screens: finance transaction/expense entry screens, purchase invoice/GRN entry screens, and `features/sales/ui/create_sales.py` no longer import `PaymentMethodHandler` at module load time, and the sales quick-product dialog no longer resolves product-form options at class-definition time
- a second screen-level thinning pass is now in place for additional stable feature screens: `features/admin/ui/theme_settings.py` now resolves theme helpers at runtime, `features/inventory/ui/add_product.py` now resolves product search/form/preview helpers at runtime, `features/purchase/ui/po_detail.py` now resolves activity logging at runtime, and `features/sales/ui/sales_detail.py` has been trimmed of a stale top-level preview helper import
- a repo-wide import normalization pass is now in place across feature UI, shared services, reports, dashboard, payroll, and tests so the app mostly uses canonical `medic...` imports internally; the main intentional exception still left is the startup fallback boundary in `starting.py` and `utilities/mylogin.py`
- the next feature-architecture cleanup step is to decide whether to keep or retire that startup fallback boundary, and then reassess which remaining non-feature legacy packages should still exist at all

## Recommended File Order

If we want the cleanest payoff with manageable risk, work in this order:

1. finish remaining product write/read cleanup
2. harden extracted services with tests and consistency passes
3. start feature-architecture migration with `admin`
4. then move `finance`
5. then move `purchase`

## Definition Of Done For A Screen

A screen counts as "service-extracted" when:

- Validation is not embedded in widget event handlers.
- SQL is not written directly in the widget except for trivial transitional leftovers.
- Save/load logic is delegated to service functions.
- The widget mostly coordinates inputs, outputs, dialogs, and rendering.
- Error handling is based on service results or exceptions, not hidden database branches scattered through the screen.

## Near-Term Focus

The next sensible move is:

1. Finish the remaining high-value service extraction in product/report areas.
2. Add tests and consistency hardening around the extracted services.
3. Begin feature-architecture migration with the `admin` slice once those boundaries are stable.

The service layer made the code safer to rearrange. Feature architecture is the next step because it changes where code lives, not just how widgets call it, so it should build on the service work rather than replace it.
