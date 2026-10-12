---
name: agency-payables
description: "Logs supplier invoices, checks duplicates and math, picks the load type and prepares registration with derived accounts. Use when supplier documents arrive. Never posts or pays itself."
---

# Register Supplier Invoices

This stage turns controlled supplier documents into recognised payables. Upstream, agency-delivery-reconciliation controls each document against the pending-to-receive balance; this skill logs the arrival in the reception register (`Recepción de Facturas`, traffic number), deduplicates, chooses one of the ten load types (`Tipo Carga`), checks totals and taxes, and prepares the registration (`Registración`) that posts to the GL and AP subledger; downstream, agency-payment-run pays the open balance. It owns the reception record, the duplicate check and the registration proposal. It never posts or pays by itself, never edits a posted document's accounts or amounts, and never writes back supplier tax master data.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [supplier-invoicing.md](references/erp/supplier-invoicing.md) (S-HDR, S-SAVE, section 2.1 load types, P-11 to P-13, P-20 to P-29, lifecycles 4.2 and 4.4, R-01, R-03, R-12 to R-41, section 10.3) — [payables-treasury.md](references/erp/payables-treasury.md) (P1 to P4 reception, return, counter-receipt, batches; P7 portal validation; P8 platform taxonomy lines; rules 1 to 4; lifecycles of InvoiceReceipt and PortalInvoice).

Agency policy: apply `currencies`, `approvals`, `taxes`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- A supplier invoice, credit note (`NC`), debit note (`ND`) or Mexican `Anexo` arrives by email, portal, XML or paper and must be logged ("ingresar comprobante", "tráfico de facturas").
- A document must be returned to the supplier with a reason, re-entered after correction, or assigned to a responsible checker.
- A controlled document needs a registration proposal: media, production or expense invoice, manual load, or credit note for volume (`N/C por Volumen`) or supplier commission (`confidencial`).
- An advance media purchase (`Compra Anticipada`) is invoiced, consumed by later invoices, or its unconsumed remainder cancelled.
- A full-cancellation credit note (`NC anula factura`) is received.

## Do not use when
- Matching the document to spots, items or request lines and recording differences: use agency-delivery-reconciliation.
- Proposing payment lists, payment orders, withholdings at payment or releases: use agency-payment-run.
- Computing volume, overcommission or incentive contract amounts: use agency-rebates.
- E-invoice validation rules, VAT books or withholding regimes: use agency-tax-compliance.
- Supplier master creation or account mapping on media/production types: use agency-master-data.
- Expense requests, sheets and settlements: use agency-expenses.

## Required inputs
- Blocking: supplier (may be blank only at reception), document type, letter and point-of-sale-number where used, document date, accounting date, currency, declared gross total in minor units, and source evidence (PDF/XML hash).
- Blocking for registration: the saved control or pending selection from agency-delivery-reconciliation, VAT account per line, perceptions, period status and user permission for pre-closed months.
- Payment term from the supplier master (editable; recomputes due date).
- Accounts on the media type, production type or expense concept (R-31); observation-coded accounts for advances (code 89), perceptions and rounding.
- For credit notes: volume or commission basis (orders, percentages, client share, counter-account choice).
Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Log reception: assign the next traffic number with today's entry date, capture document data, gross total and responsible checker; state `Pending` (P1). Portal or mail-imported documents enter the validation queue (P7). Spreadsheet imports are treated by the reference as already reviewed (P1) — require evidence anyway (agency policy).
2. Deduplicate by supplier + document type + letter + number before anything else (section 10.3); also compare source hashes across channels. A hit returns the existing record id, never a second obligation.
3. Return defective documents with a predefined return reason, priority and text, assigning a return number; re-enter the same record when the corrected document arrives (P1, P2). Returned documents cannot be registered (rule 1).
4. For portal documents, require formal/tax validation and requester confirmation by two different users before approval; reject with a classified reason or approve; only approved rows can be posted (P7, rule 2).
5. Capture the header (S-HDR): accounting date drives the period, due date = document date + payment term (use `payment_terms`), exchange rate only when the document or order currency is foreign (R-14).
6. Choose the load type from what the supplier has pending (R-01): media, media NC/ND, production, production NC, volume NC, expense, commission NC for production or media, manual production, manual media. Manual types need written justification in remarks (section 10.3).
7. Recover the control from agency-delivery-reconciliation; for platform invoices confirm every taxonomy line is associated with a plan order, otherwise route unmatched lines back (P8).
8. Run `invoice_check`: VAT is derived from each line's VAT account (`0000` not subject) (R-23); detail + taxes + extra lines − netted withholdings must equal the declared total (R-03). Accept a rounding line only within the configured threshold (R-12, P-27).
9. Derive accounts automatically on automatic loads: cost from the media type or production type of the plan/estimate, expense account from the concept (R-39). On manual loads, a cost account forces medium or production type and a cost centre for P&L accounts (R-40).
10. Credit notes: volume NC expected credit = Σ order amounts × Σ percentages, proportional allocation for the amount variant, optional client share as a pending client credit (R-15 to R-17, P-22, P-23); commission NCs only for items flagged to receive supplier NC (R-19, P-24, P-25). Use `tiered_commission` with `method: flat` for the expected amount.
11. Advance media purchase: register against an observation-code-89 account (P-12); consumption invoices net to zero via an advance line and are blocked when the balance is 0 (P-11, R-37); cancel the remainder with an NC, total or reduced (P-13).
12. Full-cancellation NC: only for the total of an invoice/ND, not in Colombia, not for special suppliers; warn if a payment order exists; it releases the order back to pending to receive and creates an association adjustment entry (P-29, R-35).
13. Check the period: accounting date in an open month; in a pre-closed month only with permission, local currency and balance-sheet accounts only (R-32, P-26). Run `reconcile` on the controlled totals as a final gate, compute `payload_digest`, and submit the registration proposal for approval.

## Rules and locks
- Reception before posting: Pending → Returned ⇄ Re-entered → Posted (terminal); delete only before posting (lifecycle InvoiceReceipt).
- Duplicate key: supplier + type + letter + number; investigate collisions, never guess.
- No posting without a pending unless the load type is manual with justification (section 10.3).
- Total equality is blocking except the configured rounding threshold (R-03, R-12) (configurable).
- Accounts are never chosen by the clerk on automatic loads (R-39); missing accounts on media/production types block registration (R-31).
- Mandatory PO and PO approval gate production invoices when configured (R-11) (configurable).
- Posted documents are immutable except due date and remarks (R-33); deletion only if unpaid and period not pre-closed, and it reopens pendings (R-34).
- At registration, unpaid balance = balance without payment order = total (R-38).
- Foreign-supplier withholdings in CL/PE/CR need assign → approve before the invoice can be paid (R-41) (configurable).
- Direct invoices not passing through the agency touch neither GL nor AP; VAT-only pass-through is Mexico-specific (R-21) (confirm locally).

## Calculations
- `invoice_check`: lines with `net_minor` and `vat_bps`, `perceptions_minor`, `other_charges_minor`, `withholdings_netted_minor`, `declared_total_minor`, `rounding_tolerance_minor`.
- `reconcile`: final ordered/delivered/invoiced gate on the controlled totals; `hold` blocks registration.
- `payment_terms`: due date from document date, `term_days`, `rule`; changing the due date implies a term change (S-HDR).
- `tiered_commission`: expected volume or commission credit (`method: flat`, `flat_bps` = sum of percentages) and client share (`client_share_mode`).

```bash
python3 scripts/agency_tools.py invoice_check < input.json
```
```json
{"currency": "MXN", "lines": [{"line_id": "L1", "net_minor": 2000000, "vat_bps": 1600}, {"line_id": "L2", "net_minor": 150000, "vat_bps": 0}], "perceptions_minor": 0, "other_charges_minor": 0, "withholdings_netted_minor": 0, "declared_total_minor": 2470000, "rounding_tolerance_minor": 100}
```

Not calculated by tools: VAT rates behind each VAT account, perception and withholding tables, fiscal code validation (CAI/CAE, CFDI, NCF), FX rates and duplicate lookups against the ledger. These come from the tax setup, authoritative connectors and the host ledger.

## Approvals and segregation of duties
- The AP clerk logs and prepares; the responsible checker validates the paper; on portal documents the formal validator and the requester must be different users; the AP lead or controller approves registration.
- Posting, deletion of a posted document, full-cancellation NCs (especially with an existing payment order), registration in a pre-closed month, manual entries hitting P&L and client share percentages need an authenticated approval bound to the `payload_digest`.

## Exceptions to escalate
- Supplier not in master at reception → data steward in agency-master-data.
- Duplicate document number for the same supplier → AP lead; hold both.
- Portal amount differs from order → agency-delivery-reconciliation.
- Total mismatch above rounding threshold → return to supplier.
- Missing accounts on media/production type → agency-master-data.
- Accounting date in a closed or pre-closed month → controller in agency-period-close.
- Full-cancellation NC on an invoice already in a payment order → treasury lead in agency-payment-run.
- Advance purchase without remaining balance → AP lead; register as normal invoice or dispute.
- Supplier fiscal status not validated (R-29) → agency-tax-compliance.

## Return and handoff
Return `reception_log`, `duplicate_check`, `normalized_invoice`, `registration_proposal`, `holds`, `posting_receipt`. Include tenant/client/job IDs, JobNumber, traffic number, supplier + type + letter + number, revision, load type, status (`draft`/`blocked`/`pending_approval`/`completed` only when a trusted ledger receipt is verified), evidence references, blockers, approvals required and next stage.
**Owner:** AP lead. **Next:** agency-payment-run, agency-tax-compliance, agency-accruals-revaluation.

## Connectors and files
- Ledgers: `xero`, `quickbooks`; e-invoice validation: `mx-cfdi-pac`, `arca-afip`; document intake from host marketplace email/documents; aggregators `composio`, `zapier` only with inner-tool approval. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
