# Medic Desktop Phase 1 Master Test Plan

This document defines Phase 1 of the production-readiness effort for the desktop `medic` app.

Scope rules:
- in scope: everything inside desktop `medic`
- out of scope: `mobile/`
- focus: feature correctness, business safety, data integrity, workflow reliability
- not a primary focus in this phase: folder structure, architectural cleanup, or refactors unless a defect cannot be tested or fixed safely without them

The purpose of Phase 1 is to build a complete test map of what exists today so later phases can execute rigorous testing without blind spots.

## Phase 1 Outcomes

By the end of Phase 1 we should have:
- a complete feature inventory of the current desktop app
- a risk-ranked testing surface
- a clear view of existing automated coverage
- a list of uncovered or weakly-covered areas
- a sequenced plan for Phases 2 through 6
- release gates tied to real business risk

## Production-Readiness Standard

The app is only considered production ready when all of the following are true:
- all critical money, stock, and posting flows pass
- no stock corruption remains
- no customer or supplier balance corruption remains
- no duplicated or partial save behavior remains
- no startup, login, or module-open crash remains in supported environments
- all business documents that operators depend on open and render correctly
- high-risk regressions can be rerun repeatedly with stable results

## Current Desktop App Feature Inventory

The current desktop app surface, excluding `mobile`, includes:

### 1. Startup, Login, Session, and App Shell

- application startup entrypoint
- login screen
- role and permission gating
- session-gated workflows
- sidebar and base page navigation
- app theming and shared dialogs
- licensing and local license validation helpers

Primary code areas:
- `starting.py`
- `utilities/mylogin.py`
- `utilities/session_gate.py`
- `utilities/session_service.py`
- `utilities/permissions.py`
- `utilities/license.py`
- `utilities/license_core.py`
- `utilities/basepage.py`

### 2. Dashboard and Operational Overview

- dashboard landing page
- welcome screen
- session metrics
- sales and stock summary visibility
- low stock and expiry signal widgets

Primary code areas:
- `dashboard/dashboard.py`
- `dashboard/welcome.py`
- `dashboard/base_dashboard_page.py`

### 3. Sales

- create sale
- hold and reload sale
- cash sale
- credit sale
- walk-in customer sale rules
- line and order totals
- pricing logic
- stock deduction and FIFO behavior
- receipt list and detail views
- standard and thermal invoice export
- payment collection behavior at sale time

Primary code areas:
- `features/sales/ui/create_sales.py`
- `features/sales/ui/sales_detail.py`
- `features/sales/ui/receipt_list.py`
- `features/sales/ui/pricing_logic.py`
- `services/sales_items_service.py`
- `services/sales_posting_service.py`
- `services/sales_transaction_service.py`
- `services/sales_detail_service.py`
- `sales/thermal.py`

### 4. Sales Return

- create sales return
- return list
- return detail
- refund or balance adjustment behavior
- stock put-back correctness
- protection against invalid or duplicate returns

Primary code areas:
- `features/salesreturn/ui/create_sales_return.py`
- `features/salesreturn/ui/sales_return_list.py`
- `features/salesreturn/ui/sales_return_detail.py`
- `services/sales_return_service.py`
- `services/sales_return_transaction_service.py`
- `services/return_read_service.py`

### 5. Purchase

- direct purchase entry
- purchase list and detail
- taxes, discounts, CN adjustment, payable remaining
- supplier transaction posting
- draft behavior
- price review and save orchestration

Primary code areas:
- `features/purchase/ui/add_purchase.py`
- `features/purchase/ui/purchase_list.py`
- `features/purchase/ui/purchase_detail.py`
- `services/purchase_items_service.py`
- `services/purchase_posting_service.py`
- `services/purchase_transaction_service.py`
- `services/purchase_draft_service.py`

### 6. Purchase Orders and GRN

- create purchase order
- PO list and detail
- create GRN from PO
- full GRN
- partial GRN
- GRN list and detail
- PO status progression after receipt
- stock and batch creation from GRN posting

Primary code areas:
- `features/purchase/ui/add_po.py`
- `features/purchase/ui/po_list.py`
- `features/purchase/ui/po_detail.py`
- `features/purchase/ui/create_grn.py`
- `features/purchase/ui/grn_list.py`
- `features/purchase/ui/grn_detail.py`
- `services/purchase_order_service.py`
- `services/grn_posting_service.py`
- `services/grn_transaction_service.py`
- `services/grn_draft_service.py`

### 7. Purchase Return

- create purchase return
- purchase return list
- purchase return detail
- supplier balance reversal behavior
- stock reversal behavior

Primary code areas:
- `features/purchasereturn/ui/create_purchase_return.py`
- `features/purchasereturn/ui/purchase_return_list.py`
- `features/purchasereturn/ui/purchase_return_detail.py`
- `services/purchase_return_service.py`
- `services/purchase_return_transaction_service.py`

### 8. Inventory and Product Administration

- add product
- product list
- product detail
- opening stock
- batch and stock movement support
- pricing, tax, discount, and reorder-related fields
- product catalog and admin management
- scheduled pricing hooks
- product media support

Primary code areas:
- `features/inventory/ui/add_product.py`
- `features/inventory/ui/product_list.py`
- `features/inventory/ui/product_detail.py`
- `services/product_admin_service.py`
- `services/product_catalog_service.py`
- `services/product_write_service.py`
- `services/inventory_movement_service.py`
- `services/stock_adjustment_service.py`
- `services/scheduled_price_service.py`
- `services/product_media_service.py`

### 9. Customer Management

- add customer
- edit customer
- customer list
- customer detail
- customer history
- quick-add customer paths from transaction flows

Primary code areas:
- `features/customer/ui/add_customer.py`
- `features/customer/ui/customer_list.py`
- `features/customer/ui/customer_detail.py`
- `customer/editcustomer.py`
- `customer/customerhistory.py`
- `services/customer_service.py`

### 10. Supplier Management

- add supplier
- supplier list
- supplier detail
- quick-add supplier paths from purchase-side flows

Primary code areas:
- `features/supplier/ui/add_supplier.py`
- `features/supplier/ui/supplier_list.py`
- `features/supplier/ui/supplier_detail.py`
- `services/supplier_service.py`

### 11. Sales Representative Management

- add sales rep
- sales rep list
- sales rep detail
- use in sales and transaction flows

Primary code areas:
- `features/salesrep/ui/add_salesrep.py`
- `features/salesrep/ui/salesrep_list.py`
- `features/salesrep/ui/salesrep_detail.py`
- `services/salesrep_service.py`

### 12. Employee and Payroll

- employee creation and management
- payroll creation
- payroll list and detail
- attendance
- attendance list
- salary advance
- advance list
- payroll posting

Primary code areas:
- `features/employee/ui/add_employee.py`
- `features/employee/ui/employee_list.py`
- `features/employee/ui/employee_detail.py`
- `features/payroll/ui/add_payroll.py`
- `features/payroll/ui/payroll_list.py`
- `features/payroll/ui/payroll_detail.py`
- `features/payroll/ui/attendance.py`
- `features/payroll/ui/attendance_list.py`
- `features/payroll/ui/salary_advance.py`
- `features/payroll/ui/advance_list.py`
- `services/employee_service.py`
- `services/payroll_service.py`
- `services/payroll_posting_service.py`

### 13. Finance, Expense, and Financial Close

- customer transactions
- supplier transactions
- transaction hub
- expense creation
- expense list and detail
- daily session open and close
- financial close list and page
- quarter summary
- accounting settings used by posting flows

Primary code areas:
- `features/finance/ui/create_customer_transaction.py`
- `features/finance/ui/customer_transaction_list.py`
- `features/finance/ui/customer_transaction_detail.py`
- `features/finance/ui/create_supplier_transaction.py`
- `features/finance/ui/supplier_transaction_list.py`
- `features/finance/ui/supplier_transaction_detail.py`
- `features/finance/ui/add_expense.py`
- `features/finance/ui/expense_list.py`
- `features/finance/ui/expense_detail.py`
- `features/finance/ui/daily_session.py`
- `features/finance/ui/financial_close_page.py`
- `features/finance/ui/financial_close_list.py`
- `features/finance/ui/financial_quarter_summary.py`
- `services/daily_session_service.py`
- `services/expense_service.py`
- `services/financial_closing_service.py`
- `services/party_transaction_service.py`
- `services/accounting_settings_service.py`

### 14. Admin and Business Settings

- business profile
- user creation
- user list and detail
- profile
- password change
- tax settings
- discount settings
- theme settings

Primary code areas:
- `features/admin/ui/business_profile.py`
- `features/admin/ui/add_user.py`
- `features/admin/ui/users_list.py`
- `features/admin/ui/user_detail.py`
- `features/admin/ui/profile.py`
- `features/admin/ui/change_password.py`
- `features/admin/ui/tax_settings.py`
- `features/admin/ui/discount_settings.py`
- `features/admin/ui/theme_settings.py`
- `services/user_service.py`
- `services/business_service.py`

### 15. Reports and Document Output

- report service
- main reports page
- sales invoice PDF
- thermal invoice PDF
- prescription file storage and preview helpers
- label printing support

Primary code areas:
- `reports/mainpage.py`
- `reports/report_service.py`
- `sales/thermal.py`
- `utilities/file_preview.py`
- `utilities/label_printer.py`

## Risk Tiers

Testing priority is driven by business impact:

### Critical

Failures here can make the app not production safe:
- startup, login, role access failure
- sales posting
- sales return posting
- purchase posting
- PO to GRN stock receipt flows
- purchase return posting
- customer and supplier transaction posting
- daily session open and close
- stock movement integrity
- customer or supplier balance integrity
- duplicate or partial save behavior
- invoice and receipt generation crash on save path

### High

Failures here can seriously disrupt daily use:
- list/detail screens for money-moving documents
- add/edit product, customer, supplier, employee, user
- dashboard totals and session summaries
- search, selection, and quick-add helpers used inside critical workflows
- expense flows
- permissions and role restrictions
- report correctness for due balances and stock indicators

### Medium

Failures here hurt reliability or trust but do not usually corrupt the business state immediately:
- non-core filtering and sorting
- cosmetic rendering issues in screens
- printer layout edge cases when data is still correct
- weaker validation messages
- convenience helpers and preview flows

## Existing Automated Coverage Snapshot

The current `tests/` folder already covers meaningful parts of the risky domain logic.

Covered strongly or moderately:
- sales posting and transaction services
- sales pricing policies
- sales item save logic
- sales return services
- purchase posting and transaction services
- purchase order service
- GRN posting
- inventory movement
- stock adjustment service
- daily session service
- accounting settings service
- report service
- several widget save-orchestration flows for purchase, PO, GRN, finance transaction, session, and returns

Representative automated files:
- `tests/test_sales_posting_service.py`
- `tests/test_sales_transaction_service.py`
- `tests/test_sales_return_service.py`
- `tests/test_purchase_posting_service.py`
- `tests/test_purchase_order_service.py`
- `tests/test_grn_posting_service.py`
- `tests/test_feature_purchase_widget_flow.py`
- `tests/test_feature_po_widget_flow.py`
- `tests/test_feature_grn_widget_flow.py`
- `tests/test_feature_finance_transaction_widget_flow.py`
- `tests/test_daily_session_service.py`
- `tests/test_report_service.py`

## Coverage Gaps Identified In Phase 1

The following areas appear weakly covered or uncovered and should be treated as Phase 2 and Phase 3 priorities:

### Startup and Login

- fresh startup on real app shell
- login lockout behavior
- packaged runtime import safety
- first-open navigation across modules

### Sales UI and End-to-End Behavior

- full create-sale screen behavior
- quick-add customer during sale
- receipt list and detail validation against actual saved sale
- thermal and standard invoice field correctness, not just smoke generation
- retry behavior after validation failure
- duplicate save protection under repeated click conditions

### Sales Return UI and Data Integrity

- list/detail correctness after return posting
- invalid quantity or invalid reference behavior
- balance and stock reconciliation after return

### Purchase, PO, and GRN UI Coverage

- list/detail screen correctness
- quick-add supplier from purchase-side workflows
- due date persistence and status visibility
- linked GRN visibility in PO detail

### Purchase Return End-to-End Coverage

- real supplier payable reversal checks
- list/detail correctness

### Inventory and Product

- add product and edit product from UI
- opening stock data integrity
- search and detail loads on realistic datasets
- expiry and reorder indicators
- scheduled pricing scenarios if active in product logic

### Customer, Supplier, Sales Rep

- CRUD flows in UI
- detail screen correctness
- in-flow selection and quick-add behavior

### Employee and Payroll

- payroll entry/posting correctness
- attendance workflows
- salary advance workflows
- payroll list/detail and totals

### Expense and Financial Close UI

- expense create/list/detail
- financial close page and history page
- quarter summary reliability

### Admin and Permissions

- user creation
- password change
- business profile persistence into printed documents
- tax and discount setting effects
- permission enforcement by role

### Reports and Dashboard

- dashboard totals vs saved transactions
- due totals vs transaction history
- low stock and expiry widgets
- report filters and empty-state handling

### Printing, Preview, and Device-Adjacent Flows

- print/export layout correctness with long names and multi-line receipts
- label printing behavior
- file preview behavior for generated files

### Licensing and Operational Edge Cases

- license check failure states
- expired or missing license behavior
- blocked startup or degraded mode behavior if implemented

## Required Test Data Matrix

Rigorous testing needs controlled data scenarios, not just random entries.

We will prepare:
- stocked product with single batch
- stocked product with multiple FIFO batches
- low-stock product
- expired product and near-expiry product
- tax-enabled and tax-disabled products
- discountable and non-discountable products if rules differ
- walk-in customer
- credit customer with prior due
- customer with overpayment or refundable state
- supplier with prior payable
- supplier with prior receivable or reverse-state case
- active and inactive users if applicable
- cashier role and admin role
- employee with payroll history
- open session and closed session states
- purchase order ready for full GRN
- purchase order ready for partial GRN

## Test Dimensions To Apply To Each Critical Workflow

Every high-risk workflow should be tested across these dimensions where relevant:

- fresh app startup
- repeated save click
- empty required field
- invalid numeric input
- partial payment
- overpayment or excess receipt
- zero quantity or zero amount edge
- reopened draft or held state
- list to detail round-trip
- restart app and re-open saved record
- print/export after save
- permission-restricted user
- with active session and without active session

## Phase 2 Through Phase 6 Execution Blueprint

### Phase 2. Coverage Audit and Test Harness Hardening

Goals:
- run current tests and measure what actually passes
- identify flaky tests, failing tests, and missing harness support
- define stable seed data and test database strategy
- add missing automation scaffolding where it improves speed and confidence

Outputs:
- current-pass baseline
- flaky or broken test list
- harness gaps list

### Phase 3. Critical Flow Manual and Automated Execution

Goals:
- run startup, session, sales, returns, purchase, GRN, finance, and document save paths first
- verify database state after each critical workflow
- log all release blockers immediately

Outputs:
- critical path pass/fail ledger
- stock and balance reconciliation notes
- blocker list

### Phase 4. Broad Module Sweeps and Adversarial Testing

Goals:
- cover inventory, customer, supplier, payroll, admin, reports, and dashboard
- run edge-case and invalid-state testing
- test permission differences and retry paths

Outputs:
- module sweep results
- negative-test findings
- role/permission findings

### Phase 5. Defect Fix, Re-Test, and Regression Buildout

Goals:
- fix highest severity bugs
- re-run impacted workflows immediately
- grow a repeatable regression set for all prior failures

Outputs:
- defect closure log
- targeted regression pack
- updated release risk view

### Phase 6. Final Certification Sweep

Goals:
- run full critical regression
- run high-priority smoke on all major modules
- verify no stock mismatch, no balance mismatch, no save duplication, and no output crash remains
- produce final release recommendation

Outputs:
- release-readiness verdict
- final blocker list if any remain
- signed-off production checklist

## Release Gates

The desktop app cannot be called production ready if any of the following are true:
- any critical test fails
- any high-severity save/posting workflow still duplicates or partially saves
- any stock reconciliation mismatch exists
- any customer or supplier running balance mismatch exists
- startup or login is unstable
- a major module crashes on first open
- invoice or receipt generation crashes on save path

## Recommended Execution Order

1. startup and login smoke
2. daily session open and gated workflow checks
3. sales and sales return
4. purchase, PO, GRN, and purchase return
5. customer and supplier transactions
6. dashboard, expense, and financial close
7. inventory and product administration
8. customer, supplier, sales rep management
9. employee and payroll
10. admin, users, permissions, and business settings
11. reports, printing, preview, and labels
12. full restart and regression sweep

## Defect Logging Standard

Every defect should capture:
- unique ID
- module
- severity
- exact reproduction steps
- expected result
- actual result
- whether data corruption occurred
- whether it blocks release
- screenshots or exported file evidence when relevant

## Phase 1 Summary

Phase 1 confirms that the desktop `medic` app already has meaningful automated coverage around several service and posting layers, but still has substantial gaps in startup, UI-heavy workflows, CRUD screens, printing correctness, dashboard/report reconciliation, admin/permission behavior, and payroll-related flows.

The next step after this document is Phase 2: run the existing test suite, record the current baseline, and convert the uncovered high-risk areas into an execution queue for rigorous real-world testing.
