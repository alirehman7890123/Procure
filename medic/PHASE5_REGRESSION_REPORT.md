# Medic Desktop Phase 5 Regression Report

This report records the Phase 5 checkpoint for defect-closure validation and regression-pack definition for the desktop `medic` app.

Scope:
- in scope: desktop `medic`
- out of scope: `mobile/`

## Phase 5 Goal

Phase 5 answers three questions:
- did the defects fixed in earlier phases stay fixed under rerun
- which tests should become the ongoing release-safety regression pack
- what do those reruns mean for current release confidence

## Defect Areas Revalidated

The following previously problematic areas were rerun directly:

### 1. Purchase expiry normalization and purchase save path

Command:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q \
  tests/test_purchase_items_service.py \
  tests/test_feature_purchase_widget_flow.py
```

Result:
- `21 passed`

Meaning:
- the expiry parsing regression remains fixed
- purchase row normalization and purchase widget save behavior remain green

### 2. Sales transaction helper/runtime path

Command:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q \
  tests/test_sales_transaction_service.py \
  tests/test_feature_sales_transaction_service.py \
  utilities/test_inventory_finance_flows.py::test_persist_sales_customer_transaction_updates_running_balance
```

Result:
- `5 passed`

Meaning:
- the missing sales transaction helper imports remain fixed
- customer transaction running-balance persistence remains green

### 3. Financial-close runtime and UI module compatibility

Runtime smoke:

```bash
PYTHONPATH=.. ../venv/bin/python - <<'PY'
import starting
from medic.features.finance.ui.financial_close_page import FinancialClosingPage
from medic.features.finance.ui.financial_close_list import FinancialClosingListPage
from medic.features.finance.ui.financial_quarter_summary import FinancialQuarterSummaryPage
print('phase5_runtime_smoke_ok')
PY
```

Result:
- `phase5_runtime_smoke_ok`

Meaning:
- startup/bootstrap compatibility and financial-close module imports remain clean

### 4. Full financial-close regression lane

Command:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q utilities/test_inventory_finance_flows.py
```

Result:
- `37 passed`

Meaning:
- the formerly unstable and failure-prone financial-close utility lane remains fully green

## Phase 5 Regression Pack

The following pack should be treated as the release-safety rerun set after future fixes in related areas:

### Core defect-closure pack

- `tests/test_purchase_items_service.py`
- `tests/test_feature_purchase_widget_flow.py`
- `tests/test_sales_transaction_service.py`
- `tests/test_feature_sales_transaction_service.py`
- `utilities/test_inventory_finance_flows.py`

### Broader critical flow pack

This should be rerun after changes affecting money, stock, balances, sessions, GRN, returns, or finance:

- `tests/test_feature_daily_session_widget_flow.py`
- `tests/test_feature_finance_transaction_widget_flow.py`
- `tests/test_feature_grn_widget_flow.py`
- `tests/test_feature_po_widget_flow.py`
- `tests/test_feature_purchase_widget_flow.py`
- `tests/test_feature_return_widget_flow.py`
- `tests/test_feature_sales_transaction_service.py`
- `tests/test_service_sqlite_integration.py`
- `purchase/test_po_grn_flow.py`
- `sales/test_createsales.py`

### Full automated gate

For a serious release candidate, the full gate remains:

```bash
PYTHONPATH=.. ../venv/bin/python -m pytest -q
```

Current result from prior phase:
- full suite `262 passed`

## Defect Closure Summary

Previously addressed issues that now hold green under Phase 5 rerun:

1. purchase expiry normalization no longer drops valid stored expiry data just because time passed
2. automated runs no longer block on bootstrap admin modal dialogs
3. sales transaction helper/runtime `NameError` defects are resolved
4. financial-close runtime, compatibility, audit/history, and reopen flows are stable
5. fresh bootstrap schemas now support the summary/reporting regression lane that financial-close relies on

## Release Implication

Phase 5 materially improves confidence because the defects were not only fixed once, but survived focused reruns in the exact areas where they previously failed.

Current implication:
- the project now has a meaningful regression pack, not just a green snapshot
- the highest-risk fixed areas are repeatably testable
- future work can be validated faster and with less ambiguity

## Remaining Reality Check

Phase 5 does not replace the need for manual/live validation of:
- full desktop UI walkthroughs
- payroll behavior
- CRUD-heavy screen flows
- visual report/dashboard correctness
- printed output readability

But it does mean:
- the backend and hybrid widget/service defect-prone areas are in a much safer place than they were at the start of this effort

## Phase 5 Conclusion

Phase 5 is a successful checkpoint.

The previously failing lanes remain fixed, the financial-close cluster is stable, and the project now has a practical regression pack that should be rerun after future code changes before any serious desktop release.
