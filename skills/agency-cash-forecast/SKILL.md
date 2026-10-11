---
name: agency-cash-forecast
description: "Projects agency cash by day, week or month from bank balances, AR/AP open items, cheques, the client-approved unbilled pipeline, payroll, capex and adjustments, with expected date = due or billing date + terms + chronic delay. Use for liquidity planning. Do not treat revenue or invoices as cash, and never post or pay; snapshots are planning only."
---

# Cash Forecast

This stage reads balances and open items produced by receivables, payables, treasury and the approved-but-unbilled pipeline (production estimates, media plans, fee contracts), and feeds payment-run sizing, collections priorities and financing decisions. It owns the cash-flow snapshot (`Cash Flow Previsional`) and its scenario variants. A snapshot never posts accounting entries, never alters source transactions and is not refreshed by later transactions; it never moves money.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [management-security.md](references/erp/management-security.md) (P-CF-01 to P-CF-12, rules R-CF 1–17, §6, §10.1–10.4 cashflow jobs and exceptions, gaps 2 and 8) and [payables-treasury.md](references/erp/payables-treasury.md) (payment lists P9–P10 and locks rules 5–7, release date rule 21, availability rule 26, payment-delay rule 28, aging rule 29, cheques P25–P26, gap 3 pay-when-paid).

## Use when
- "Cash flow", "flujo de caja", "Cash Flow Previsional", "will we cover payroll / the Friday payment run?", "liquidity gap".
- Building a daily, weekly or strategic (monthly) projection from actual balances and open items.
- Dating the approved-unbilled pipeline: estimated billing dates (`Fecha Fact.`) for pass-through sale and agency service, and supplier invoice dates for pending costs.
- Adding payroll, expenses, recurring outflows, capex, capital moves and net adjustments.
- Rolling forward a previous snapshot or stress-testing delayed collections.
- Checking which suppliers stay unpaid after the related client collection (pay-when-paid view).

## Do not use when
- Approving or releasing payments, payment lists or bank files → agency-payment-run.
- Recording receipts, deposits, bank charges or reconciliations → agency-cash-settlement or agency-collections.
- Profit, margin or gross income analysis → agency-profitability; monthly pack and KPIs → agency-management-reporting.
- FX revaluation entries → agency-accruals-revaluation.
- Tax position amounts or filings → agency-tax-compliance.

## Required inputs
- **Blocking:** tenant, as-of date, granularity (daily, weekly, strategic), horizon, currencies with exponents, holiday calendar for the fiscal year (R-CF 7).
- **Blocking:** opening liquidity = book balance of bank and cash accounts (`Disponibilidades líquidas`) per currency, from active accounts with the right observation codes (R-CF 2–3).
- **Blocking:** open AR and AP items with due dates, documents receivable, cheques in portfolio and post-dated cheques payable, obligations payable; ideally taken after the scheduled payment run (R-CF 15).
- Chronic delay days per customer and supplier (`Días de Atraso Crónico`) and usual payment terms (P-CF-02).
- Client-approved estimates, media plans and fee instalments with estimated billing dates; approved items without a date are excluded (R-CF 9).
- Payroll and social charges, other expenses and income, recurring outflows (frequency, payment days, currency), capex purchases and sales, capital moves, VAT payment day.
- Scenario policy: probabilities for expected items, stress cases. Ask only for missing material inputs. Never ask for credentials or bank logins in chat.

## Procedure
1. Fix the snapshot header: type, as-of date, currencies, horizon (daily 15 business or 20 calendar days per the conflicting reference, gap 2, configurable; weekly 15 Mondays; strategic 15 months), notes, and whether to copy forward a previous snapshot of the same type (R-CF 13).
2. Read opening liquidity per currency. Keep bank cash, values to deposit, undeposited third-party cheques and processor balances on separate lines; only cleared funds are opening cash.
3. Load AR open items: expected date = due date + customer chronic delay (R-CF 4). Load AP open items: due date + supplier chronic delay. Show multiple control accounts separately (R-CF 16).
4. Date the pipeline: for each client-approved, unbilled estimate, plan or fee instalment, expected collection = estimated billing date + customer usual term + chronic delay (R-CF 5; P-CF-05). Media and production carry separate dates for pass-through sale and agency service. Supplier side: estimated supplier invoice date + supplier term + delay (P-CF-06). Exclude pending-approval and rejected items, and list approved items without dates as `undated_pipeline` (§10.4).
5. Use `payment_terms` to compute and check individual due and expected dates with the holiday calendar and weekend roll (R-CF 7). The `end_of_month_then_days` and `next_fortnight` rules are tool options; use them only when the counterparty's terms say so.
6. Add manual lines: payroll and social charges per month, other expenses and income (positive = outflow), recurring outflows (expense contracts are not read automatically, R-CF 17), capex (payment = purchase date + supplier terms + delay, R-CF 6), capital increases and decreases, the read-only VAT position on the configured day (R-CF 11), and net adjustments without detail (R-CF 12).
7. Apply expected withholdings per party as a percentage or manual amount to reduce net cash (R-CF 10); rates come from the host tax configuration.
8. Run `cash_projection` per currency with `granularity` week or month. For daily views, compute dates with `payment_terms` and sum by day; `cash_projection` has no daily mode. Mark items `confirmed` (probability 10000) or `expected` with a documented probability.
9. Read `overdue_in_minor` and `overdue_out_minor` (moved to as-of), `beyond_horizon_*` (the `Posterior` column, R-CF 8) and `minimum_closing_minor` with its period. Projected balance = previous + inflows − outflows (R-CF 14).
10. Build the supplier-exposure view: payables whose related client invoice is collected vs not collected, from receipts evidence. Pay-when-paid is evidence, not an enforced rule in the reference (gap 3).
11. Stress-test: delayed collections (extra delay days), lower pipeline probabilities, disputed deliveries, cancellation costs. Keep each scenario as a separate snapshot variant.
12. Return the snapshot, liquidity gaps and draft actions (collection follow-ups, payment-run sizing, financing request). Each action goes to its own workflow and approval.

## Rules and locks
- Snapshots are planning only: no journal entries, no change to source transactions, no automatic refresh (R-CF 13).
- Refresh means a new snapshot copied from the last one of the same type; delete a snapshot only if it was never used as a copy source (P-CF-12).
- Only client-approved estimates, plans and fees enter the pipeline; approved items without an estimated billing date are excluded and must be listed (R-CF 9).
- Expected dates on holidays or weekends roll to the next business day (R-CF 7).
- Items locked in a provisional payment list or unreleased payment order remain unpaid in reports; do not count them as paid until released (payables-treasury rules 6, 21).
- The accounting date of a payment is the release date, not the payment-order date (payables-treasury rule 21).
- Availability = book balance + deposited collections − cheques in transit − transfers in transit; the reference wording is loose (payables-treasury rule 26, gap 16) (confirm locally).
- Fixed default delays (client 40 days, supplier collection + 7) are reference parameters only (payables-treasury rule 28) (configurable).
- Currencies stay separate unless an approved dated FX policy supports consolidation; never assume a rate.
- Do not double count a client payment in both a processor event and a bank receipt, or an AR item and the pipeline line that produced it.

## Calculations
- `cash_projection`: weekly or monthly buckets from `opening_balances` and `items` (direction, amount, base date, term days, delay days, confirmed or expected with `probability_bps`); returns per-period confirmed/expected in and out, closing balance, overdue, beyond-horizon and minimum closing.
- `payment_terms`: one item's due and expected date from base date, `term_days`, rule, `delay_days`, holidays and weekend roll; use for daily views and to audit pipeline dates.
- `aging`: bucket AR or AP open items by days past due (ascending `bucket_limits_days`, for example 30, 60, 90) to explain overdue inflows and outflows.

```sh
python3 scripts/agency_tools.py cash_projection < input.json
```
```json
{"as_of": "2026-10-12", "granularity": "week", "periods": 6, "holidays": ["2026-11-02", "2026-11-16"],
 "opening_balances": [{"currency": "MXN", "amount_minor": 180000000}],
 "items": [
  {"item_id": "AR-881", "currency": "MXN", "direction": "in", "amount_minor": 95000000, "base_date": "2026-09-30", "term_days": 30, "delay_days": 10, "status": "confirmed", "probability_bps": 10000},
  {"item_id": "PIPE-E0042", "currency": "MXN", "direction": "in", "amount_minor": 60000000, "base_date": "2026-10-31", "term_days": 30, "delay_days": 10, "status": "expected", "probability_bps": 8000},
  {"item_id": "AP-311", "currency": "MXN", "direction": "out", "amount_minor": 140000000, "base_date": "2026-10-05", "term_days": 15, "delay_days": 0, "status": "confirmed", "probability_bps": 10000},
  {"item_id": "PAYROLL-10", "currency": "MXN", "direction": "out", "amount_minor": 85000000, "base_date": "2026-10-30", "term_days": 0, "delay_days": 0, "status": "confirmed", "probability_bps": 10000}]}
```
- Not calculated by tools: FX rates and consolidation, VAT position (read from tax records), withholding rates, probabilities (policy), interest on overdue.

## Approvals and segregation of duties
- Treasury prepares the snapshot; the CFO reviews assumptions and scenarios. Drafting needs no approval.
- Collection messages, supplier payment changes, financing, refunds and transfers each need their owning workflow and an authenticated human approval bound to the payload digest; the preparer does not approve. The forecast cannot authorize any payment.

## Exceptions to escalate
- Minimum closing balance below zero or below the agency buffer → CFO; payment-run sizing → agency-payment-run.
- Approved pipeline without estimated billing dates → account team and agency-client-billing.
- Ledger accounts missing observation codes, so a concept is silently empty → agency-general-ledger.
- Holidays not configured for the year → controller.
- No previous snapshot of the same type for copy-forward → build fresh and note it.
- Supplier overdue or claiming while the related client is uncollected → agency-collections and treasury.
- Rejected cheques or cheques issued but not picked up → agency-cash-settlement.
- Mixed currencies without an approved FX policy → CFO; keep separate.

## Return and handoff
Return `cash_forecast`, `currency_buckets`, `undated_pipeline`, `collection_scenarios`, `supplier_exposure`, `liquidity_gaps`. Include tenant and client IDs where relevant, snapshot number and type, as-of date, horizon, currencies, source references and extraction times, assumptions, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), blockers, approvals required and next stage.
**Owner:** CFO / treasury. **Next:** agency-payment-run, agency-collections, agency-management-reporting.

## Connectors and files
- Bank and ledger balances, open invoices and bills: `xero`, `quickbooks`; processor settlements: `stripe`, `paypal` (balances are not cash until paid out); Mexican reference FX for scenarios: `banxico-sie`. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` for supplier and client invoice extracts; other kinds plan|broadcast-order|emission|ooh|rating. Bank statements and aging exports arrive as values-only CSV and stay unverified evidence.
