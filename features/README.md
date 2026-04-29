# Feature Architecture

This project is moving from screen/layer folders toward feature ownership.

## Goal

Keep each business area together so it is easier to reason about, change, and eventually test or move behind a backend.

Instead of spreading one feature across:

- `sales/`
- `services/`
- `reports/`
- `utilities/`

we want each feature to own its UI entry points, service helpers, and read/write logic in one place.

## Target Shape

Example layout:

```text
features/
  sales/
    ui/
    services/
    reports/
    __init__.py
  purchase/
    ui/
    services/
    __init__.py
  inventory/
    ui/
    services/
    __init__.py
  parties/
    customer/
    supplier/
  admin/
    users/
    business/
    theme/
  finance/
    transactions/
    expenses/
    financial_close/
  dashboard/
    ui/
    services/
```

This is a destination, not a big-bang rewrite target.

## Migration Rules

- Move one feature slice at a time.
- Preserve existing imports until a slice is stable.
- Prefer adapter modules over mass renames.
- Do not mix packaging changes with unrelated behavior changes.
- Move code only after the service boundary for that slice is reasonably stable.

## Best First Feature Groups

1. `features/admin/`
   Includes `userprofile`, `business`, theme/tax/discount settings.
2. `features/finance/`
   Includes `transaction`, `expense`, `financialclose`.
3. `features/purchase/`
   Includes PO, GRN, purchase, purchase return.
4. `features/sales/`
   Includes sales, sales return, held sales.
5. `features/inventory/`
   Includes product, stock adjustment, catalog/media helpers.

## First Safe Migration Pattern

For a feature such as admin:

1. Create the feature package.
2. Move service modules first.
3. Add compatibility imports where needed.
4. Move UI screens after service imports are stable.
5. Update the feature shell/base widget last.

## Success Criteria

- A feature can be opened and understood mostly from one top-level folder.
- UI, service, and read models for a feature live near each other.
- Cross-feature imports become fewer and more intentional.
- Future tests can target one feature package without dragging the whole app into scope.
