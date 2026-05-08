# Postgres Portability Audit

Goal: identify what still prevents an eventual move from SQLite to PostgreSQL
after UI/data-access separation is complete.

## Current Position

The codebase is in a much better place than before:

- feature UI files are being stripped of direct SQL
- most active queries now live in `services/*`
- that means future database migration work is becoming concentrated and
  realistic

This is the right direction.

But moving SQL out of UI does **not** by itself make the app Postgres-ready.
The main remaining migration work is now inside the service layer.

## Audit Summary

The main portability risks are:

1. SQLite-specific date/time functions and string-based date parsing
2. runtime schema migrations implemented with SQLite `PRAGMA` / `ALTER TABLE`
3. SQLite-oriented ID assumptions such as `lastInsertId()` / autoincrement flows
4. SQLite-specific aggregate functions like `GROUP_CONCAT`
5. SQL embedded directly in service/business methods rather than behind a
   narrower repository/data-access layer

## Risk Categories

### Tier 1: Highest Migration Risk

These areas will need deliberate redesign or SQL rewrites for PostgreSQL.

#### 1. Date/time math and localtime SQL

Common patterns found:

- `date('now', 'localtime')`
- `datetime('now','localtime')`
- `julianday(...)`
- `strftime(...)`
- expiry parsing with `substr(...)`

Heavily affected modules include:

- `services/product_catalog_service.py`
- `services/inventory_movement_service.py`
- `services/purchase_order_service.py`
- `reports/report_service.py`

Why this matters:

- SQLite date functions are not portable to PostgreSQL
- many date comparisons currently depend on text-stored dates plus SQLite
  parsing tricks
- PostgreSQL will want proper date/timestamp columns and different expressions

Recommended direction:

- normalize date storage formats first
- move complex date expressions into helper functions or repository methods
- avoid embedding SQLite date syntax directly in business service methods

#### 2. Runtime schema migration logic

Patterns found:

- `PRAGMA table_info(...)`
- `ALTER TABLE ... ADD COLUMN ...`
- `CREATE TABLE IF NOT EXISTS ...`
- `CREATE INDEX IF NOT EXISTS ...`

Affected modules include:

- `services/sales_transaction_service.py`
- `services/product_media_service.py`
- `services/financial_closing_service.py`
- `services/scheduled_price_service.py`
- `utilities/database.py`
- `reports/report_service.py` (`reminder_state`)

Why this matters:

- these are tightly coupled to SQLite behavior
- PostgreSQL migration should eventually move schema management out of runtime
  service code and into a migration system

Recommended direction:

- keep runtime SQLite migrations for now if needed
- long term, move schema changes into explicit migration scripts
- separate “app boot migration” concerns from domain service logic

### Tier 2: Medium Migration Risk

These are portable in concept, but still need query rewrites or design cleanup.

#### 3. Aggregate/query idioms tied to SQLite

Patterns found:

- `GROUP_CONCAT(...)`
- heavy `COALESCE(...)` use with text-number coercion assumptions
- `CAST(... AS TEXT)` for barcode/code matching
- `SUBSTR(...)`-based number extraction

Affected modules include:

- `services/sales_detail_service.py`
- `services/product_admin_service.py`
- `services/purchase_order_service.py`
- `reports/report_service.py`

Why this matters:

- PostgreSQL equivalents exist, but not always with the same syntax
- some current queries depend on SQLite’s permissive typing and text handling

Recommended direction:

- isolate these into dedicated query helpers
- avoid mixing type-normalization tricks into business workflow code

#### 4. SQLite-oriented ID flows

Patterns found:

- `query.lastInsertId()`
- `PRIMARY KEY AUTOINCREMENT`

Affected in many services, including:

- `services/sales_transaction_service.py`
- `services/product_write_service.py`
- `services/grn_transaction_service.py`
- `services/purchase_order_service.py`
- `services/supplier_service.py`
- `services/employee_service.py`

Why this matters:

- PostgreSQL supports returning inserted IDs, but the mechanism is different
- this is manageable, but it should be abstracted eventually

Recommended direction:

- keep it for now
- later wrap insert-and-return-id behavior in a DB adapter/repository layer

### Tier 3: Lower Risk / Mostly Normal SQL

These are not the real blockers:

- standard joins
- `COALESCE(...)`
- basic `LIMIT ... OFFSET ...`
- simple inserts/updates/deletes

These will still need syntax review, but they are not the hard part.

## Recommended Next Architecture Step

After “no SQL in UI”, the next sensible target is:

## Introduce a narrower data-access boundary

Suggested shape:

- `features/*/ui`
  - presentation only
- `services/*`
  - business workflows, validation, orchestration
- future `repositories/*` or `data_access/*`
  - raw SQL and DB-dialect-specific queries

This does **not** need to be a huge rewrite immediately.

A practical gradual approach is:

1. keep removing SQL from UI
2. stop growing raw SQL directly in service workflow functions
3. start extracting the most DB-specific service queries into dedicated query
   modules

## Priority Backlog

### Phase 1: Finish UI Separation

- remove any remaining live SQL from feature UI files
- remove dead commented SQL blocks from return detail screens

### Phase 2: Isolate SQLite-heavy Services

Start with the most SQLite-specific service/query surfaces:

1. `reports/report_service.py`
2. `services/product_catalog_service.py`
3. `services/inventory_movement_service.py`
4. `services/purchase_order_service.py`
5. `services/sales_detail_service.py`

### Phase 3: Separate Schema Concerns

Extract runtime schema logic away from domain services where possible:

- `services/sales_transaction_service.py`
- `services/product_media_service.py`
- `services/financial_closing_service.py`
- `services/scheduled_price_service.py`

### Phase 4: Create DB-Portability Layer

Possible future modules:

- `repositories/product_repository.py`
- `repositories/sales_repository.py`
- `repositories/report_repository.py`
- `repositories/migration_support.py`

## Practical Conclusion

Yes, your current goal is sensible.

Removing SQL from UI is the correct first step for a future PostgreSQL move.
And now that the UI is getting thinner, the remaining migration problem is
visible and manageable:

- not “the whole app”
- mostly the service/query layer
- especially date logic, schema logic, and SQLite-specific query idioms

That means the project is moving in the right direction.
