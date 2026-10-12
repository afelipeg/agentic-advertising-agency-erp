---
name: agency-payment-run
description: "Proposes supplier payment lists, payment orders, withholdings and release instruments for two-person approval. Use for a payment run or bank file. Never approves or releases payments."
---

# Prepare the Supplier Payment Run

This stage sits after supplier invoice registration (agency-payables) and before bank and cash settlement (agency-cash-settlement). It owns the payment list (`Lista de Pagos`), the payment orders (`Órdenes de Pago`, OP) of each type, the withholding computation and the release proposal (`Libranza`) that assigns funding instruments. Lists and orders create no journal entry; only the release does. The skill drafts and verifies; it never approves a list, releases an OP, writes a bank file or confirms bank results on its own.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [payables-treasury.md](references/erp/payables-treasury.md) (P9 to P19 payment list, OP types, release, undo flows, availability, bank export/import; rules 5 to 11, 13 to 17, 21 to 23, 28, 31, 35, 39; PaymentList and PaymentOrder lifecycles; accounting impacts in section 6; controls 10.3; gaps 2, 3, 13, 15).

Agency policy: apply `currencies`, `approvals`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- Preparing the recurring payment list ("lista de pagos provisoria") from open supplier invoices due in a window.
- Reviewing which payables are covered by fully collected client invoices (pay-when-paid evidence) before payment.
- Drafting payment orders: automatic by list, manual supplier payment, supplier advance (`anticipo`), pending notes, client refund (`devolución a clientes`), miscellaneous payment (`pagos varios`) or cost advance (`anticipo de costos`).
- Computing withholdings (`retenciones`) at list calculation or at release, and proposing release instruments: transfer, cheque, cash, third-party cheques, notes or expenses to render.
- Preparing a bank payment export file or reconciling a bank import of executed payments.
- Undoing a release, deleting an unpaid OP or annulling a paid OP.

## Do not use when
- Logging, deduplicating or registering supplier invoices: use agency-payables.
- Matching invoices to orders or deliveries: use agency-delivery-reconciliation.
- Bank deposits, bank charges, reconciliation, cheque printing, rejection or corporate card statements: use agency-cash-settlement.
- Employee reimbursements and petty cash replenishment from settlements: use agency-expenses.
- Withholding regimes, certificates and statutory returns: use agency-tax-compliance.
- Cash projection beyond this run: use agency-cash-forecast.

## Required inputs
- Blocking: intended payment date, due-date window, currency, payment method segment (cheque or transfer) and bank account for the list.
- Blocking: open items with supplier, document, due date, open balance and balance without payment order in minor units, plus lock status (already in a provisional list or unreleased OP).
- Blocking for withholdings: supplier tax profile defaults, per-OP overrides with reason, period accumulations, host-supplied rates and minimums, and the agency setting for when withholdings are computed.
- Client-collection evidence per item: related client invoice status, receipt number and date, cheque due date.
- Availability per funding source as of the payment date; checkbook next unreleased number.
- For foreign currency: book rate and payment rate from an authoritative source.
Ask only for missing material inputs; never ask for credentials or full bank account numbers in chat.

## Procedure
1. Build candidates: open balance > 0, due date in the window, matching supplier/type/media type/control-account filters, currency and payment method segment, and not locked by another list or pending OP (rule 5). Use `aging` to show overdue buckets per currency.
2. Attach pay-when-paid evidence per item: client invoice status and, when fully collected, receipt, date and cheque due date (P9 step 3). The reference only displays it; whether it is a hard gate is agency policy (gap 3, confirm locally). Flag items not yet collected.
3. Use `payment_terms` to confirm due and expected dates against the business-day calendar. Apply early-payment discount only when configured and the payment date is on or before the agreed date (rule 14) (configurable).
4. Save the selection as a Provisional list: every listed item is locked, even unticked ones, until approval; locked items still show as unpaid in reports (P9, rule 6).
5. Compute withholdings at the configured moment: at list calculation or at release, agency-wide, never per list (rule 8). Use `withholding` with host-supplied rates; joint ventures split by member share totalling 100% (rule 9, rule 36). Per-OP overrides of income-tax category, VAT % or IIBB % apply to that OP only, need a stated reason and are never written back to the supplier master (P11, rule 9).
6. Submit the list for approval by a different user with list-approval permission. On approval it becomes Definitive and unticked items unlock; only Definitive lists can be paid (P9).
7. Generate one OP per supplier from the Definitive list: one payment method, one bank account, whole list only, no partial payment of a list (P10, rule 7). Split OPs by debt currency (rule 15). Insufficient availability means re-approving a smaller list, not partial payment (section 10.4).
8. For manual OPs, check type-specific rules: one debt currency per OP, partial amounts allowed, no netting of an invoice against a credit note inside an OP — use an adjusting entry (P11, rule 35); client refunds only against unapplied advances or credit notes in the same currency (P14); cost advances only on client-approved estimate items and capped at the item amount (P15, rule 31); P&L manual lines need job, work order and cost centre.
9. Check the beneficiary through a trusted channel outside uploaded documents; a bank-detail change needs independent review per the control contract.
10. Propose the release: payment currency (foreign debt cannot be paid in another foreign currency), payment date and instruments. Normal cheque due = issue + 48 h; deferred cheque > 48 h; next cheque number = lowest unreleased in the checkbook; only endorsable third-party cheques; each instrument must map to an account of the right observation code and currency (P16, rules 15, 17, 19). Check total vs availability per source (P18).
11. Remember the accounting date is the release date, not the OP date: an OP dated the 31st released on the 2nd books in the next month (rule 21). Use `fx_revaluation` to preview exchange differences between book and payment rates (rule 16, inferred).
12. Bank-executed payments: export only within `today + 1 day < export date < today + 15 days`; exported OPs flip to Released, so the file is an irreversible step requiring explicit approval; the entry is recorded on bank import (P19, rule 23). Reconcile the import by OP and amount before marking paid.
13. Undo flows: delete a release only outside a pre-closed month (OP returns to Pending payment); delete an OP only if unpaid (number reusable within the configured gap); annul only a Paid OP with an open-period date, which reverses all withholdings, so a re-issue may compute a different net (P17, rules 10, 21, 22, 39).
14. Compute `payload_digest` over the list, each OP and each release proposal and hand off with approvals pending.

## Rules and locks
- Lifecycle: list New → Provisional (items locked) → Definitive (unticked unlocked) → Paid; OP Draft → Pending payment → Paid → Annulled; journal entry only in Paid/Released states.
- Never create parallel OPs for locked items (rule 6, section 10.3).
- List preparer ≠ list approver; OP creator ≠ releaser when split functions is on (configurable).
- One payment method and one bank account per list; whole-list payment only (rule 7).
- One debt currency per OP; no different foreign currency at payment (rule 15).
- No netting of invoices against credit notes inside an OP (rule 35).
- Withholding timing is an agency-wide setting (rule 8) (configurable); the withholding formula in the reference is a design assumption (rule 11, gap 2) (confirm locally).
- Costa Rica: OPs to foreign suppliers are blocked until the income-tax withholding is approved (rule 13); CL/PE/CR invoices need approved retentions before payment (supplier-invoicing R-41) (configurable).
- Release deletion forbidden in pre-closed months; annul with an open-period date instead (rule 21).
- Restricted deletion mode requires user, task number and reason (rule 39) (configurable).
- Supplier notifications go out only after release, and in practice after cheque signature (section 10.3).

## Calculations
- `aging`: overdue buckets per currency for candidate selection (`as_of`, strictly ascending `bucket_limits_days`, items; the reference report enters scales in descending order, so convert them).
- `payment_terms`: due and expected dates with `rule`, `term_days`, `delay_days`, holidays and weekend roll.
- `withholding`: per payment or cumulative in period with `payment_base_minor`, `accumulated_base_minor`, `accumulated_withheld_minor`, `non_taxable_minimum_minor`, `rate_bps`, `minimum_withholding_minor`.
- `fx_revaluation`: exchange difference preview for foreign-currency items between book and payment rates; it does not post.

```bash
python3 scripts/agency_tools.py withholding < input.json
```
```json
{"currency": "ARS", "method": "cumulative_period", "payment_base_minor": 85000000, "accumulated_base_minor": 40000000, "accumulated_withheld_minor": 650000, "non_taxable_minimum_minor": 22400000, "rate_bps": 200, "minimum_withholding_minor": 24000}
```

Not calculated by tools: withholding rates, categories, minimums and certificates; FX rates; early-payment percentages; availability balances; bank file formats. These come from the tax setup, authoritative rate sources, the bank and the treasury ledger.

## Approvals and segregation of duties
- The treasury lead prepares lists, OPs and release proposals; a finance approver with list-approval permission approves the list; release, bank file export, bank import confirmation, OP annulment and release deletion each need an authenticated human approval bound to the `payload_digest`, revision, currency, total and destination.
- The AI cannot approve its own proposal. A solo owner may approve under the documented owner policy; the owner's own reimbursements and any beneficiary bank change keep their independent-review requirement.

## Exceptions to escalate
- Supplier overdue or claiming while the client has not paid → finance approver decides; agency-collections for the client side.
- Item locked in another list or pending OP → treasury lead; do not duplicate.
- Multi-currency debt for one supplier → split OPs.
- Availability below the approved list → re-approve a smaller list.
- Checkbook exhausted or cheque number already released → agency-cash-settlement.
- Bank import with unknown OP or amount mismatch → treasury lead; status `uncertain`, no blind re-export.
- Foreign supplier withholding not approved → tax lead in agency-tax-compliance.
- Release date in a different period than the OP → controller in agency-period-close.
- Withholding recomputation after annulment changes the net → finance approver.
- Beneficiary bank detail changed → independent review before any release.

## Return and handoff
Return `payment_list_proposal`, `payment_orders_draft`, `withholding_schedule`, `release_proposal`, `bank_file_request`, `approval_requests`. Include tenant/client/job IDs, JobNumber where manual lines exist, list description and payment date, OP fiscal year and number, document ids and revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when a trusted bank or ledger receipt is verified), evidence references, blockers, approvals required and next stage.
**Owner:** Treasury lead (preparer) and finance approver. **Next:** agency-cash-settlement, agency-tax-compliance, agency-cash-forecast.

## Connectors and files
- Ledgers and payables: `xero`, `quickbooks`; payment rails where reviewed: `stripe`, `paypal`; official FX reference: `banxico-sie`; withholding certificates: `mx-cfdi-pac`, `arca-afip`; host marketplace documents/email for remittance advice. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
