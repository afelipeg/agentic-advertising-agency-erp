---
name: agency-fixed-assets
description: "Prepares the fixed-asset register, monthly depreciation, disposals and annex from capital expense requests. Use when capitalising, depreciating or retiring assets."
---

# Agency Fixed Assets

Fixed assets (`bienes de uso`) enter from the expense circuit: an expense request whose concept maps to an obs B1 account creates the asset when the supplier invoice is registered. This skill keeps the register, prepares the monthly or annual depreciation run, disposals by disuse or sale, and the annex roll-forward that ties to the balance sheet, then hands the run to the close. It prepares and validates; it never posts entries, never edits an asset after its first depreciation and never computes inflation adjustments.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounting.md](references/erp/accounting.md) (P27, P28, §3.4 fixed-asset concept and depreciation criterion, §4.7, BR-20 to BR-25, E41–E44, Anexo Bienes de Uso in §9, §11 gap 10) · [expenses.md](references/erp/expenses.md) (P5 fixed-asset request variant, rule 20 asset trigger, §6 B1 posting, §7 handoff to fixed assets).

Agency policy: apply `currencies`, `approvals`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- Registering an asset from an expense request or invoice (`alta de bien de uso`, `solicitud de gastos` with B1 concept), or reviewing an import of legacy assets with prior accumulated depreciation.
- Preparing a depreciation run (`amortizaciones`, voucher type 94) with cost-center mode and division.
- Disposing of an asset by disuse, full depreciation (`baja`) or sale (`facturación de bienes de uso`).
- Producing the fixed-asset annex (`Anexo Bienes de Uso`) and tying it to B1/B2 balances.
- Explaining first-month criteria S/N/P/M or the complete-year-of-acquisition setting.

## Do not use when
- Creating or approving the expense request or PO: use agency-expenses; registering the supplier invoice: use agency-payables.
- Issuing the sales invoice for an asset sale to the buyer: use agency-client-billing (this skill prepares the NBV and gain/loss).
- Manual GL entries or account setup for B1–B8: use agency-general-ledger.
- Month pre-close or close: use agency-period-close; other month-end provisions: use agency-accruals-revaluation.
- Statutory tax depreciation filings: use agency-tax-compliance.

## Required inputs
- Blocking: tenant, asset concept with B1/B2/B4 accounts (B3, B5–B7 under inflation adjustment) and default useful life, purchase date and value in minor units with currency, depreciation start date, cost center, division or division split.
- Blocking for runs: method (monthly or annual), complete-year-of-acquisition flag, criterion per concept or run (S/N/P/M), period state (month, or last month of the year for the annual method, pre-closed), locked periods, cost-center mode.
- Source evidence: expense request number, supplier invoice, inventory code; for legacy assets, prior accumulated depreciation and elapsed months.
- Disposal: year, month, reason, sale price (for sale), whether that month's depreciation was already posted.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Prefer the expense route: confirm the request's concept maps to an obs B1 account, useful life was captured and the supplier invoice is registered; the asset record is then created automatically (P27, expenses rule 20). Flag manually created assets: their GL value must be posted separately and is not controlled.
2. Validate the record: unique description, purchase date and value, supplier and invoice, cost center, division or percentage split totalling 100%, asset concept, useful life in months, depreciation start date, first-period amount, opening accumulated depreciation for pre-system history.
3. Legacy assets: compute opening accumulated depreciation as value ÷ life × elapsed months and enter it before the first run (BR-23 worked example); keep the external evidence.
4. Lock check: an asset is editable only while it has not been depreciated and its month is open (P27). Changes after that become a disposal plus re-registration or a documented adjustment.
5. Choose the first-month rule from the criterion: S full first period, N none, P proportional by months and days, M 50% in the first year and 50% in the last (BR-21). Map to the tool: N → `following_month`; a whole first month → `acquisition_month`. P and M, and the complete-year coefficient (BR-20), are not computed by the tool: calculate them separately and label them (how the criterion interacts with the complete-year flag: confirm locally).
6. Run `depreciation_schedule` per asset for straight-line monthly charges (base = current value ÷ useful life, BR-22) with exact totals; sum the period charges by B1 concept and division.
7. Choose the cost-center mode (P28): (a) each asset's own cost center, (b) a forced single cost center, or (c) a general allocation key; use `allocate` for mode (c) so the split conserves the total exactly.
8. Build the run entry: voucher type 94, entry type Otros, debit B4 depreciation expense (B8 on revaluation) and credit B2 accumulated (B5), by division and cost center (BR-24). Exclude inactive, disposed and fully depreciated assets.
9. Validate the entry with `journal_check` (locked periods, dimensions: B-accounts on result lines carry Job/OT/CC per BR-02) and confirm the control: total period depreciation = entry total (P28). Summary mode cannot be posted; use it only to tie to B1/B2.
10. Disposal by disuse or full depreciation: the month must not be pre-closed or closed; if that month's depreciation is posted, plan its annulment first, then the disposal, then the re-run. Entry: debit B2 (and B4 for residual on disuse), credit B1 (E43, inferred pattern).
11. Disposal by sale: prepare NBV = cost − accumulated depreciation and gain/loss = sale price − NBV, booked to obs BR (BR-25); hand the sales invoice to agency-client-billing.
12. Inflation adjustment (BR-23, P17): only in jurisdictions with `Corrección Monetaria` on. Note the coefficient formula and B3/B5–B7 accounts, but do not compute it with `depreciation_schedule`; request the controller's coefficient table and an adviser-reviewed calculation.
13. Produce the annex roll-forward: opening value, revaluation, additions, disposals, closing; accumulated depreciation opening, revaluation, disposals, charge, closing; NBV, by concept. Tie closing totals to B1 and B2 balances and list differences.

## Rules and locks
- Assets are created from expense requests with B1 concepts; manual creation is discouraged and uncontrolled (P27).
- An asset is editable only before its first depreciation and while the month is open (P27, §4.7).
- The depreciation run requires the month (annual method: the last month of the year) to be pre-closed (P28).
- Disposal requires the month not pre-closed or closed; posted depreciation for that month is annulled first (P27, §10.4).
- Deletion only by a supervisor and only with no invoice and no movements; otherwise deactivate (P27, BR-09).
- Annulling a run allows adding or disposing of assets, followed by a re-post (P28).
- Method, complete-year flag and criteria are agency settings (configurable).
- Asset sale and disuse entry patterns are partly inferred (E43, E44): confirm locally.

## Calculations
- `depreciation_schedule`: `cost_minor`, `residual_minor`, `life_months`, `acquisition_date`, `first_month_rule` (`acquisition_month` or `following_month`); returns monthly charge, accumulated and NBV with the remainder in the last month.
- `journal_check`: validate the run, disposal and sale entries before approval.

```bash
python3 scripts/agency_tools.py depreciation_schedule < input.json
```
```json
{"currency": "MXN", "cost_minor": 3600000, "residual_minor": 0, "life_months": 36,
 "acquisition_date": "2026-10-14", "first_month_rule": "following_month"}
```
- Not calculated by tools: P and M first-period criteria, complete-year coefficients, inflation coefficients (FACPCE or local index), tax depreciation rates, VAT on asset sales. These come from the controller, the tax adviser and authoritative tables.

## Approvals and segregation of duties
- The Chief accountant prepares the register changes and runs; the Controller approves posting of runs and disposals. The person who requested the asset in agency-expenses does not approve its disposal. In a solo business the authenticated owner may approve under a documented owner approval policy.
- Hash each run, disposal and sale proposal with `payload_digest`; require an authenticated human approval bound to the digest, period, revision and total. Asset deletion needs supervisor rights.

## Exceptions to escalate
- Asset created manually without GL posting → Chief accountant reconciles to B1.
- Request to edit an asset already depreciated → refuse; propose disposal or adjustment entry.
- Disposal in a month whose depreciation is posted → annul run first, Controller approves.
- Disposal in a pre-closed or closed month → Controller via agency-period-close.
- Run total ≠ entry total, or annex ≠ B1/B2 balances → hold posting; Chief accountant investigates.
- Missing useful life or concept on a B1 expense request → agency-expenses.
- Inflation adjustment required → tax adviser and Controller provide coefficients.
- Division split not totalling 100% → return to preparer.

## Return and handoff
Return `asset_register_changes`, `depreciation_run_proposal`, `disposal_proposal`, `fixed_asset_annex`. Include tenant, asset codes, expense request and invoice references, concept, cost center, division, voucher type 94, period, revision, status (`draft`/`blocked`/`pending_approval`, `completed` only with verified posting receipts), evidence references, blockers, approvals required and next stage.
**Owner:** Chief accountant. **Next:** agency-period-close.

## Connectors and files
- Provider ids: `xero`, `quickbooks` (asset registers and draft journals where enabled), `mx-cfdi-pac` or `arca-afip` for invoice evidence of purchases and sales. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` for purchase or sale invoices. Asset register spreadsheets are unverified evidence.
