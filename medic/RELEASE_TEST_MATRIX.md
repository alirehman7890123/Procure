# Medic Release Test Matrix

This matrix is the working release checklist for the current desktop `medic` version before rollout to a small group of customers.

The goal is not to test everything equally. The goal is to catch failures that would:
- lose money
- corrupt stock
- corrupt balances
- block daily operator workflows
- break receipt or session workflows during real use

## Release Gate

Treat these as release blockers for the pilot build:
- Any failed `Critical` test
- Any failed `High` test in sales, purchase, GRN, session, or finance posting
- Any stock mismatch
- Any customer or supplier balance mismatch
- Any save flow that can duplicate or partially save a transaction

## Test Run Rules

- Test on a copy of a realistic database when possible.
- Record the build date and commit before starting.
- Run each `Critical` flow at least once with fresh app startup.
- Re-test any related flow after fixing a failure.
- Capture screenshots for any broken receipt, totals mismatch, or blocked screen.

## Test Environment

Fill this before running:

- Build / commit:
- Tester:
- Test date:
- Machine / OS:
- Database used:
- Printer used:
- Barcode scanner used:

## Status Key

- `Pass`
- `Fail`
- `Blocked`
- `Not Run`

## Severity Key

- `Critical`: can lose money, corrupt stock, or block operations
- `High`: major workflow break or wrong business state
- `Medium`: workflow still usable but damaged or confusing
- `Low`: polish or non-blocking issue

## 1. Sales

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| S-01 | Critical | Cash sale, single item | Add one stocked item, full payment, save receipt | Sale saves once, stock reduces correctly, receipt opens/prints, totals match screen | Not Run | |
| S-02 | Critical | Cash sale, multiple items | Add 3 or more items with different rates and quantities, full payment, save | One receipt saved, all line totals correct, stock reduces for every row | Not Run | |
| S-03 | Critical | Credit sale | Use saved customer, receive partial amount, save | Sale saves, remaining amount recorded, customer receivable updated correctly | Not Run | |
| S-04 | Critical | Walk-in customer with remaining amount blocked | Use walk-in customer and try to leave remaining balance | App blocks invalid save or forces full payment/writeoff rule correctly | Not Run | |
| S-05 | Critical | Hold sale and reload | Put sale on hold, load it back, complete save | Held sale reloads same items/totals, final save succeeds once | Pass | Automated: hold persistence + reload widget flow |
| S-06 | Critical | Low stock protection | Try to sell more than available stock | App blocks save and no partial stock deduction occurs | Pass | Automated: sale item save path rejects insufficient stock |
| S-07 | Critical | FIFO stock deduction | Sell item with multiple batches | Deduction follows expected batch order and sold batch records are correct | Pass | Automated: FIFO posting orchestration service tests |
| S-08 | High | Discount and tax combinations | Test line discount, header discount, line tax, header tax, mixed settings | Saved totals match UI totals and printed totals | Pass | Automated: pricing/totals services and receipt render payload checks |
| S-09 | High | Quick-add customer in sale | Add new customer from sale screen and complete sale | Customer saves, appears in combo, sale posts correctly | Not Run | |
| S-10 | High | Quick-add manufacturer helper | Add manufacturer through sales helper flow if used | Helper saves cleanly and no later save failure occurs | Not Run | |
| S-11 | High | Thermal receipt export | Save sale with thermal receipt path | Thermal PDF/print renders item names, qty, totals, and header correctly | Pass | Automated smoke: export path writes file without crash |
| S-12 | High | Standard receipt export | Save sale with standard invoice export | Standard PDF renders correct business, customer, item, and totals data | Pass | Automated smoke: export path writes file without crash |
| S-13 | Medium | Cancel/retry after failed sale | Force a validation failure, correct it, save again | No duplicate sale and no broken UI state remains | Not Run | |

## 2. Purchase / PO / GRN

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| P-01 | Critical | Direct purchase save | Create purchase invoice with multiple items and save | Purchase saves once, stock/batches created, supplier balance updates correctly | Pass | Automated: widget save orchestration + rollback coverage |
| P-02 | Critical | Purchase with taxes/discounts | Save purchase with discount and tax values | Saved totals match screen totals and supplier posting | Not Run | |
| P-03 | Critical | Create PO | Create purchase order with multiple items | PO saves correctly with correct totals and item rows | Pass | Automated: PO save widget flow and validation suite |
| P-04 | Critical | Full GRN against PO | Receive entire PO through GRN flow | GRN saves, PO status updates correctly, stock/batches created correctly | Pass | Automated: end-to-end PO -> GRN -> bill -> stock test |
| P-05 | Critical | Partial GRN against PO | Receive part of a PO only | GRN saves, remaining PO quantity stays available, status stays correct | Pass | Automated: partial receipt integration + validation suite |
| P-06 | High | GRN detail and list | Open GRN list and detail for saved GRNs | Screen loads correct supplier, totals, and line items | Not Run | |
| P-07 | High | PO detail linked GRN visibility | Open PO detail after receipt | Linked GRN information is visible and correct | Not Run | |
| P-08 | High | Supplier quick-add in PO | Add supplier from PO flow if used | Supplier saves correctly and can be selected immediately | Not Run | |
| P-09 | High | Due date behavior | Save purchase with due date / payable remaining | Due date persists and supplier transaction reflects correct remaining balance | Not Run | |

## 3. Finance Transactions

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| F-01 | Critical | Customer payment receive | Post customer payment against existing due | Customer transaction saves and running balance decreases correctly | Pass | Automated: widget save flow + running balance persistence tests |
| F-02 | Critical | Customer refund / overpayment case | Post scenario that creates payable/excess state | Saved balances reflect correct payable/receivable side | Pass | Automated: excess confirmation + transaction payload coverage |
| F-03 | Critical | Supplier payment | Post supplier payment against existing due | Supplier transaction saves and running balance decreases correctly | Pass | Automated: supplier save widget flow coverage |
| F-04 | Critical | Supplier receive / reverse case | Post supplier scenario that affects receivable side | Balance math is correct and no sign inversion bug appears | Pass | Automated: supplier excess/cancel flow and service coverage |
| F-05 | High | Transaction list/detail | Open transaction lists and detail pages | Detail matches saved transaction values and references | Not Run | |
| F-06 | High | Payment method variants | Test cash and at least one non-cash method | Payment metadata persists correctly | Not Run | |

## 4. Daily Session / Operational Close

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| DS-01 | Critical | Open session | Open new daily session with opening cash | Session opens once and becomes active for transaction workflows | Pass | Automated: service round-trip + widget open flow |
| DS-02 | Critical | Session-gated workflow | Try sales/purchase/finance flow with and without open session | Protected flows require active session correctly | Not Run | |
| DS-03 | Critical | Close session after activity | Run sample sales, expense, and payments, then close session | Close totals reconcile to recorded activity and closing succeeds cleanly | Pass | Automated: cash-flow summary, close persistence, and widget close flow |
| DS-04 | High | Session history | Open session history/list | History rows load and show correct dates/cash values | Pass | Automated: session history filter/service coverage |
| DS-05 | High | Dashboard session metrics | Compare dashboard values to actual session activity | Dashboard summaries match expected numbers | Not Run | |

## 5. Inventory / Product Safety

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| I-01 | High | Add product | Create a new product with required pricing fields | Product saves and appears in list/detail correctly | Not Run | |
| I-02 | High | Edit product | Update name, pricing, or tax/discount settings | Changes persist and product detail reloads correctly | Not Run | |
| I-03 | High | Opening stock product | Create product with opening stock values | Product and opening stock records save correctly | Not Run | |
| I-04 | High | Product list/detail load | Open list, search product, open detail | No broken loads, correct data visible | Not Run | |
| I-05 | Medium | Expiry / reorder visibility | Use product with low stock or expiry data | Relevant dashboard/list information appears correctly | Not Run | |

## 6. Expense

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| E-01 | High | Add expense | Create expense with normal values | Expense saves once and appears in list/detail | Not Run | |
| E-02 | High | Expense affects session totals | Add expense during active session and review close/dashboard | Expense contributes correctly to operational totals | Not Run | |
| E-03 | Medium | Expense list/detail | Open expense list and expense detail | Values render correctly with no load errors | Not Run | |

## 7. Admin / User / Permissions

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| A-01 | High | Create user | Add a user with role and credentials | User saves correctly and appears in user list | Not Run | |
| A-02 | High | Change password | Change password for existing user | Validation works and new password is accepted afterward | Not Run | |
| A-03 | High | Business profile save | Edit business profile and reopen app/screens using it | Updated business info appears in invoices and profile screens | Not Run | |
| A-04 | High | Permission checks | Test cashier/admin differences on create and restricted screens | Restricted actions are blocked correctly | Not Run | |

## 8. Reports / Dashboard Spot Checks

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| R-01 | High | Sales totals vs dashboard | Compare known test sales to dashboard totals | Dashboard matches saved sales | Not Run | |
| R-02 | High | Customer due vs transactions | Compare customer due to posted sale and customer payment flows | Reported due matches transaction history | Not Run | |
| R-03 | High | Supplier due vs purchase/finance | Compare supplier due to purchases and supplier payments | Reported due matches transaction history | Not Run | |
| R-04 | Medium | Low stock / expiry widgets | Seed relevant data and inspect dashboard/report output | Results are present and believable | Not Run | |

## 9. Printing / Output

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| PR-01 | High | Sales thermal print layout | Print short and long invoices | Layout remains readable and totals are visible | Not Run | |
| PR-02 | High | Sales standard PDF layout | Export standard invoice PDF | PDF opens and all fields match receipt data | Not Run | |
| PR-03 | Medium | Purchase / PO print outputs | Export any available purchase-side document | Output opens and key fields are correct | Not Run | |

## 10. Smoke After Fresh Startup

| ID | Severity | Test Case | Steps | Expected Result | Status | Notes |
|---|---|---|---|---|---|---|
| SM-01 | Critical | App startup | Launch app and log in as admin | App opens without import/runtime crash | Not Run | |
| SM-02 | Critical | Open all major modules once | Open Sales, Purchase, PO, GRN, Transaction, Expense, Dashboard, Users | No screen crashes on first load | Not Run | |
| SM-03 | High | Reopen after data changes | Restart app after running sample transactions | Previously saved data loads cleanly | Not Run | |

## Suggested Execution Order

1. `SM-01` to `SM-03`
2. `DS-01` and `DS-02`
3. `S-01` to `S-07`
4. `P-01` to `P-05`
5. `F-01` to `F-04`
6. `DS-03` to `DS-05`
7. `I-01` to `I-04`
8. `E-01` to `E-03`
9. `A-01` to `A-04`
10. `R-01` to `R-04`
11. `PR-01` to `PR-03`

## Pilot Release Rule

For a small-customer release, I would want:
- all `Critical` tests passing
- no unresolved stock mismatch
- no unresolved balance mismatch
- no startup/import crash
- no receipt export crash
- no duplicated save behavior in sales, purchase, GRN, or finance posting
