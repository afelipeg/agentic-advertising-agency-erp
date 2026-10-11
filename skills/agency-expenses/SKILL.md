---
name: agency-expenses
description: "Controls agency overhead: expense contracts and requests, employee expense sheets, cost sheets vs estimates, petty cash and expense budget. Use for non-media spend. No self-approval."
---

# Control Agency Expenses and Petty Cash

This stage covers spend that is neither media buying nor client production purchasing. Expense contracts (`Contratos de Gastos`) and requests (`Solicitudes de Gastos`), optionally formalised by expense purchase orders (`Órdenes de Compra de Gastos`), feed supplier invoices registered in agency-payables; expense, cost and petty cash sheets (`Planillas de Gastos / Costos / Fondo Fijo`) become settlements (`Rendiciones`) that book receipts and lead to reimbursement, refund or replenishment in treasury. It owns requests, sheets, settlement proposals, deferral schedules and the expense budget (`Presupuesto de Gastos`). It never approves on behalf of a claimant, never posts a settlement and never pays.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [expenses.md](references/erp/expenses.md) (P1 configuration, P3 to P19 contracts, requests, POs, accrual, sheets, settlements, petty cash, budget; lifecycles 4.1 to 4.6; rules 1 to 35; section 6 accounting; controls 10.3; gaps 5, 7, 8, 14, 16).

## Use when
- A recurring supplier agreement (rent, insurance, subscriptions) must become an expense contract with a monthly schedule.
- A one-off purchase needs an expense request, its approval route, or an expense PO ("solicitud de gastos", "orden de compra de gastos").
- An employee submits an expense sheet or travel expenses, or accounting must prepare the expense settlement ("rendición de gastos") with reimbursement or advance refund.
- Staff paid production costs that belong to a client-approved estimate item ("planilla de costos", "rendición de costos").
- A petty cash custodian needs a sheet, a settlement and replenishment ("reponer fondo fijo").
- A quarterly or annual bill must be deferred over several months ("devengar"), or the expense budget compared with actuals.

## Do not use when
- Registering the supplier invoice against an approved request: use agency-payables.
- Paying suppliers or releasing payment orders: use agency-payment-run.
- Production estimates, items and client approval: use agency-production-estimating.
- Hours, timesheets and labour cost: use agency-tasks-timesheets.
- Corporate card statements and bank movements: use agency-cash-settlement.
- Fixed asset depreciation after acquisition: use agency-fixed-assets.
- Month-end expense provisions: use agency-accruals-revaluation.

## Required inputs
- Blocking: tenant, requester or claimant pseudonym, concept (drives the GL account), net amount in minor units, currency and rate source, and allocation (cost centre, division, client or AGENCY, JobNumber/work order).
- Blocking: agency configuration flags — JobNumber control, self-approval policy, PO mandatory, PO approval, second approval by concept — and the approver matrix with amount limits.
- For contracts: supplier, validity, contract total, monthly amounts, invoice counts and accrual rows.
- For sheets: lines with date, concept, gross amount, receipt evidence (personal data redacted before model access), advance delivered and cash returned.
- For cost sheets: client-approved estimate, item assigned to the cost-rendering supplier, item currency and remaining amount.
- For petty cash: fund account, its GL balance and unposted sheets.
- For budget checks: authorized, spent, committed and reserved amounts per cost centre and account.
Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Validate eligibility: currency must be local or a controlled foreign currency (sheet lines may use an uncontrolled currency with a typed rate) (rule 1); the work order must be open or provisionally closed (rule 10); with JobNumber control off only generic work orders are allowed (rule 11); agency overhead goes to the AGENCY client (rule 12).
2. Check budget before approval with `budget_check` on the cost centre × account cell; requests still pending approval are ignored by the reference budget (rule 29), so add them explicitly as requested amounts.
3. Contracts: require a periodic concept; block approval if any month falls in a fiscal year not yet opened (rule 14, P4). On approval the reference creates one approved request per expected invoice per month (P4); use `installment_schedule` to propose monthly amounts that sum exactly to the contract total (equal split is an assumption, gap 7 — confirm locally).
4. Requests: amount is net of VAT; with item breakdown it is Σ quantity × unit price (rule 5); manual allocation lines must sum to the header (rule 6); use `allocate` for allocation codes, whose percentages must total 100% per level (rules 7, 8); subaccount breakdown cannot combine with allocation codes (rule 9). Detect variants: multi-invoice, credit, reimbursement (bridge account S1), fixed asset (account B1) (P5).
5. Route approval: supervisor or assigned approver within amount limit; creator ≠ approver unless self-approval is enabled and the user is an expense-approver user; flagged concepts need a second approval; rejection needs a reason (rule 13, P6). Escalation beyond a limit is unspecified (gap 5 — confirm locally).
6. PO gate: POs only on approved requests; when POs are mandatory the supplier invoice is blocked until the PO exists, and until it is approved when PO approval is on; a request with a PO cannot be edited, deleted, rejected or disapproved (rule 18, P9). Hand off approved requests or POs to agency-payables; the request becomes `Contabilizada` on invoice entry (P10).
7. Deferral: entries for months + 1 periods from the start date, equal installments assumed (rule 17, gap 8); use `installment_schedule` with `advance_bps: 0` and installments = months + 1. Accruals are not auto-reversed and the invoice later posts against the expenses-to-accrue account (P8).
8. Expense sheets: one line per taxed receipt in the agency's name, untaxed tickets may be grouped, multi-service receipts split pro rata by concept (rule 23); line total = amount × rate (rule 2). Run `invoice_check` on each taxed receipt (net, VAT rate, declared gross). Check duplicates by supplier tax ID + document number + amount across sheets (agency policy). Send locks the sheet (P11).
9. Sheet review: bounce to Pending with reasons, delete disallowed lines, or authorize; de-authorization is blocked once the settlement is posted (P12). A request to skip review because the claimant is an administrator stays pending.
10. Settlement proposal: VAT = reported gross − net entered, other taxes typed, `0000` if no VAT (rule 24); deductible flag on by default (rule 26); non-split receipts form one exempt VAT-book entry (rule 27); no posting into a closed fiscal year (rule 28). Provisional save posts nothing; final save posts and is immutable (P13, lifecycle 4.5).
11. Balance: owed to employee = total − advance; owed to agency = advance − total; returned cash brings the agency balance to zero (rule 32). Reimbursement and refund are separate treasury actions by users with payment or collection rights (P14, P15).
12. Cost sheets: currency must equal the estimate item currency and total ≤ item amount on a client-approved estimate (rules 3, 4); the account follows the item's service type and cannot be changed (rule 34); after a settlement splits out tax T, propose reducing the item's pending by T once the item shows as supplier-invoiced (rule 33, P17).
13. Petty cash: sheet currency = fund currency (rule 3); available = fund GL balance − Σ sent or authorized unposted sheets (rule 31); submit before depletion; replenishment returns the fund to its fixed amount (P18).
14. Compute `payload_digest` over each proposal and hand off with approvals pending.

## Rules and locks
- Creator ≠ approver unless self-approval is configured and the user is classed as expense approver (rule 13) (configurable). The claimant never approves their own reimbursement; the owner's personal reimbursement follows the configured independent-review policy.
- Amount limits per approver and second approval per concept (rule 13) (configurable).
- PO gate: request approved → PO (approved) → invoice (rule 18) (configurable).
- Sheets lock on Send; edits only through a bounce; no de-authorization after posting (P12).
- Cost sheets capped by the client-approved estimate item and in its currency (rules 3, 4).
- Settlements and budget entries are blocked in closed periods (rule 28).
- Contract approval blocked while any month lies in an unopened fiscal year (rule 14).
- Allocation codes total 100% at each level (rule 7).
- The reference hard-deletes contracts, requests, sheets and settlements; treat deletion as soft delete with an audit log (section 10.3, agency policy).
- Missing receipts, rates or approvals are gaps, not zero cost.

## Calculations
- `allocate`: split a request, contract month or settlement line across cost centres, divisions or JobNumbers by integer weights with exact conservation.
- `installment_schedule`: contract monthly amounts or deferral over months + 1 periods, summing exactly to the gross.
- `invoice_check`: recompute VAT and total for each taxed receipt against its declared gross with a rounding tolerance.
- `budget_check`: available = authorized − spent − open commitments − reservations; a request above availability needs the budget owner.

```bash
python3 scripts/agency_tools.py allocate < input.json
```
```json
{"currency": "COP", "amount_minor": 1850000000, "weights": [{"target_id": "CC-ADM", "weight": 5000}, {"target_id": "CC-CRE", "weight": 3000}, {"target_id": "CC-MED", "weight": 2000}]}
```

Not calculated by tools: VAT rates and receipt tax data (typed from receipts), per-diem or category caps, FX rates, approval routing and fiscal codes (CAI/CAE, CFDI). These come from the agency expense policy, the tax setup and authoritative rate sources.

## Approvals and segregation of duties
- Requesters and claimants prepare; assigned approvers or supervisors approve within limits; accounting prepares settlements; users with payment or collection permissions execute reimbursement, refund and replenishment in treasury.
- Contract approval, request approval, PO approval, sheet authorization, final settlement posting, deferral runs and voids, and estimate tax adjustments need an authenticated approval bound to the `payload_digest`. The AI cannot approve its own proposal.

## Exceptions to escalate
- Claimant asks to bypass review or approve their own sheet → remain `pending_approval`; independent approver.
- Request over the approver's limit → next approver per policy (confirm locally).
- Supplier invoice arrives without the mandatory PO → agency-payables holds; purchasing issues PO.
- Cost sheet above the estimate item or on an unapproved estimate → producer in agency-production-estimating.
- Contract months in an unopened fiscal year → controller in agency-period-close.
- Request with a PO needs changes → remove from PO first.
- Foreign currency missing from the controlled list → administration; sheet use only.
- Petty cash nearly exhausted → custodian submits early.
- Fixed-asset concept (B1) → agency-fixed-assets after invoice entry.
- Settlement posted into a closed period or expense on a closed work order → controller.

## Return and handoff
Return `expense_request_drafts`, `contract_schedule`, `sheet_review`, `settlement_proposal`, `deferral_schedule`, `budget_check_result`, `approval_requests`. Include tenant/client/job IDs, JobNumber and work order, cost centre and division, document ids (contract, request, PO, sheet, settlement) and revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Office manager and controller. **Next:** agency-payables, agency-payment-run, agency-cash-settlement, agency-profitability.

## Connectors and files
- Ledgers: `xero`, `quickbooks`; e-invoice validation of receipts: `mx-cfdi-pac`, `arca-afip`; receipt intake from host marketplace documents/email; `notion` for policy documents; aggregators `composio`, `zapier` only with inner-tool approval. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
