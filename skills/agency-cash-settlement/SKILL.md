---
name: agency-cash-settlement
description: "Prepares deposits, transfers, bank charges, bank reconciliation, cheque lifecycle and card statements. Use when treasury must record or reconcile cash. Never moves money."
---

# Settle Bank, Cash and Cheques

This stage is the cash ledger of the agency circuit: receipts from agency-collections bring cash, transfers and third-party cheques in; releases from agency-payment-run send own cheques, transfers and endorsed cheques out; this skill records deposits, transfers and bank charges, manages cheque and card lifecycles, and reconciles every treasury movement against the bank statement before agency-period-close. It owns deposit (`Depósito Bancario`), bank charge/credit (`Débito/Crédito Bancario`), bank reconciliation (`Conciliación Bancaria`), cheque state and card statement (`Resumen de Tarjeta`) proposals. It never executes transfers, never posts, and never marks a reconciliation Definitive without a balance proof.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [payables-treasury.md](references/erp/payables-treasury.md) (P20 cheque pickup, P22 to P27, P28 withholdings suffered; lifecycles OwnCheck, ThirdPartyCheck, Deposit, BankReconciliation, CardStatement; rules 17 to 20, 24 to 27, 33; section 6; controls 10.3; gaps 5, 10, 16) — [receivables.md](references/erp/receivables.md) (P-17 receipt instruments and third-party cheques, P-18 void/delete guards when cheques were endorsed, rule 30, section 6 customer receipt entries).

Agency policy: apply `currencies`, `approvals`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- Collected cash or third-party cheques (`cheques de terceros`) must be deposited, or funds moved between own banks ("depósito bancario", "transferencia entre bancos").
- Bank statement charges or credits (maintenance, cheque tax, perceptions, interest) need recording with VAT ("débitos y créditos bancarios").
- The bank account must be reconciled to the statement ("conciliación bancaria").
- An own cheque must be registered, printed, signed, marked picked up, annulled, deleted or replaced after rejection; a client cheque bounced (`cheque rechazado`).
- A corporate card statement must be matched and its payment prepared, or availability per funding source checked before a payment run.

## Do not use when
- Applying client receipts to invoices, customer advances or credit exposure: use agency-collections.
- Payment lists, payment orders, withholdings at payment or releases: use agency-payment-run.
- Petty cash sheets and expense settlements: use agency-expenses.
- Cash projection by week or month: use agency-cash-forecast.
- Month-end FX revaluation of bank balances: use agency-accruals-revaluation.
- Manual journal entries outside treasury documents: use agency-general-ledger.

## Required inputs
- Blocking: bank account id with observation code and currency, statement period, statement opening and closing balances and lines in minor units (read-only export or file).
- Blocking for reconciliation: the last Definitive reconciliation (opening reconciled balance and its date) and the treasury movements since then (OPs, receipts, deposits, bank debits/credits, funds-movement entries).
- For deposits: portfolio cheques with internal code, due date, endorsable flag and currency; cash amounts; source bank for transfers.
- For bank charges: bank tax ID, movement date, account per line by observation code, VAT account, job/work order/cost centre.
- For cheques: checkbook range, OP link, print and signature status, pickup date; for rejections the rejection date and replacement instruments.
- For cards: card master, statement due date, rendered petty-cash items and installment adjustments, issuer statement totals per currency.
Ask only for missing material inputs; never ask for credentials or full account numbers in chat.

## Procedure
1. Confirm identity and currency: deposits and transfers only in the destination account's currency (P22, rule 15). Prefer recording inter-bank transfers with a miscellaneous OP in agency-payment-run for control (P22).
2. Deposit proposal: select portfolio third-party cheques, cash and transfers in; clearing hours drive availability; propose the entry Dr bank / Cr values-to-deposit, cash or source bank (P22, section 6). Validate with `journal_check`.
3. Bank charges and credits: expense lines only to observation-code-07 accounts, IIBB perceptions to code 60, VAT perceptions to code 15; VAT = net × rate of the VAT account, overridable; exempt lines carry no VAT account (P23, rule 25). Only charges recorded here feed the VAT purchase book. Split a charge across cost centres or jobs with `allocate`; validate the entry with `journal_check` including locked periods.
4. Reconciliation: start from the last reconciliation date; system movements arrive pre-ticked, so untick all and tick only items that appear on the statement; reconcile only picked-up cheques (P24, P20).
5. Match movements to statement lines by amount plus cheque number or reference, then amount plus date window (section 10.2). For each pair, compare amounts with `reconcile` (system amount as ordered, statement amount as delivered and invoiced, tolerance 0 unless policy says otherwise); any `hold` stays unreconciled.
6. Balance proof: `reconciled_balance = opening_reconciled_balance + Σ ticked deposits/credits − Σ ticked payments/debits` must equal the statement closing balance before proposing Definitive (rule 24). Otherwise save Provisional with the unreconciled list.
7. Remember reconciliation sees only treasury-originated movements and funds-movement journal entries; manual ledger adjustments of other types never appear (P24). Report them as reconciling items, not matches.
8. Own cheques: register checkbooks (default 50); print only for OPs paid by cheque; mark signed, printed, picked up; annul only cheques linked to an OP after undoing the release; printed cheques can only be annulled, never deleted; unused unlinked cheques can be deleted (P25, rules 17, 18).
9. Own cheque rejected: propose the rejection dated at rejection date with replacement instruments in the same operation, unless a deferred-replacement setting exists (P26, rule 20).
10. Third-party cheque rejected: the supplier debt reopens if the cheque was endorsed (replacement needed), and the client amount moves to the rejected-cheques account (observation code 45), not to the client's invoice account; no debit note or bank fee is generated (P26, rule 20). Route the client replacement to agency-collections.
11. Corporate card: build the statement from rendered items and installment adjustments, untick items not on this statement, and require Σ selected items per currency = issuer total (P27, rule 33). Payment OP only on or after the due date, one line per currency, via agency-payment-run.
12. Availability: `availability = opening balance + deposited collections − cheques in transit − transfers in transit` per source (rule 26; wording loose, gap 16 — confirm locally). Report negative balances.
13. Withholdings suffered: tick reconciled certificates against the withholding account and drill to the originating receipt (P28).
14. Compute `payload_digest` over each proposal and hand off; never report a deposit, charge or reconciliation as saved without a trusted ledger receipt.

## Rules and locks
- Deposits, transfers and instruments only in the account's currency; instrument accounts must carry the right observation code (P16, P22).
- Reconciliation is extra-accounting; Definitive only with an exact balance proof; it sets the next opening balance; annul or modify only the latest reconciliation (rule 24).
- Only endorsable third-party cheques may pay suppliers; non-endorsable ones can only be deposited (rule 19, receivables rule 30).
- A receipt cannot be voided or deleted once its third-party cheques were handed to suppliers (receivables P-18).
- Printed cheques are annulled, never deleted; annul only OP-linked cheques after the release is undone (rule 18).
- Normal cheque due = issue + 48 h; deferred cheque due must be > 48 h (rule 17).
- Treasury entries are read-only views; to change one, annul or delete the source document and recreate it (section 6).
- Deferred cheques are enabled per country; deferred rejection replacement uses two unnamed settings (gap 10) (confirm locally).
- Distinguish initiated, bank-accepted and settled; unexplained cash stays unapplied, never forced onto an invoice.
- Locked periods block entries; the host owns period state.

## Calculations
- `reconcile`: per matched pair, same-currency amount comparison with an explicit tolerance; a `hold` keeps the pair unreconciled.
- `allocate`: split a bank charge, card installment or deposit across cost centres, jobs or documents by integer weights with exact conservation.
- `journal_check`: validate proposed deposit, bank charge, rejection and card entries for balance per currency, one-sided lines, dimensions and locked periods.

```bash
python3 scripts/agency_tools.py journal_check < input.json
```
```json
{"entry_id": "BCH-2026-0412", "posting_date": "2026-10-09", "locked_periods": ["2026-08"], "lines": [{"line_id": "1", "account_id": "BANK-FEES-07", "currency": "MXN", "debit_minor": 125000, "credit_minor": 0, "required_dimensions_present": true}, {"line_id": "2", "account_id": "VAT-CREDIT", "currency": "MXN", "debit_minor": 20000, "credit_minor": 0, "required_dimensions_present": true}, {"line_id": "3", "account_id": "BANK-43-001", "currency": "MXN", "debit_minor": 0, "credit_minor": 145000, "required_dimensions_present": true}]}
```

Not calculated by tools: VAT rates per VAT account, perception regimes, FX rates, the balance proof sum itself (show it explicitly), availability, statement parsing and automatic reconciliation codes (undocumented, gap 5). These come from the tax setup, bank data and the treasury ledger.

## Approvals and segregation of duties
- The treasury lead prepares deposits, charges, reconciliations, cheque actions and card statements; a different authorized user approves Definitive reconciliations, rejections with replacement instruments, card payments and any annulment or deletion.
- Annul/delete of cheques, deposits, bank charges and reconciliations need an authenticated approval bound to the `payload_digest` with audit fields (user, task number, reason) (section 10.3). The AI cannot approve its own proposal; a solo owner may approve under the documented owner policy.

## Exceptions to escalate
- Balance proof does not close → treasury lead; keep Provisional, list unreconciled items.
- Statement line with no treasury movement (manual GL entry or unknown cash) → chief accountant in agency-general-ledger; leave unapplied.
- Own cheque rejected → treasury lead with replacement instruments; supplier notified after release.
- Third-party cheque rejected → agency-collections for client replacement; agency-payment-run if the supplier debt reopened.
- Cheque issued but not picked up for a long time → treasury lead; exclude from reconciliation.
- Card statement total mismatch → card holder and controller; do not save.
- Deposit currency differs from account → reject and split.
- Negative availability before a payment run → finance approver in agency-payment-run.
- Bank import or timeout with unknown outcome → status `uncertain`; query by reference, never re-record blindly.

## Return and handoff
Return `deposit_proposals`, `bank_charge_entries`, `reconciliation_report`, `cheque_actions`, `card_statement_match`, `availability_snapshot`, `unapplied_cash`. Include tenant and bank account ids, statement period, document ids and revision, linked OP/receipt numbers, status (`draft`/`blocked`/`pending_approval`/`completed` only when a trusted ledger receipt is verified), evidence references, blockers, approvals required and next stage.
**Owner:** Treasury lead. **Next:** agency-period-close, agency-cash-forecast, agency-collections, agency-payment-run.

## Connectors and files
- Ledgers and bank feeds: `xero`, `quickbooks`; payment processors as read-only settlement evidence: `stripe`, `paypal`; official FX reference: `banxico-sie`; host marketplace documents/email or warehouse for statement files. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
