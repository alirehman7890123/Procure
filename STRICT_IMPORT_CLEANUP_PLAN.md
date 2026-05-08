# Strict Import Cleanup Plan

Goal: remove transitional runtime fallbacks and make the app rely on a single
internal import model:

```python
from medic....
```

## Current State

Feature migration is largely complete. The remaining structural ambiguity is
concentrated in the startup and packaging boundary, not in the feature layout.

The remaining fallback-dependent files are:

- `starting.py`
- `utilities/mylogin.py`
- `dashboard/dashboard.py`
- `services/scheduled_price_service.py`
- `utilities/app_theme.py`
- `utilities/__init__.py`
- `services/__init__.py`

These are the only active code paths still using one or more of:

- `try/except ModuleNotFoundError` import fallbacks
- `_import_symbol(...)`
- synthetic `medic` package registration
- top-level fallback namespaces such as `utilities.*`, `services.*`,
  `features.*`, `dashboard.*`, `reports.*`

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

These are the most important files because they decide whether the app even
boots.

- `starting.py`
  - contains `_import_symbol(...)`
  - contains synthetic `medic` registration for source execution
  - still resolves startup services/widgets through fallback module names

- `utilities/mylogin.py`
  - contains `_import_symbol(...)`
  - lazily resolves most page factories through fallback module names
  - lazy-loads scheduled-price services through fallback names

### Tier 2: Runtime Module Fallbacks

- `dashboard/dashboard.py`
  - dual-path imports for utilities/services/reports/feature UI

- `services/scheduled_price_service.py`
  - dual-path imports for `activity_logger` and `product_admin_service`

- `utilities/app_theme.py`
  - dual-path import for `accounting_settings_service`

### Tier 3: Transitional Namespace Alias Files

- `utilities/__init__.py`
  - still conditionally registers `medic` and `medic.utilities`

- `services/__init__.py`
  - still conditionally registers `medic` and `medic.services`

These files are helpful for compatibility today, but they should disappear once
the runtime package surface is stable.

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
5. `starting.py`

Reasoning:

- start with narrow service/module fallbacks
- then remove the broader shell fallbacks last

### Phase 3: Remove Synthetic Namespace Registration

After the app is running cleanly with strict `medic...` imports:

1. delete synthetic `medic` registration from `starting.py`
2. delete alias logic from `utilities/__init__.py`
3. delete alias logic from `services/__init__.py`

At that point, the packaged app either exposes `medic` correctly or fails
cleanly, which is the architecture we want.

### Phase 4: Simplify the Spec

Once fallback imports are gone:

- remove top-level fallback collections from `ProcureMedic.spec`
  - `utilities`
  - `services`
  - `features`
  - `dashboard`
  - `reports`
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

1. stabilize the packaged runtime one level further
2. verify `medic.*` imports are consistently available in the frozen app
3. begin strict fallback removal with:
   - `services/scheduled_price_service.py`
   - `utilities/app_theme.py`
   - `dashboard/dashboard.py`

Only after those succeed should we cut over `utilities/mylogin.py` and
`starting.py`.

## Success Criteria

The cleanup is complete when:

- no production `.py` file contains `except ModuleNotFoundError` for import
  fallbacks
- no production `.py` file contains `_import_symbol(...)`
- no production `.py` file imports `utilities.*`, `services.*`, `features.*`,
  `dashboard.*`, or `reports.*` as top-level fallback surfaces
- the packaged app boots, logs in, opens the shell, and loads major screens
  using only `medic...` imports
