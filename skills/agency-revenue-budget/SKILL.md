---
name: agency-revenue-budget
description: "Build and version the yearly agency revenue budget by client, product and month: investment, commission %, cost-difference %, fees and rebates, with copy-with-actuals, supervisor lock and projection. Use when planning or comparing agency income against actuals. Do not edit a locked version or treat managed media spend as agency revenue."
---

# Revenue Budget

The revenue budget (`Presupuesto de Ingresos`) is the planning layer over the account circuit: client and product masters → **versioned yearly budget by client × product (× division) × media/supplier or production type × month** → plan-vs-actual and projected views → management reporting and cash forecast. This stage owns budget versions, their lines and computed income, the copy-with-actuals operation and the open/closed state of each version. It never posts entries, never changes actuals and never edits a version that a supervisor closed.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-25 revenue budget, entity `RevenueBudgetVersion` in 3.11, lifecycle 4.6, rules 69–73 and 76–77, report rows "Revenue budget queries", job J17, gap 10) and [management-security.md](references/erp/management-security.md) (P-RP-03 forecast stub and gap 1, R-SEC 41 supervisor visibility level A, R-AP and section 10.3 configuration-change control).

## Use when
- "Presupuesto de ingresos", "budget anual de ingresos", "forecast de gross income", "nueva versión del presupuesto" for one or more clients.
- Entering investment by month for media (by media and supplier) and production (by production type), with commission % and cost-difference %.
- Adding projected fees, rebates and rebate refunds per client and product.
- Copying a version to a new one including closed months with actuals (`incluir meses cerrados`).
- Comparing plan vs actual, version vs version, or producing the projected view (actual closed months + plan open months).
- Locking or reopening a version (`Cerrado a modificaciones`).

## Do not use when
- Actual job or client profitability and overhead allocation → `agency-profitability`.
- Monthly management packs and KPIs from booked figures → `agency-management-reporting`.
- Dated cash inflows and outflows → `agency-cash-forecast`.
- Fee contract instalments that will become actual fee income → `agency-fee-contracts`.
- Supplier rebate contracts and their calculation → `agency-rebates`.

## Required inputs
- Blocking: `tenant_id`, budget year, version name, loading method (recommended "detailed by media and production type"), currency.
- Blocking per line: titular client, product, division (when divisions are used), the opening (`Apertura`) rows (media + supplier, or production type), monthly investment in minor units, commission % and cost-difference % in basis points.
- Optional per client/product: projected fees, rebates and rebate refunds by month.
- For copies and projections: source version id, last closed month, actuals per line (booked or ordered, per the chosen scope "media billing" or "complete").
- The acting user's supervisor status from the host identity store for lock and reopen.

## Procedure
1. Confirm the target version is `Abierto`; a closed version cannot be modified (lifecycle 4.6). Modifications require a specific client, product and division, never "all" (rule 73).
2. Create or select the version (optionally restricted to active clients) and save it before adding lines (P-25).
3. Open the rows first: choose media + supplier rows; production rows list all production types. Enter percentages only after opening, because percentages entered before the opening are wiped (rule 71).
4. Enter monthly investment per row and the commission % and cost-difference % (rule 69: lines per product, and per division when used).
5. Compute per line and month: commission income = investment × commission %; cost-difference income = investment × cost-difference % (rule 70). Use integer minor units with half-up rounding (agency policy) and keep the formula with each figure.
6. Add projected fees, rebates and rebate refunds per client and product. Total income = commission + cost difference + fees + rebates − rebate refunds; the refund sign is (confirm locally) (rule 70, gap 10).
7. When an annual figure must be phased over months, use `allocate` with seasonality weights so the months sum exactly to the annual amount.
8. Keep managed media investment separate from agency income at every level; run `margin` with agency income as revenue, planned direct agency cost if known, and investment as managed spend, so margin percentage is never computed on gross media.
9. Copy to a new version: when "include closed months" is chosen, past months carry actual values instead of the old plan (rule 72). Record source version, last closed month and actuals scope.
10. Projection: actual for closed months plus plan for open months; actual means booked or ordered per the chosen scope (P-25 queries).
11. Plan vs actual and version vs version: compare per year by media or by client; flag lines with actuals but no plan and plan lines on inactive clients.
12. Prepare a lock or reopen proposal for a supervisor with its `payload_digest`; the agent never closes or reopens a version itself (rule 73).
13. Return the version pack with lines, computed income, comparisons and blockers.

## Rules and locks
- A version is either open or closed to modifications; only supervisors close or reopen it (rule 73).
- Open the media/supplier rows before entering percentages (rule 71).
- Copy with closed months substitutes actuals for past months; it never alters the actuals themselves (rule 72).
- Budget lines are per product and per division when divisions are used (rule 69).
- Gross income definition follows the reference ROT formula (revenue − direct costs + commission + fees); budget income is plan, not booked revenue (rule 76).
- Managed media investment is never agency revenue in margin or growth figures.
- The loading method (granularity of entry) is (configurable).
- The management-module forecast is a stub in the reference ERP; any forecast beyond this budget is agency policy (management-security gap 1).
- Changing a locked baseline after approval requires a new version, not an edit (agency policy).

## Calculations
- `allocate`: phase an annual investment, fee or rebate across months, or a client total across products, by integer weights with exact conservation.
- `margin`: agency margin from planned agency revenue and agency cost, reported apart from `managed_spend_minor`.

```bash
python3 scripts/agency_tools.py margin < input.json
```
```json
{"currency": "MXN", "agency_revenue_minor": 4150000, "agency_cost_minor": 2900000, "managed_spend_minor": 25000000}
```
Expected: `margin_minor` 1250000, `margin_bps` 3012, managed spend reported separately at 25000000.

- Not calculated by tools: commission and cost-difference income (compute explicitly as investment × bps ÷ 10000 in minor units and show the formula), actuals (from booked or ordered documents), FX for multi-currency clients and the rebate-refund sign.

## Approvals and segregation of duties
- The finance planning lead or account director prepares lines; a supervisor (visibility level A) locks or reopens versions.
- The baseline version used for targets is approved by a human bound to the `payload_digest` of the version content and revision.
- Users without cost visibility should receive budgets without cost-difference or margin fields (R-SEC 42, section 10.3 item 3).

## Exceptions to escalate
- Edit requested on a closed version → supervisor: reopen or create a new version.
- Percentages entered before the opening → re-enter after opening.
- Mixed currencies for one client → finance for budget FX rate.
- Actual scope unclear (booked vs ordered, media billing vs complete) → finance planning lead.
- Rebate refunds sign or rebate ownership unclear → controller and `agency-rebates`.
- Lines on inactive clients or products → `agency-master-data`.
- Large unexplained version-vs-version variance → account director.

## Return and handoff
Return `budget_version`, `budget_lines`, `income_projection`, `plan_vs_actual`, `version_lock_proposal`, `budget_exceptions`. Include tenant, year, version id and revision, client and product ids, division, currency, last closed month, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Finance planning lead. **Next:** `agency-management-reporting`, `agency-cash-forecast`, `agency-profitability`.

## Connectors and files
- Provider ids: `xero` or `quickbooks` for booked actuals, `supermetrics` or `google-analytics` for media investment evidence, `meridian` for planning scenarios, `notion` for version notes. Host marketplace warehouse or spreadsheets may hold actuals. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating when actuals arrive as plan or invoice exports.
