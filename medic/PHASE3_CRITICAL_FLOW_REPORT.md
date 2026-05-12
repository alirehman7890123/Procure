# Medic Desktop Phase 3 Critical Flow Report

This report records the Phase 3 critical-flow checkpoint for the desktop `medic` app.

Scope:
- in scope: desktop `medic`
- out of scope: `mobile/`

## Phase 3 Goal

Phase 3 focuses on the release-gate flows that can:
- lose money
- corrupt stock
- corrupt balances
- block operators during the working day
- break receipts, sessions, or posting workflows

## Environment Used

Runtime used for verification:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q
```

## Automated Baseline Status

Current automated baseline:
- full suite: `262 passed`
- financial-close utility lane: `37 passed`

Additional critical slice rerun during Phase 3:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q \
  tests/test_feature_daily_session_widget_flow.py \
  tests/test_feature_purchase_widget_flow.py \
  tests/test_feature_po_widget_flow.py \
  tests/test_feature_grn_widget_flow.py \
  tests/test_feature_return_widget_flow.py \
  tests/test_feature_finance_transaction_widget_flow.py \
  tests/test_feature_sales_transaction_service.py \
  tests/test_service_sqlite_integration.py \
  purchase/test_po_grn_flow.py \
  sales/test_createsales.py
```

Critical slice result:
- `64 passed`

Startup and module-import smoke:
- `startup_import_ok`
- `critical_widgets_import_ok`

## Critical Release-Gate View

### Startup / Shell

- `SM-01 App startup`
  - status: `Pass (automated smoke)`
  - evidence: `starting.py` imports successfully in project runtime

- `SM-02 Open all major modules once`
  - status: `Partial automated confidence`
  - evidence: critical widget imports for sales, purchase, GRN, and daily session succeeded
  - still needed: real interactive open of all major modules in the running desktop app

### Daily Session

- `DS-01 Open session`
  - status: `Pass`
  - evidence: service and widget-flow tests pass

- `DS-03 Close session after activity`
  - status: `Pass`
  - evidence: session summary, close persistence, and widget flow pass

- `DS-02 Session-gated workflow`
  - status: `Not fully closed`
  - evidence: some session gating is covered indirectly
  - still needed: direct real-app manual validation across sales, purchase, and finance screens

### Sales

- `S-05 Hold sale and reload`
  - status: `Pass`
  - evidence: hold persistence and reload flows pass

- `S-06 Low stock protection`
  - status: `Pass`
  - evidence: sales item and FIFO service checks reject insufficient stock

- `S-07 FIFO stock deduction`
  - status: `Pass`
  - evidence: FIFO allocation and integration coverage pass

- `S-11 Thermal receipt export`
  - status: `Pass`
  - evidence: export smoke path passes

- `S-12 Standard receipt export`
  - status: `Pass`
  - evidence: standard PDF export smoke path passes

- `S-01 Cash sale, single item`
- `S-02 Cash sale, multiple items`
- `S-03 Credit sale`
- `S-04 Walk-in customer with remaining amount blocked`
  - status: `Partially covered automatically, still manually required`
  - evidence: pricing, totals, save helpers, stock movement, and balance integration all pass
  - still needed: real UI execution in the live app with saved records and printed output checks

### Purchase / PO / GRN / Purchase Return

- `P-01 Direct purchase save`
  - status: `Pass`
  - evidence: widget save orchestration and SQLite integration pass

- `P-03 Create PO`
  - status: `Pass`
  - evidence: PO widget flow and service validations pass

- `P-04 Full GRN against PO`
  - status: `Pass`
  - evidence: end-to-end PO -> GRN -> bill -> stock tests pass

- `P-05 Partial GRN against PO`
  - status: `Pass`
  - evidence: partial receipt tests pass

- Purchase return critical posting behavior
  - status: `Pass`
  - evidence: purchase return service and integration tests pass

- `P-02 Purchase with taxes/discounts`
  - status: `Not fully closed`
  - evidence: underlying math and purchase flow coverage is strong
  - still needed: live UI save and detail verification with realistic invoice values

### Finance Transactions

- `F-01 Customer payment receive`
  - status: `Pass`
  - evidence: widget flow and running-balance persistence pass

- `F-02 Customer refund / overpayment case`
  - status: `Pass`
  - evidence: excess and receivable/payable logic pass

- `F-03 Supplier payment`
  - status: `Pass`
  - evidence: supplier transaction widget flow passes

- `F-04 Supplier receive / reverse case`
  - status: `Pass`
  - evidence: reverse/excess cases pass

### Stock / Balance Integrity

- sales integration stock updates
  - status: `Pass`
- sales return stock restoration
  - status: `Pass`
- purchase batch creation and supplier liability
  - status: `Pass`
- purchase return stock reduction and supplier balance update
  - status: `Pass`
- GRN stock creation and PO status update
  - status: `Pass`
- customer running-balance persistence
  - status: `Pass`
- supplier running-balance summary path
  - status: `Pass`

Evidence source:
- `tests/test_service_sqlite_integration.py`
- `utilities/test_inventory_finance_flows.py`
- posting/service test files for sales, purchase, GRN, returns, and finance

## Current Release-Blocker Assessment

As of this Phase 3 checkpoint:

- no automated critical-flow failure is currently open
- no known automated stock mismatch is currently open
- no known automated customer/supplier balance mismatch is currently open
- no known automated duplicate-save regression is currently open
- no known automated receipt export crash is currently open

This is a strong milestone, but it is not the same as final production certification.

## Manual-Only Critical Items Still Required

The following critical or near-critical checks still need direct desktop-app execution with a realistic database:

1. `SM-02` Open all major modules once in the real app shell
2. `S-01` Cash sale single item through the live UI
3. `S-02` Cash sale multiple items through the live UI
4. `S-03` Credit sale with customer due creation
5. `S-04` Walk-in customer remaining-balance rejection
6. `DS-02` Session gating with and without an open session across protected workflows
7. `P-02` Purchase save with taxes/discounts and live detail verification
8. printed-output visual checks for receipt readability and field correctness

## Phase 3 Conclusion

Phase 3 materially improved confidence in the desktop app:
- the automated regression baseline is fully green
- the previously unstable financial-close lane is now stable and passing
- critical stock, balance, posting, return, PO, GRN, and finance flows are strongly covered by automation

The app is now in a much better state for the next step:
- focused manual execution of the remaining real-world critical workflows in the running desktop application

## Recommended Next Step

Proceed to the manual execution portion of Phase 3 / early Phase 4:
- run the remaining live desktop critical flows using a realistic database copy
- capture pass/fail evidence directly against the release matrix
- especially validate startup/login, module-open behavior, live sales saves, session gating, and printed output correctness
