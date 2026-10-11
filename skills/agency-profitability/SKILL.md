---
name: agency-profitability
description: "Analyzes job, client and media profitability: gross income, valued hours, expenses, contribution and overhead allocation, with media spend kept apart. Use for margin reviews."
---

# Agency Profitability

This stage reads the circuit after billing, supplier invoicing, timesheets and month-end provisions, and feeds management reporting and period close. It owns the job P&L (posted plus pending), the client profitability statement and the media profitability view. It never posts journal entries, changes rates or hours, or reallocates costs in the ledger; it prepares analysis and corrective proposals.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (rules 74–80 profitability formulas, §6 job P&L and WIP, §9 ROT and client profitability reports, J16, gaps 6 and 11) and [accounting.md](references/erp/accounting.md) (BR-54 and BR-55 staff cost and overhead, P08–P09 provisions, BR-52 control 3, §3.2 dimensions, §9 work-order profitability).

## Use when
- "Is this job profitable?", "rentabilidad por cliente", "job P&L", "ROT" (`Inversión y Gross Income por Cliente`), media profitability (`Rentabilidad de Medios`).
- Valuing hours at internal cost and at client rate for a job, contract or client.
- Allocating structural overhead from the agency's non-chargeable JobNumber to clients.
- Building a planned-vs-actual margin bridge or explaining a negative contribution.
- Separating managed media spend and pass-through from agency revenue for a client review.

## Do not use when
- Building the monthly pack, parent-company mapping or KPI set → agency-management-reporting.
- Posting provisions, WIP or work-order closes → agency-accruals-revaluation; closing the month → agency-period-close.
- Approving or correcting timesheets → agency-tasks-timesheets; hourly-fee overage billing → agency-fee-contracts.
- Campaign performance, pacing or ROAS → agency-campaign-optimization.
- Cash timing of collections and payments → agency-cash-forecast.
- Rebate and overcommission calculations → agency-rebates.

## Required inputs
- **Blocking:** tenant, period, basis (posted only, or posted plus pending billing and pending supplier invoices), currency and exponent, scope (job, client, product, division, sub-company).
- **Blocking:** revenue and cost by JobNumber and work order (OT) from the ledger or billing/supplier subledgers, mapped to income types: sale/investment, agency service (obs 20), fees (obs 22), bonuses (obs 23), supplier commissions.
- **Blocking for client profitability:** approved hours by collaborator and job; internal hourly cost and client rate per collaborator and month; direct expenses by job; structural expenses booked to the agency generic job; collaborator-to-client allocation table if used.
- Managed media spend and pass-through amounts by client, with the configured principal/agent treatment.
- Pending items: approved-unbilled estimate and plan lines, uninvoiced supplier costs, WIP balance.
- Driver choice for overhead (contribution share by default; valued hours, hour count or 50/50 are reference options).
- Ask only for missing material inputs. Never ask for credentials in chat.

## Procedure
1. Fix scope: period, date criterion (work-order month, client-invoice date or accounting date), basis, currency, and whether pending and in-process items are included. Keep each currency separate unless an approved dated FX policy exists.
2. Pull posted results per JobNumber and OT. Every result line must carry JobNumber, OT and cost center (accounting BR-02); flag lines without dimensions as completeness gaps.
3. Compute gross income per job and client: revenue − direct costs + agency commission + fees (accounts-jobs rule 76). Exclude managed spend and pass-through that the agency does not recognize as revenue; carry it in a separate `managed_spend` line.
4. Add pending lines for the projected job result: pending billing and pending supplier invoices, as in the work-order profitability report. Label them projected, never posted.
5. Value hours: internal cost = approved hours × internal hourly cost; client value = hours × client rate (rule 80). Use only approved hours when approval is on. Internal rate = annual cost ÷ annual working hours adjusted for vacation (BR-54); take it from the host, do not derive it from payroll in chat.
6. Compute contribution margin per client: income (billing − supplier costs) − direct costs (valued hours + unplanned direct expenses) (rule 78). Run `margin` per client with agency revenue = income, agency cost = direct costs, managed spend separate.
7. Collect structural expenses booked to the agency generic job in expense accounts. Allocate them with `allocate` using each client's contribution margin as weight (rule 78), so the allocated total equals the pool exactly.
8. If any client has zero or negative contribution, do not feed negative weights (the tool rejects them and the reference leaves this undefined, gap 11). Allocate over positive contributors only and disclose it, or use the agency's documented alternative driver (valued hours is the reference recommendation, rule 79; the accounting module distributes by hours, BR-55) (confirm locally).
9. Net result per client = contribution margin − allocated structural expenses. Client result (ROT view) = gross income − other expenses (non-billable, new business, own advertising) + miscellaneous income − miscellaneous expenses (rule 77).
10. Media profitability, if requested: report both formulas, (sale + commission − cost) / sale and (sale + commission − cost) / (sale + commission); the reference labels appear swapped (rule 75, gap 6), so name each by its formula.
11. Reconcile: total posted gross income must equal the P&L Gross Income heading (accounting BR-52 item 3). Any difference is a blocker for a `completed` status.
12. Build the margin bridge (planned estimate/plan margin → actual) and list corrective proposals (rate changes, scope revisions, write-offs) as drafts for their own workflows.

## Rules and locks
- Managed media spend, pass-through and direct-billed media are never agency revenue by default; principal/agent treatment is agency policy (configurable).
- Typologies N, S and W and billing code `0` jobs carry no sale value; their costs reduce the client result as other expenses (accounts-jobs rules 15, 18).
- Only approved hours count when timesheet approval is on; hours on now-inactive clients can be hidden by filters, so check for them.
- Provisions (GI, WIP) are last-day snapshots reversed on day 1 (accounting BR-28); never count a provision and the later actual twice in one view.
- Overhead allocation must conserve the pool exactly; show the driver and weights.
- Negative-contribution allocation behaviour is undefined in the reference (confirm locally).
- Collaborator-to-client allocation tables redirect agency hours to specific clients and must total 100% per period (accounting §3.4).
- A profitability figure is analysis, not a posting; corrections go through reversals in an open period by the accounting owner.

## Calculations
- `margin`: per job or client, `agency_revenue_minor` = income or gross income, `agency_cost_minor` = direct costs (valued hours + direct expenses, plus allocated overhead for net result), `managed_spend_minor` reported separately; `margin_bps` is null when revenue is zero.
- `allocate`: structural overhead pool across clients with integer weights (contribution margin in minor units, or hours in hundredths) and exact largest-remainder conservation.

```sh
python3 scripts/agency_tools.py allocate < input.json
```
```json
{"currency": "MXN", "amount_minor": 4000000, "weights": [
 {"target_id": "CLI-A", "weight": 6000000}, {"target_id": "CLI-B", "weight": 3000000}, {"target_id": "CLI-C", "weight": 1000000}]}
```
- Not calculated by tools: internal hourly cost (host collaborator master), client rates, FX conversion, principal/agent classification, tax, rebate recognition.

## Approvals and segregation of duties
- The finance controller prepares and signs off the analysis; account directors review their clients. Analysis needs no approval to draft.
- Anything that changes money or records (price changes, write-offs of media differences, reallocation entries, scope revisions) needs its owning workflow and an authenticated human approval bound to the payload digest; the preparer does not approve.
- Cost and margin fields are visible only to roles with cost/profitability visibility (levels A/B); strip them for others before model access.

## Exceptions to escalate
- Negative contribution margin for a client or job → account director and controller.
- Jobs with costs but no revenue, or sale value on N/S/W jobs → agency-job-lifecycle.
- Posted gross income not tying to the P&L Gross Income heading → agency-general-ledger.
- Result lines missing JobNumber, OT or cost center → agency-general-ledger.
- Unapproved or missing hours for the period → agency-tasks-timesheets.
- Supplier invoices booked but client not billed (WIP) ageing → agency-accruals-revaluation and agency-client-billing.
- Managed spend classification disputed → controller and tax adviser.
- Missing internal rate or client rate for a collaborator category → controller.

## Return and handoff
Return `job_pnl`, `client_profitability`, `overhead_allocation`, `margin_bridge`, `managed_spend`, `completeness_gaps`. Include tenant, client and job IDs, JobNumbers and OTs, period, basis, currency, driver, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Finance controller. **Next:** agency-management-reporting, agency-period-close.

## Connectors and files
- Ledger and P&L by tracking category: `xero`, `quickbooks`. Media spend evidence: `google-ads`, `meta-ads`, `amazon-ads`, `supermetrics` (use read tools only). Host marketplace warehouse for timesheet and ledger extracts. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating. Ledger, hours and rate extracts arrive as values-only CSV and stay unverified evidence.
