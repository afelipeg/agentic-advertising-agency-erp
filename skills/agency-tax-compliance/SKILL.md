---
name: agency-tax-compliance
description: "Prepares e-invoice authorization (Mexico CFDI, Argentina CAE), VAT books, withholdings, certificates and tax positions from your tax tables. Use for tax steps. Never stamps or files itself."
---

# Tax Compliance

This stage wraps the fiscal side of the circuit: it takes drafts approved in `agency-client-billing`, supplier documents from `agency-payables`, receipts from `agency-collections` and payments from `agency-payment-run`, and prepares authorization requests (CAE, CFDI stamping), books, certificates and month-end positions for `agency-period-close`. It owns fiscal numbering checks, tax recomputation, book reconciliation and statutory export packs. It never invents tax rates, signs or stamps documents itself, files returns or posts position entries; country tables and credentials stay with the host.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [receivables.md](references/erp/receivables.md) (P-14 fiscal validation, §4.6, §5 rules 13–18, 25, 28, §8 country matrix, gap 13); [supplier-invoicing.md](references/erp/supplier-invoicing.md) (S-CAI, R-03, R-12, R-23 to R-29, R-41, §8 country matrix); [accounting.md](references/erp/accounting.md) (P05 withholding settlement, P14 VAT position, P15 non-computable VAT, P16 IIBB position, P29 statutory files, BR-39 to BR-43, BR-50 close order). Below `AR-Rn` = receivables §5 rule n.

Agency policy: apply `agency`, `approvals`, `taxes` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Request CAE for today's invoices on point of sale 0003", "solicitar CAE", "timbrar CFDI", "adjuntar XML timbrados".
- Checking fiscal numbering gaps per point of sale × document type × letter, or a CAE/PAC rejection.
- Reconciling the VAT sales book (`Libro IVA Ventas`) and purchase book (`Libro IVA Compras`) to the ledger.
- Withholding and perception regimes (`retenciones`, `percepciones`, IIBB, ISR/IVA, Renta/ICA), withholding certificates made and suffered, certificate numbering.
- Month-end VAT position (`Posición de IVA`) and gross-receipts position (`Posición de IIBB`), statutory exports (SICORE, ARCIBA, SIRE/CITI, DIAN, SENIAT, SUNAT books).

## Do not use when
- Computing invoice content, agency fee or split billing → `agency-client-billing`.
- Registering supplier documents or three-way match → `agency-payables`.
- Applying customer withholding certificates inside a receipt → `agency-collections`.
- Withholdings computed on a payment order → `agency-payment-run` (this skill supplies the regime and validates).
- Running the close checklist and locks → `agency-period-close`; ledger entries → `agency-general-ledger`.
- Connector wiring for PAC or AFIP/ARCA credentials → `agency-integrations`.

## Required inputs
- **Blocking:** tenant, legal entity, country, period, fiscal year and its open/pre-closed status.
- **Blocking:** host-supplied country tables: VAT rates by VAT account, perception and withholding regimes (rates, minimum taxable base, non-taxable minimum, accumulation method), IIBB jurisdictions with rates and multilateral percentages, certificate numbering series. No tables are bundled; missing tables block.
- **Blocking for authorization:** approved document drafts with point of sale (normal or electronic), type, letter, number proposal, client fiscal data (tax id, VAT condition, postal address where mandatory), currency with its fiscal identifier, and the approval digest from billing.
- Ledger balances for VAT debit (09/10/0A), VAT credit (11/12/13), payable 17, credit balance 08, withholding and perception accounts; sales and purchase sub-journals; withholdings made and suffered with certificate numbers.
- PAC or AFIP/ARCA access only through a host connector; never ask for certificates, keys or passwords in chat.

## Procedure
1. Confirm the period is open or pre-closed as the step requires (VAT position needs pre-close, accounting P14) and that country tables, accounts and numbering series exist. Missing table or identifier → `blocked`.
2. Validate each draft before authorization: recompute VAT by rate and the total with `invoice_check` (AR-R14); confirm perceptions follow the client profile and validity (AR-R15); a rounding line is allowed only within the cap and never where the authority recalculates VAT (AR-R13). Check zero-value documents are not sent in Chile or Colombia (AR-R28) and the currency carries its fiscal identifier (receivables §8.1).
3. Check fiscal numbering: next number = last used + 1 per point of sale × type × letter (AR-R25). Report gaps from deleted documents and the manual counter repair needed; never reuse a voided number; propose bulk void of unissued ranges only with approval.
4. Argentina CAE (P-14): build the request for all documents in status `Pendiente Solicitar` on the electronic point of sale and request type (`Normal` or `Exportación`), never filtered by client, because authorization is consecutive and an earlier pending blocks the rest. Capture CAE and expiry, or the rejection reason (`Motivo del Rechazo`), propose the fix and resubmission. Use `Solicitar últ. comp. aprobado` to resync numbering. Check certificate validity; for contingency CAI forms, record code and expiry per letter for the VAT position.
5. Mexico CFDI (receivables §8.2 and gap 13): prepare the stamping request for the PAC through the host connector, attach the stamped XML from the configured path (`Adjuntar XML Timbrados`) and refresh status (`Actualizar Estado Comprobantes`). Issue the `Anexo` with direct-billing invoices. CFDI versions, cancellation flows and payment complements (`complemento de pago`) are outside the reference; treat them as host-configured agency policy and require the host's validated schema.
6. Supplier side: validate fiscal codes on supplier documents (AR CAI/CAE, DO NCF, CO support documents) and taxpayer status with expiry (R-29); flag suppliers `En Conflicto` from apocryphal lists. Check the total equality rule (R-03) and VAT per line by VAT account with `0000` as not subject (R-23); difference lines without VAT distort the purchase book (R-24).
7. Withholdings and perceptions: compute expected amounts with `withholding` per payment or cumulative in the period from host rates, non-taxable minimum and minimum withholding (CO/MX at registration, R-26; CO accumulated base with deductions, R-27; AR at payment). For withholdings suffered, reconcile certificates captured at collection; settle late certificates through a customer adjustment against the withholding account (accounting P05). Retention approval for foreign suppliers in CL/PE/CR (R-41) must be approved before payment.
8. Certificates made: next certificate number = last stored + 1 per withholding type and year, with optional joint VAT and income-tax numbering (BR-43). Produce the certificate list; issuing and sending them needs approval.
9. VAT books: reconcile the sales book and purchase book by rate and taxpayer category to the ledger VAT accounts and sub-journals; non-computable VAT must be reclassified to I7 before the position (BR-40).
10. VAT position (BR-39): Σ VAT debit − Σ VAT credit − perceptions suffered − withholdings suffered up to the entry date ± transfers; positive to payable 17, negative to credit balance 08 carried forward; optional application of a credit to other tax accounts. Present the proposed entry; posting needs approval.
11. IIBB position (Argentina, accounting P16, BR-41, BR-42): base = agency own income (cost difference + agency service + fees + bonuses) with per-jurisdiction rates; criterion multilateral agreement (percentages total 100%), real income by jurisdiction or home jurisdiction. Preconditions: registers updated, subledgers closed, OTs closed if bridge accounts, GI provision posted.
12. Statutory exports (accounting P29): prepare SICORE/SIRE withholding files, ARCIBA/SIRFT IIBB files, SIRED/CITI or unified VAT book exports, Colombian exogenous information and DIAN media (drafts only), SENIAT, SUNAT books, Guatemala SAT TXT, DGI TXT. Validate record counts and totals against the books; mark them `draft` until the host files them.
13. Assemble the authorization or filing pack with tool outputs, compute `payload_digest`, and return `pending_approval`. Report CAE numbers, stamped UUIDs or filing receipts only when returned by the authority through a trusted connector.

## Rules and locks
- Never invent or default a tax rate, regime, threshold or layout; country tables are host-supplied and versioned.
- Request authorization consecutively per point of sale; never filter a CAE batch by client (P-14).
- Printed (or PDF) documents count as delivered; only authorized documents are printed for clients.
- Voided numbers are burnt; deleted documents leave gaps that need manual counter repair (receivables P-16).
- VAT position requires the month pre-closed; annulling it deletes the entry and re-allows documents (accounting P14).
- Posted tax entries are immutable; corrections are reversals (accounting BR-07).
- Withholdings only through observation-coded accounts; customer VAT withholding transfer locks once used in a payment order (accounting P05).
- Zero-value documents prohibited in CL and CO; partial NC cancellation prohibited in CO (receivables §8.2).
- CFDI cancellation and payment complements are outside the reference (confirm locally).
- Mexico SAT e-accounting is not covered beyond the tax-rubro tab (accounting gap 14, confirm locally).

## Calculations
- `invoice_check`: VAT by rate, perceptions, other charges and netted withholdings against the declared total with an explicit rounding tolerance; status `matched`, `rounding_adjustment` or `mismatch`. Use it on sales drafts and supplier documents.
- `withholding`: per-payment or cumulative-period withholding from host rate, non-taxable minimum, prior accumulated base and withheld amount, and minimum withholding.

```bash
python3 scripts/agency_tools.py invoice_check < input.json
```
```json
{"currency": "ARS", "lines": [{"line_id": "L1", "net_minor": 8550000, "vat_bps": 2100}, {"line_id": "L2", "net_minor": 1282500, "vat_bps": 2100}], "perceptions_minor": 0, "other_charges_minor": 0, "withholdings_netted_minor": 0, "declared_total_minor": 11897325, "rounding_tolerance_minor": 100}
```
Not calculated by tools: tax rates and regimes, perception eligibility, IIBB jurisdiction split, VAT and IIBB position netting, file layouts, CFDI XML and CAE validity. Take rates and layouts from host country tables and authority schemas; positions are presented from ledger balances supplied by the host.

## Approvals and segregation of duties
- Tax analyst prepares; tax lead approves authorization batches, certificates, positions and exports; the billing lead remains owner of document content.
- Requesting CAE, stamping CFDI, voiding number ranges, issuing certificates, posting VAT or IIBB positions, applying VAT credits and filing statutory files require an authenticated human approval bound to the `payload_digest`, entity, period, document range and totals.

## Exceptions to escalate
- CAE rejection or PAC error → tax lead; fix data, resubmit in sequence.
- Expired AFIP certificate or e-invoice service down → tax lead and system owner; CAI contingency only if configured.
- Numbering gap or duplicate number → billing lead and controller.
- Missing country table, regime or currency fiscal identifier → tax lead; block.
- Book does not reconcile to ledger or sub-journal → chief accountant.
- Withholding certificate missing, `0000000` or mismatched → collections lead.
- Supplier taxpayer status expired or apocryphal → AP lead; hold payment.
- Foreign-supplier retention pending approval (CL/PE/CR) → tax lead before payment run.
- Non-computable VAT reclassified after the VAT position → chief accountant; annul and rerun.
- Request outside the reference (CFDI cancellation, payment complement) → tax lead with host-configured policy.

## Return and handoff
Return `authorization_requests`, `numbering_report`, `vat_books_reconciliation`, `withholding_perception_schedule`, `certificate_register`, `tax_positions`, `statutory_exports`. Include tenant, entity, country, period, point of sale, document type, letter and number ranges, currency, amounts in minor units, authority references only when returned, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence, blockers, approvals required and next stage.
**Owner:** Tax lead. **Next:** agency-collections, agency-payment-run, agency-period-close, agency-general-ledger.

## Connectors and files
- `mx-cfdi-pac` for CFDI stamping and status, `arca-afip` for CAE and taxpayer status, `banxico-sie` for official MXN rates where required; `xero` or `quickbooks` for ledger balances. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` for sales or purchase document extracts.
