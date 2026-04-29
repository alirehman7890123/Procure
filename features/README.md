# Feature Architecture

This project is moving from screen-folder ownership toward feature ownership.

The next stage should optimize for one clear source of truth:

- one canonical package root: `medic`
- one final import style: `from medic...`
- one primary ownership model: `medic.features.*`

The app is still in a transitional state right now, so this file defines the
target shape and the migration rules we want to follow from here.

## Source Of Truth

The final app structure should be organized around these boundaries:

- `medic.features.*`
  Feature-owned UI and feature orchestration.
- `medic.services.*`
  Shared reusable business logic used by more than one feature.
- `medic.utilities.*`
  Framework helpers, dialogs, theme, widgets, permissions, session helpers,
  and infrastructure support.
- legacy top-level screen folders such as `sales/`, `purchase/`, `transaction/`
  Transitional compatibility only until migration is complete.

The long-term rule is:

- internal imports should use `from medic...`
- feature modules should be the primary app-facing paths
- legacy folders should stop being active implementation owners

## Final Package Direction

The intended final shape is:

```text
medic/
  features/
    admin/
      ui/
      services/
    finance/
      ui/
      services/
    purchase/
      ui/
      services/
    inventory/
      ui/
      services/
    sales/
      ui/
      services/
    parties/
      customer/
      supplier/
    dashboard/
      ui/
      services/
    reports/
      ui/
      services/
    payroll/
      ui/
      services/
    returns/
      purchase/
      sales/
  services/
  utilities/
  tests/
```

This is still an incremental target, not a big-bang rewrite.

## What Stays Shared

Not everything should move out of `medic.services`.

Shared `medic.services` modules are still the right place for logic that is:

- reused by more than one feature
- domain-heavy but not UI-owned
- important to keep stable while feature folders mature

Examples:

- accounting settings
- inventory movement
- scheduled price changes
- media storage helpers
- transaction posting helpers used across multiple screens

So the final model is not “everything must move under `features`”.
It is:

- features own screens and feature orchestration
- shared services stay shared
- legacy screen folders stop owning real behavior

## Current Migration State

These feature groups already exist and should be treated as the main ownership
direction:

1. `features/admin/`
2. `features/finance/`
3. `features/purchase/`
4. `features/inventory/`
5. `features/sales/`

Current practical status:

- `admin`: strong
- `finance`: strong
- `purchase`: strong
- `inventory`: solid
- `sales`: in progress, but the hardest structural move is already done

The least-finished feature area is still `sales`, especially around
`features/sales/ui/create_sales.py`.

## Transitional Rules

Until migration is finished:

- keep shims only where they reduce risk
- do not create new top-level legacy implementations unless necessary
- do not let compatibility files become permanent owners again
- avoid mixing packaging fixes with broad behavior refactors in the same step

Transitional modules are allowed to exist, but they should be understood as:

- temporary adapters
- not the final source of truth

## Import Rules

### Final rule

All internal imports should eventually be:

```python
from medic....
```

### Transitional exception

During migration only, small defensive fallbacks may exist for:

- packaged startup safety
- legacy compatibility boundaries

But those should be treated as temporary hardening, not final architecture.

## Packaging Guidance

The packaged app problems are a sign that the repo is still in a mixed
transitional import state.

That does **not** mean feature architecture is wrong.
It means:

- feature migration is incomplete
- package boundaries are still eager in some places
- old and new import paths are still mixed during startup

So the right response is:

1. finish feature ownership more cleanly
2. reduce eager package imports
3. remove unnecessary compatibility layers
4. normalize imports to `medic...`
5. then tighten packaging

## Best Completion Order

From here, the safest order is:

1. finish the remaining `sales` feature cleanup
2. make package `__init__.py` files light and non-eager
3. decide which shared services stay in `medic.services`
4. reduce feature bridge/shim usage where ownership is already stable
5. migrate any remaining unfinished domains into feature ownership
6. remove transitional legacy modules in batches
7. normalize the repo to strict `from medic...` imports
8. do final packaging hardening only after that structure is stable

## Screen And Module Ownership Rules

A module should count as feature-owned when:

- its real implementation lives under `medic.features.*`
- old locations are only compatibility wrappers
- feature UI imports mostly stay within the feature or shared `medic.services`
- cross-feature imports are intentional and limited

A module should count as transitional when:

- it still lives in a legacy top-level screen folder
- it still re-exports a feature-owned implementation
- or it still exists only to preserve old import paths

## Success Criteria

We should consider the migration structurally complete when:

- each major business area is understandable mostly from one feature folder
- top-level legacy screen folders no longer own real implementations
- package `__init__.py` files no longer pull half the app into startup
- internal imports are consistently `from medic...`
- packaging does not need broad fallback behavior to boot
