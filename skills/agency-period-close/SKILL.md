---
name: agency-period-close
description: "Sequences the monthly and year-end close: subledger pre-close, ordered close jobs, mandatory gates, reconciliations and reopen rules. Use to close or reopen a period."
---

# Agency Period Close

The close is what makes Accounting the single source of truth: operational modules stop posting into a pre-closed month, the close jobs derive the accrual view, and the definitive close freezes it for reporting, consolidation and tax filing. Upstream are agency-general-ledger, agency-accruals-revaluation, agency-fixed-assets, agency-payables, agency-collections and agency-tax-compliance; downstream are agency-management-reporting and agency-profitability. This skill owns the close checklist, the gate evidence, the lock proposal and the reopen/adjustment plan; it never posts, never locks or reopens a period itself and never overwrites posted history.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounting.md](references/erp/accounting.md) (P19, P21, P23–P25, §4.2 period states, §4.3 fiscal year, BR-13, BR-50 to BR-53, §10.3 controls, §10.4 exceptions, §11 gaps 6, 7) · [payables-treasury.md](references/erp/payables-treasury.md) (rule 21 release period, rule 24 bank reconciliation proof, rule 29 aging, rule 30 cut-off reports, §10.3 period guard).

## Use when
- Running the monthly close (`cierre mensual`): pre-close (`pre-cierre`) of Clients, Suppliers, Treasury and Accounting subledgers, ordered close jobs and definitive close (`cierre definitivo`).
- Checking whether a month can close: mandatory gates, missing jobs, open exceptions.
- Post-close reconciliations: integration differences, unpaid invoices vs control accounts, Gross Income tie-out, bridge control, checks in portfolio, deferred checks.
- Reopening a month (`abrir mes`) and assessing the cascade and deleted automatic entries.
- Fiscal-year close (`cierre de ejercicio`, `cierre de cuentas`), generating the new year, or an audit re-close.

## Do not use when
- Preparing provisions, WIP, FX, OT closing or IC reclass entries: use agency-accruals-revaluation.
- Drafting a manual or adjustment entry: use agency-general-ledger; depreciation: use agency-fixed-assets.
- VAT or IIBB positions and statutory files: use agency-tax-compliance.
- Payment releases or bank files: use agency-payment-run; supplier invoice posting: use agency-payables; receipts: use agency-collections.
- Management P&L, client profitability or KPI packs after close: use agency-management-reporting or agency-profitability.

## Required inputs
- Blocking: tenant, fiscal year, month, period × subledger state grid, enabled features (bridge accounts, WIP, divisions, inflation adjustment, group service fee), last-day exchange rate loaded.
- Blocking: status and receipts of each close job (FX AR/AP/accounts, OT close, provisions, depreciation, positions), open exception list with owner and materiality.
- Post-close evidence: trial balance with integrator breakdown, unpaid client and supplier invoices at cut-off, Inversión y Gross Income por Cliente (posted only), bridge control report, third-party checks and deferred checks listings, bank reconciliations.
- For reopen or year close: reason, requester, authorized controller, affected later months, auditor adjustments.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Pre-close readiness (BR-50 steps 1–5, optional): finished tasks costed, client-unapproved estimate and plan items rejected (not deleted), finished JobNumbers closed (Cuentas provisionally, Finanzas definitively), pending adjustments and 8A entries posted. Record anything left open with owner.
2. Subledger pre-close (P23, step 6, mandatory): require the last-day rate; a user with the special pre-close permission pre-closes Clients, Suppliers, Treasury and Accounting. Pre-close blocks new documents but allows close jobs and voucher types flagged for pre-closed months (§4.2). A subledger with no registrations cannot be closed.
3. Sequence the close jobs in the vendor order (BR-50 steps 7–16): VAT position (agency-tax-compliance), depreciation (agency-fixed-assets), expense provision, Gross Income provision, overcommission provision, WIP (mandatory when bridge accounts are not used), FX differences on payables, receivables and FX accounts (mandatory), OT closing (mandatory with bridge accounts), IIBB position, regional service fee (after FX, GI, IIBB and OT/WIP close, BR-34). Request each job from its skill and record its verified status.
4. Check the payment and cash cut-off: releases are booked by release date, not payment-order date, and release deletion is forbidden in a pre-closed month (annul with an open-period date instead) (payables rule 21). Run `aging` on unpaid client and supplier invoices at the cut-off for the close pack.
5. Post-pre-close adjustments (step 17): only voucher types allowed in pre-closed months; validate each with `journal_check`, passing closed months as locked periods.
6. Evaluate the gates for definitive close (BR-51): all subledgers pre-closed; FX posted when foreign balances exist; OT results posted with bridge accounts; income provision and IIBB recommended. Whether the ERP blocks a close with missing items is unknown (confirm locally), so treat the mandatory items as hard gates in this skill (agency policy).
7. Post-close reconciliations (BR-52, P25): (1) trial balance shows no integration differences on 48, 30, 82–85; (2) unpaid invoices listings at cut-off equal GL control accounts and subledger trial balances; (3) posted Gross Income by client equals the P&L Gross Income rubro; (4) bridge control equals the bridge rubro; (5) third-party checks in portfolio equal values to deposit; (6) post-dated deferred checks equal deferred checks; plus depreciation run total = entry total, VAT position = ledger = sub-journals, and month-end routine findings. Bank reconciliations count only when the balance proof equals the statement (payables rule 24).
8. Record unresolved balances with owner, amount, currency and materiality under approved policy; unknowns are blockers, never zero.
9. Prepare the lock proposal for definitive close (step 18) with the gate evidence, tool outputs and reconciliation results; hash it with `payload_digest` and route for controller approval. Report `completed` only with a verified period-state receipt.
10. Reopen assessment: closed → pre-closed is allowed but discouraged because it can change reported income and settled taxes; pre-closed → open deletes automatic FX, provision and tax-position entries (other jobs: confirm locally); reopening an earlier month cascades open to all later months (§4.2, BR-53). List every month and every automatic entry affected, and the re-run sequence.
11. Late errors in a closed period: preserve original entries; propose a reversal or adjustment dated in an open period via agency-general-ledger. Reopen only with explicit controller authorization and an audit trail.
12. New fiscal year (P21): generate before the last month ends (vendor advice: last working day after hours, with a backup); needs the year-end rate; seeds holidays, monthly staff-cost rows and relocates deferred checks. Reversible only while it has no movements.
13. Fiscal-year close (P19, BR-13): all months closed, next year generated, its first month open; inflation adjustment in the last month while pre-closed and REI reverse on day 1 of the new year where applicable. The close produces a result close into obs 90, a patrimonial close and the next-year opening entry.
14. Audit re-close (P19): delete the closing entry (opening entry kept) → reopen the needed months → post adjustments → re-close the months → re-run the year close, which updates the opening entry. Each pass needs its own approval and audit record.

## Rules and locks
- Period states are Open → Pre-closed → Closed per month × subledger; exchange rates are editable only in open months (§4.2).
- Every automatic close job requires pre-close; no posting into closed or pre-closed periods unless the voucher type allows it (§10.3).
- Definitive close requires pre-close plus the mandatory jobs (FX when foreign balances exist; OT close with bridge accounts) (BR-50, BR-51).
- Pre-closed → open deletes automatic FX, provision and tax-position entries; earlier-month reopen cascades to all later months (BR-53, §4.2).
- Posted history is never overwritten; corrections are reversals or adjustments in an open period (control contract).
- Year close needs all months closed, next year generated and its first month open; re-close updates the opening entry, with no limit on passes (BR-13).
- Release deletion is forbidden in a pre-closed month; annul with an open-period date (payables rule 21).
- Pre-close permission is a distinct, logged permission (§8) (configurable).
- Optional steps and their order beyond the mandatory gates follow agency policy (configurable).

## Calculations
- `journal_check`: validate post-pre-close adjustments and any proposed reversal against locked periods, balance and dimensions.
- `fx_revaluation`: re-verify the FX job totals when the receipt and the supporting open items disagree; it does not replace the job in agency-accruals-revaluation.
- `aging`: bucket unpaid client and supplier invoices at the cut-off per currency for the close pack and the BR-52 item 2 tie-out (ascending `bucket_limits_days`).

```bash
python3 scripts/agency_tools.py aging < input.json
```
```json
{"as_of": "2026-10-31", "bucket_limits_days": [30, 60, 90],
 "items": [
  {"doc_id": "SINV-881", "currency": "MXN", "due_date": "2026-10-15", "open_minor": 2500000},
  {"doc_id": "SINV-902", "currency": "MXN", "due_date": "2026-11-20", "open_minor": 1800000},
  {"doc_id": "SINV-760", "currency": "USD", "due_date": "2026-08-20", "open_minor": 420000}]}
```
- Not calculated by tools: exchange rates, tax positions, materiality thresholds, Gross Income engine and recognition policy. These come from the ledger, the tax adviser and the controller.

## Approvals and segregation of duties
- The Chief accountant prepares the checklist and evidence; the Controller approves the definitive close, any reopen and each year-close pass. The preparer of close jobs does not approve the lock. In a solo business the authenticated owner may approve under a documented owner approval policy, with an external accountant where that policy requires independent review.
- Hash the lock proposal, reopen plan and adjustment plan with `payload_digest`; require an authenticated human approval bound to digest, period, revision and policy version. A user-supplied "approved" flag is not approval.

## Exceptions to escalate
- Last-day rate missing → Treasury loads it; pre-close blocked.
- Mandatory job missing (FX, OT close) → agency-accruals-revaluation; definitive close blocked.
- Integration differences on 48/30/82–85 → owning subledger lead; close blocked.
- Gross Income by client ≠ P&L rubro, or bridge control ≠ bridge rubro → Chief accountant investigates.
- Bank reconciliation proof ≠ statement → Treasury; unresolved items listed.
- Request to reopen a month with settled taxes or reported income → Controller and tax adviser decide.
- Reopen would cascade to later closed months → Controller confirms the full cascade plan.
- Auditor adjustment after year close → audit re-close sequence with Controller approval.
- Fiscal year generated too early with transactions defaulting to it → Controller; reverse only if empty.

## Return and handoff
Return `close_checklist`, `close_job_status`, `post_close_reconciliations`, `unresolved_balances`, `lock_proposal`, `reopen_plan`, `adjustment_plan`. Include tenant, fiscal year, month, subledger states, job receipts, revision, status (`draft`/`blocked`/`pending_approval`, `completed` only with a verified period-state receipt), evidence references, blockers, approvals required and next stage.
**Owner:** Controller. **Next:** agency-management-reporting, agency-profitability, agency-general-ledger (authorized adjustments).

## Connectors and files
- Provider ids: `xero`, `quickbooks` (trial balance, period lock dates, open items), `banxico-sie` (reference rates), `mx-cfdi-pac` or `arca-afip` for tax-document evidence. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` for open-item evidence. Exported reports are unverified evidence until tied to the ledger.
