# Strict Import Cleanup Plan

Goal: remove transitional runtime fallbacks and make the app rely on a single
internal import model:

```python
from medic....
```

## Current State

Feature migration is largely complete. The remaining structural ambiguity is
concentrated in the startup and packaging boundary, not in the feature layout.

Completed cleanup already removed:

- dead legacy shell directories:
  - `business/`
  - `expense/`
  - `financialclose/`
  - `product/`
  - `transaction/`
  - `userprofile/`
- stale repo `__pycache__/` directories
- unused placeholder file:
  - `purchase/newfile.py`
- duplicate non-canonical sales pricing module:
  - `sales/pricing_logic.py`

The canonical sales pricing implementation is now only:

- `features/sales/ui/pricing_logic.py`

Completed UI/service cleanup already moved:

- `features/admin/ui/discount_settings.py`
- `features/admin/ui/tax_settings.py`

Both now use:

- `services/group_settings_service.py`

for sales group list loading, detail loading, active-group choices, and save
operations, so they no longer own direct `discount_group` / `tax_group` SQL.

- `features/sales/ui/create_sales.py` quick-product dialog now routes dormant
  product lookup, existing-product matching, and opening-stock save operations
  through `services/product_write_service.py` instead of owning its own product,
  batch, price-pack, and media transaction block.

- `features/sales/ui/create_sales.py` product-search and barcode read helpers
  now route through `services/product_catalog_service.py` for barcode lookup,
  exact-name matching, sales product search/detail reads, hold-row pricing
  defaults, and available-stock lookup. Customer credit summary rendering now
  reuses `services/sales_transaction_service.py`.

- `features/sales/ui/create_sales.py` now uses
  `services/sales_transaction_service.py` for write-transaction orchestration
  and hold-sale persistence, so the widget no longer owns the database
  transaction shell for “save receipt” and “put on hold”.

- `features/purchase/ui/add_purchase.py` now routes supplier option reads,
  supplier creation, rep option reads, rep creation, manufacturer option reads,
  manufacturer creation, previous-price lookup, and purchase quick-product
  creation through shared services instead of owning those SQL statements in the
  widget.

- feature UI files no longer own live SQL or `QSqlDatabase` transaction shells.
  The last remaining purchase-domain transaction wrappers were moved into:
  - `services/purchase_workflow_service.py`
  - `services/grn_workflow_service.py`
  - `services/stock_adjustment_service.py`
  - `services/product_admin_service.py`
  - `services/scheduled_price_service.py`

This means `features/**/*.py` is now acting as UI/orchestration only for data
access and transaction boundaries.

The remaining runtime-bootstrap focus is:

- `utilities/mylogin.py`

This file still lazy-loads page classes, but only through canonical
`medic...` module paths now.

## Why They Still Exist

They were introduced to keep the app bootable while the packaging setup was
still unstable. They are not the desired end state.

Right now they help the app survive when the frozen environment does not expose
`medic` consistently at runtime.

## Final Target

The final state should be:

- one package root: `medic`
- one import style: `from medic...`
- no synthetic package registration
- no top-level fallback namespaces in production code
- a simplified `ProcureMedic.spec` that collects only the canonical package
  surface plus explicit non-package data files

## Fallback Inventory

### Tier 1: Startup Boundary

This is the main remaining dynamic-import area affecting shell startup.

- `utilities/mylogin.py`
  - lazily resolves page factories through canonical `medic...` module names
  - no longer uses fallback namespace imports

### Tier 2: Runtime Module Fallbacks

No active runtime module fallbacks remain in the narrow service/module layer.

### Tier 3: Transitional Namespace Alias Files

Resolved:

- `utilities/__init__.py`
- `services/__init__.py`

These now act as normal package markers and no longer synthesize namespace
aliases.

## Removal Sequence

### Phase 1: Freeze the Runtime Contract

Before removing fallback code, prove these are true in the packaged app:

1. `medic` is importable at runtime in the frozen executable.
2. `medic.utilities`, `medic.services`, `medic.features`, `medic.dashboard`,
   and `medic.reports` are importable without synthetic aliases.
3. required data files are packaged explicitly:
   - `licensing/public_key.json`
   - `manufacturers.csv`
   - `master_products.csv`
   - `purchase/med-template.ods`
   - `styles/*`
   - `res/**`

This is the gating condition for strict-import cleanup.

### Phase 2: Remove Runtime Fallback Imports

Do this after the packaged app reliably imports `medic.*`.

Order:

1. `services/scheduled_price_service.py`
2. `utilities/app_theme.py`
3. `dashboard/dashboard.py`
4. `utilities/mylogin.py`

Reasoning:

- start with narrow service/module fallbacks
- then simplify shell lazy-loading last if needed

### Phase 3: Simplify the Spec

Once fallback imports are gone:

- keep:
  - `collect_submodules("medic")`
  - `collect_data_files("medic")` if still useful
  - explicit top-level asset additions

The spec should then package:

- canonical Python surface: `medic.*`
- explicit runtime assets only

## Practical Next Step

Do not remove the fallbacks blindly from all files at once.

The next correct step is:

1. rebuild the packaged runtime with canonical-only `medic.*` collection
2. verify `medic.*` imports are consistently available in the frozen app
3. if startup remains stable, decide whether `utilities/mylogin.py` should keep
   canonical lazy loading or move to more direct imports later

## Success Criteria

The cleanup is complete when:

- no production `.py` file contains `except ModuleNotFoundError` for import
  fallbacks
- no production `.py` file contains `_import_symbol(...)`
- no production `.py` file imports `utilities.*`, `services.*`, `features.*`,
  `dashboard.*`, or `reports.*` as top-level fallback surfaces
- the packaged app boots, logs in, opens the shell, and loads major screens
  using only `medic...` imports
