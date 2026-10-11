---
name: agency-accruals-revaluation
description: "Prepare month-end agency close jobs: unbilled revenue and uninvoiced cost provision, WIP, expense and overcommission provisions, FX revaluation, work-order closing and intercompany reclass, each with day-1 reversal checks. Use after pre-close. Do not post entries, pre-close or close periods, or invent rates."
---

# Agency Accruals and Revaluation

These are the batch jobs only Accounting runs once a month is pre-closed: they turn the operational state of media plans, production estimates, expense requests and overcommission pendings into the accrual-basis view of revenue, cost and FX. Upstream are agency-media-buying, agency-production, agency-expenses and agency-rebates; downstream is agency-period-close. This skill proposes each job's entry with per-OT detail and its reversal; it never posts, never pre-closes or closes a period and never supplies an exchange rate.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounting.md](references/erp/accounting.md) (P07–P13, P26, §4.4–4.6, BR-15 to BR-19, BR-28 to BR-38, E19–E35, E50, §11 gaps 3, 4, 7) · [production.md](references/erp/production.md) (§4.1 estimate states, rules 20–26 locks, override engine rules 50–60, §6 month-end accrual) · [media-buying.md](references/erp/media-buying.md) (P-OP-07 order close, P-OC-02 cut-off months, §4.6, BR-OC-00 to BR-OC-09, §6 PO/PD provisions).

## Use when
- Month-end provisions: Gross Income provision (`provisión de Gross Income`, unbilled revenue / uninvoiced cost), WIP (`trabajos en proceso`), expense provision (`provisión de gastos`), overcommission provision (`provisión de overcomisiones`).
- FX revaluation (`diferencia de cambio`) of open receivables, payables and foreign-currency GL accounts at the month-end rate.
- Work-order closing (`cierre de OT`) under the bridge-account scheme (`cuenta puente`): provisional, definitive or refundición.
- Intercompany reclassification (`reclasificación intercompany`) for reporting.
- Annulling and re-running a job after a correction, or explaining a day-1 reversal.

## Do not use when
- Pre-close, close, reopen or the fiscal-year close itself: use agency-period-close.
- Manual adjustments, templates or chart changes: use agency-general-ledger.
- Depreciation runs: use agency-fixed-assets.
- Computing overcommission pendings from contracts: use agency-rebates; VAT/IIBB positions: use agency-tax-compliance.
- Fixing estimate states or supplier choice: use agency-production; closing insertion orders: use agency-media-buying.
- Job profitability analysis: use agency-profitability.

## Required inputs
- Blocking: tenant, year and month, period × subledger states (Clients, Suppliers, Accounting must be pre-closed for GI; Clients and Suppliers for OT close), enabled features (bridge accounts, WIP, provisional circuit, divisions, intercompany).
- Blocking for FX: buy and sell rates for the last day of the month from the authoritative rate table, open foreign-currency documents and FX GL/subaccount balances with booking rates and currency exponents.
- Blocking for GI/WIP: plans and estimates with pending billing and pending supplier invoices per OT, provision start date, option flags (BR-30), provision accounts (PI, PE, PH, PC, optional PP, PA; WP with WIP).
- Expense provision: approved, non-deferred, non-accrued expense requests without invoice; PG account.
- Overcommission: generated pendings with Provision/Bill month flags; PO and PD accounts.
- OT close: bridge balances 01/02/03 per OT, pending items, closing type, accounting month. IC: intercompany flags and IC accounts.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Confirm the gate: every job needs the relevant subledgers pre-closed and not closed (§4.2). If not, return `blocked` and route to agency-period-close. Expense provision may be simulated before pre-close (P10).
2. Ask operational teams to confirm pendings first: media and production validate pending items, never-progressed estimates are disapproved, insertion orders are closed before supplier invoicing (P08, P-OP-07). Record who confirmed.
3. FX revaluation (P07): prepare three runs, all mandatory, in any order: receivables (voucher type 95) at the buy rate, payables (96) at the sell rate, foreign-currency GL accounts (8), revaluing accounts with subaccounts subaccount by subaccount (BR-15, BR-17, BR-19). Run `fx_revaluation` per run; post date is the last day of the month.
4. FX reversal: each run auto-reverses on day 1 of next month, except in the last month of the fiscal year, where the next year starts from the first-day rate (BR-18). If a manual FX entry already exists, still run the automatic entry and propose a manual reversal of the user's entry (P07).
5. Gross Income provision (P08): one entry per month covering all clients, media and production, one line set per OT, dated the last day and reversed on day 1 (BR-29). Untick `Honorarios y Comisión siempre` unless policy says otherwise; keep `Sin ingreso pendiente` on (mandatory with WIP) (BR-30). Partial runs are simulation only.
6. WIP (P09): when WIP is on, list plans and estimates with supplier invoice recorded but client not invoiced; move that cost from P&L to WP on the last day, reversed day 1; media and production are processed together once per month (BR-31). Pair it with the GI provision for the revenue side.
7. Expense provision (P10): select approved, non-deferred, non-accrued requests without supplier invoice; one run per month, not split by expense type; optionally revalue foreign-currency requests at the current rate (BR-32). Exclude requests already accrued with `Devengar`.
8. Overcommission provision (P11): include all pending items with no line selection; PO for overcommission income, PD for client refunds; reversed day 1 (BR-33). Recompute or verify a pending with `tiered_commission` only from contract terms supplied by agency-rebates; Provision months accrue only and the last contract month must be Bill (BR-OC-07).
9. OT closing (P13), mandatory with bridge accounts: close only OTs billed in the month with a cost difference (BR-50 step 14). Difference = client side (01) − supplier side (02); move it from 03 to 05 if positive or 04 if negative, voucher type 6, one entry per OT (BR-37). Request definitive only when nothing is pending; otherwise it silently becomes provisional (§4.4). Do not mix close and reopen in one run.
10. Intercompany reclass (P26): reclassify balances with intercompany parties in 42/52, 93, 32, 50 and provisions PG/PC/PH/PI/WP to IC while the month is pre-closed and not closed (provision code labels differ between pages: confirm locally).
11. Validate every proposed entry with `journal_check` (balance per currency, dimensions, locked periods) and check per-division balance by slicing lines (BR-01). Use `allocate` when an amount must be split across OTs, divisions or cost centers.
12. Package each job as a separate proposal with its mirror reversal, the per-OT or per-document detail and the tool outputs. Annulment of a posted job removes both the entry and its reversal (BR-28); prefer correcting in the next month over re-running (§4.6).
13. Report the job checklist to agency-period-close: which jobs are mandatory (FX always when foreign balances exist; OT close with bridge accounts; WIP when bridge accounts are not used), which are optional, which are done with verified receipts.

## Rules and locks
- Every close job requires pre-close; none runs in an open or closed month (§4.2, §10.3).
- Every provision is a last-day snapshot with automatic day-1 reversal; annulling removes both (BR-28).
- Only one Gross Income provision entry per month (BR-29); expense provision is one run per month (BR-32).
- All three FX runs are mandatory every month when foreign-currency balances exist; without them AR/AP subledgers do not match the GL (BR-19).
- No FX reversal across the fiscal-year boundary (BR-18).
- After a provisional OT close, no further movements may be dated in that month; a definitive close blocks postings until reopened (P13). Late supplier invoices are dated after the close month.
- Bridge difference accounts 03/04/05 move only through OT closing; no manual entries (BR-36).
- Reopening a month from pre-close to open deletes automatic FX, provision and tax-position entries; whether WIP, expense, overcommission and OT closings are also deleted: confirm locally (BR-53, gap 7).
- Option flags and the GI start date are agency settings (configurable).
- WIP account WP vs obs 86 may be distinct accounts (confirm locally).

## Calculations
- `fx_revaluation`: per open document `doc_id`, `side` (asset for receivables and FX cash/bank, liability for payables), `open_minor` with its `exponent`, `book_rate_micro` (or the prior base rate after a reversal-free year start) and `closing_rates` in micro units. Use buy rates for the AR run and sell rates for the AP run as separate calls.
- `journal_check`: validate each job entry and its reversal before approval.
- `tiered_commission`: verify a monthly overcommission increment (`prior_adjusted_base_minor` for cumulative scales) and client share; terms come from the contract.
- `allocate`: split provisions or IC amounts across OTs, divisions or cost centers with exact conservation.

```bash
python3 scripts/agency_tools.py fx_revaluation < input.json
```
```json
{"local_currency": "MXN", "local_exponent": 2,
 "closing_rates": [{"currency": "USD", "rate_micro": 18250000}],
 "items": [
  {"doc_id": "AR-INV-4411", "side": "asset", "currency": "USD", "exponent": 2, "open_minor": 1000000, "book_rate_micro": 17900000},
  {"doc_id": "AR-INV-4420", "side": "asset", "currency": "USD", "exponent": 2, "open_minor": 250000, "book_rate_micro": 18400000}]}
```
This is the receivables run (voucher type 95) at the buy rate; repeat with the sell rate and `side: liability` items for payables (96).
- Not calculated by tools: exchange rates, the GI engine (pending billing × fee, commission, investment, additional cost per OT), WIP selection, IIBB and service-fee prerequisites, and recognition policy. Take pendings from the ERP report and rates from the authoritative table; unknowns stay blockers, never zero.

## Approvals and segregation of duties
- The Chief accountant (or delegate with the job permission; WIP needs access level 2 and visualization A) prepares; the Controller approves posting. The preparer cannot approve their own proposal; in a solo business the authenticated owner may approve under a documented owner approval policy.
- Hash each job proposal with `payload_digest` and require an authenticated human approval bound to the digest, period, revision and total. Annulment of a posted job requires a separate approval.
- No job has an in-system approval in the reference ERP (P08); the approval here is agency policy.

## Exceptions to escalate
- Month not pre-closed, or already closed → Controller via agency-period-close.
- Missing last-day buy or sell rate → Treasury loads the rate; FX stays blocked.
- Manual FX entry found → Chief accountant approves the automatic run plus manual reversal.
- Pending item stale or caused by VAT recovered on cost renditions → agency-production edits estimate cost or marks as invoiced (no GL entry).
- Definitive OT close requested with pendings → report downgrade to provisional; Account lead resolves pendings.
- Supplier invoice arrives for an OT closed provisionally in this month → date it in the next open month.
- Second GI provision requested for the same month → refuse; propose annul-and-redo with approval.
- Provision code mapping (PI/PE/PH/PC) inconsistent between pages → Chief accountant confirms before posting.
- Overcommission pending conflicts with contract cut-off flags → agency-rebates.

## Return and handoff
Return `fx_revaluation_proposal`, `gross_income_provision_proposal`, `wip_reclass_proposal`, `expense_provision_proposal`, `overcommission_provision_proposal`, `ot_close_proposal`, `ic_reclass_proposal`, `close_job_checklist`. Include tenant, client, JobNumber and OT per line, voucher type, posting and reversal dates, revision, status (`draft`/`blocked`/`pending_approval`, `completed` only with verified posting receipts), evidence references, blockers, approvals required and next stage.
**Owner:** Chief accountant. **Next:** agency-period-close.

## Connectors and files
- Provider ids: `banxico-sie` (reference FX series; the authoritative rate is the one loaded in the ledger), `xero`, `quickbooks` (open items and draft journals), `supermetrics` only as delivery evidence for pendings. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` or `--kind plan ...` for pending-billing evidence. Normalized files are unverified evidence.
