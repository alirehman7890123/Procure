# Medic Desktop Phase 2 Baseline Report

This document records the current automated-test baseline for the desktop `medic` app.

Scope:
- in scope: desktop `medic`
- out of scope: `mobile/`

## Phase 2 Goal

Phase 2 was intended to answer three questions:
- what is the correct command and interpreter to run the current suite
- how much of the existing suite collects and runs successfully today
- what harness or stability issues will affect the deeper production-readiness phases

## Environment Baseline

Observed on this machine:
- system shell did not expose `pytest`
- system shell did not expose `python`
- `/usr/bin/python3` existed but did not have project `pytest` installed
- the working project interpreter was the user-provided virtual environment at `../venv/bin/python`

Working command shape:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q
```

Why `PYTHONPATH=..` was needed:
- several tests import modules as `medic.*`
- when running from inside the repo root `/Desktop/Procure/medic`, the parent directory must be import-visible for `medic` package resolution

Without that environment fix, collection failed with `ModuleNotFoundError: No module named 'medic'`.

## Collection Baseline

Successful collection command:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest --collect-only -q
```

Collection result:
- `262 tests collected`

This is the current automated suite size that Phase 3 and later regression work can build on.

## Current Functional Regression

One real failing test was isolated cleanly:

- file: `tests/test_purchase_items_service.py`
- test: `PurchaseItemsServiceTests.test_normalize_purchase_item_row_builds_landing_cost`

Failure:
- expected `row["expiry"] == "2026-04-01"`
- actual `row["expiry"] == None`
- input under test: `expiry_text="04-26"`

Relevant implementation:
- `services/purchase_items_service.py`
- `parse_expiry_to_db_date()`
- `normalize_purchase_item_row()`

Observed behavior:
- `parse_expiry_to_db_date()` rejects `MM-YY` values that are earlier than the machine's current month
- the test expects month-year normalization to remain deterministic for `04-26`
- because the current date is now later than April 2026, the function returns empty and `normalize_purchase_item_row()` converts that to `None`

Risk assessment:
- severity: `High`
- reason: purchase batch expiry parsing is core pharmacy/inventory data and can affect stock quality, expiry visibility, and purchase save correctness

Interpretation:
- this looks like either
  - a test that became date-sensitive over time and now fails, or
  - an implementation rule that is too strict for current product expectations

Phase 2 records it as a real regression that must be resolved before calling the suite clean.

## Harness And Stability Findings

### 1. Import-path dependency

Problem:
- the suite is not stable under a plain `pytest` or plain `python3 -m pytest` invocation from the repo root

Impact:
- easy to get false-negative collection failures
- CI or future local runs can break if the environment is not configured the same way

Status:
- reproducible
- not an app bug, but a test-harness issue

### 2. Virtual environment dependency

Problem:
- the runnable interpreter is not the system Python
- the suite depends on the parent-level `venv`

Impact:
- contributors can think tests are unavailable or broken when the real issue is interpreter selection

Status:
- reproducible
- should be documented or scripted

### 3. Slow or blocking test module

Problem area:
- `utilities/test_inventory_finance_flows.py`

Observed behavior:
- in a per-file sweep with a `45s` timeout, this file did not complete and exited `124`
- a `-vv` run showed the file collecting `37 items` and stalling very early in execution
- this indicates the module is significantly slower than the rest of the suite and may contain one or more blocking or very expensive tests/setup paths

Impact:
- full-suite confidence runs become harder to trust
- longer regression cycles reduce feedback speed during Phase 5 fix/retest work

Status:
- not yet classified as a functional failure
- classified as a stability/performance concern for the harness

## Per-File Baseline Snapshot

Files confirmed green in isolated runs:
- `purchase/test_addpurchase.py`
- `purchase/test_po_grn_flow.py`
- `sales/test_createsales.py`
- `tests/test_accounting_settings_service.py`
- `tests/test_daily_session_service.py`
- `tests/test_feature_daily_session_widget_flow.py`
- `tests/test_feature_finance_transaction_widget_flow.py`
- `tests/test_feature_grn_widget_flow.py`
- `tests/test_feature_po_widget_flow.py`
- `tests/test_feature_purchase_widget_flow.py`
- `tests/test_feature_return_widget_flow.py`
- `tests/test_feature_sales_transaction_service.py`
- `tests/test_grn_posting_service.py`
- `tests/test_inventory_movement_service.py`
- `tests/test_product_admin_service.py`
- `tests/test_product_catalog_service.py`
- `tests/test_purchase_order_service.py`
- `tests/test_purchase_posting_service.py`
- `tests/test_purchase_return_service.py`
- `tests/test_purchase_transaction_service.py`
- `tests/test_report_service.py`
- `tests/test_return_transaction_service.py`
- `tests/test_sales_items_service.py`
- `tests/test_sales_posting_service.py`
- `tests/test_sales_pricing_policies.py`
- `tests/test_sales_return_service.py`
- `tests/test_sales_transaction_service.py`
- `tests/test_service_sqlite_integration.py`
- `tests/test_stock_adjustment_service.py`
- `utilities/test_get_session.py`
- `utilities/test_permissions.py`
- `utilities/test_session_service.py`

Files with known issues:
- `tests/test_purchase_items_service.py`
  - `1 failed, 5 passed`
- `utilities/test_inventory_finance_flows.py`
  - slow/blocking under baseline timeout investigation

## Phase 2 Conclusion

The current automated suite is valuable and broad, but the baseline is not yet clean enough to act as a strong production gate.

Current status:
- test inventory exists and collects to `262` tests
- most isolated files are green
- one concrete functional regression is present in purchase expiry parsing
- the suite requires environment-specific invocation to collect cleanly
- at least one late utility-heavy test module is too slow or unstable for comfortable regression usage

## Recommended Next Actions

Before or during early Phase 3 work, the following should be addressed:

1. document or script the canonical test command using `../venv/bin/python` and `PYTHONPATH=..`
2. resolve the purchase expiry parsing regression or update the test/spec if product behavior intentionally changed
3. isolate the exact slow test or setup path inside `utilities/test_inventory_finance_flows.py`
4. rerun the full suite after those fixes to produce a clean automated baseline

## Release Readiness Implication

At the end of Phase 2, the desktop app is not yet certifiable for production readiness because:
- the automated baseline is not fully green
- the suite invocation is fragile
- one inventory-related regression is already confirmed
- one utility-heavy regression lane is not yet stable enough for dependable repeated runs
