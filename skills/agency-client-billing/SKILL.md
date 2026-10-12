---
name: agency-client-billing
description: "Prepares client invoices and credit/debit notes from plans, estimates and fees approved for billing: fee, VAT, partial and split billing. Use to turn pending-to-bill into invoices."
---

# Client Billing

This stage sits between operations and collection: approved media plans (`Pauta`), production estimates (`Presupuesto de Producción`) and fee contracts create pending-to-bill (`pendiente de facturar`); this skill turns it into draft sales documents (`Factura`, `Nota de Débito`, `Nota de Crédito`); `agency-tax-compliance` authorizes them and `agency-collections` collects them. It owns the billing selection, the invoice computation and credit/debit-note proposals. It never assigns fiscal numbers, posts entries, sends documents, bills unapproved work, or treats direct-billed media spend as agency revenue.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [receivables.md](references/erp/receivables.md) (§2.1–2.17 processes P-01 to P-16, §5 rules 1–15, 20, 25–29, §10.3–10.4); [production.md](references/erp/production.md) (P19–P20 approval for billing, §5 rules 12, 16, 20–22, 33); [media-planning.md](references/erp/media-planning.md) (P31 approve for billing, §5 R9–R11, R15, R32, §7 handoff to AR). Below, `AR-Rn` = receivables §5 rule n, `PR-Rn` = production §5 rule n, `MP-Rn` = media-planning §5 rule n.

Agency policy: apply `currencies`, `approvals`, `taxes`, `commercial`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Bill the approved October schedules for client X", "facturar pendientes", "facturación de medios, producción y fees".
- Building an invoice from approved estimate lines, including partial billing (`% de anticipo`, amount per item).
- Billing agency service separately (`Comisión General`), fee instalments (`Cuotas de Fee`) or order differences after supplier-invoice reconciliation.
- Preparing a credit note that cancels an invoice (`N/C Anula Factura`), a manual NC/ND, or an advance sale (`Venta Anticipada`) and its consumption.
- Splitting a document across billing clients with a split code (`Código de Apertura de Facturación`).

## Do not use when
- Client prerequisites (PO, service entry, mandatory attachment) are unchecked → `agency-billing-requirements` first.
- Authorizing, stamping or numbering e-invoices (CAE, CFDI via PAC) or VAT books → `agency-tax-compliance`.
- Applying receipts, withholding certificates or chasing overdue invoices → `agency-collections`.
- Supplier commission, incentive or overcommission invoices to suppliers and client rebate NCs → `agency-rebates`.
- Releasing spots or estimate lines for billing → `agency-media-planning`, `agency-production-estimating`; fee instalment approval → `agency-fee-contracts`.
- Credit-limit decisions at client approval → `agency-budget-control`.

## Required inputs
- **Blocking:** tenant, billing client (`Cliente de Facturación`) and owner client, JobNumber/OT, point of sale (`Sucursal`), document type and letter, currency, billing type and subtype (media, production, fee).
- **Blocking:** trusted pending-to-bill extract with source ids (plan/schedule/order/item, estimate/line, fee instalment), approval-for-billing state, version, due-date type and product per line.
- **Blocking:** billing-client master: agency service base and %, `Junto`/`General` timing, direct/indirect default and per-media exceptions, VAT condition, perception profile, term mode, `Práctica Auditoría` and `En Conflicto` flags.
- **Blocking:** VAT rates and perception/withholding rules from host tax tables; supervisor rounding cap.
- Readiness result from `agency-billing-requirements`; advance-sale balances; split-code lines; previous invoices and credits on the same sources.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Confirm the billing client is vigent and warn if `En Conflicto`. Check the JobNumber billing code: `0` never bills, `?` blocks until a billing client exists, `*` needs a split code per document. Require a ready result from `agency-billing-requirements`; otherwise return `blocked`.
2. List pending-to-bill by client (recommended) or by document, filtered by currency, billing type and subtype (P-01, P-02, P-04). Include only lines approved for billing (PR-R33; media-planning P31). Flag schedules not yet ad-verified as estimate billing (a warning, not a block).
3. Enforce selection partitioning: one source family per document, never mixing plans, estimates and fees, media and production apart (AR-R1); one currency per document (AR-R2, PR-R16); single due date and single product when those controls are on (AR-R12). Additional costs (`Costos Adicionales`) bill as one unit, never item by item. Split violating selections into separate drafts.
4. Resolve direct vs indirect per line (AR-R5): indirect bills investment plus agency service; direct bills only agency service, and direct spend never becomes agency revenue. For `Práctica Auditoría` clients block lines where cost ≠ sale (AR-R27). Bonus lines bill zero; barter bills only if configured (MP-R9).
5. Compute media net and agency service on the configured base (`Bruto`, `Neto`, `1° Descuento` or fixed) with `discount_cascade` (AR-R3, MP-R11). Compute production sale, cost and service per currency with `estimate_totals` (PR-R12). Never charge agency service on fee-linked estimates.
6. Apply billing timing (AR-R4): `Junto` = investment and service on one document; `General` = service on a separate `Comisión General` document, only after the investment is billed (P-03).
7. Apply production partial billing (P-02, AR-R10): `% de anticipo` over the selection, or an amount per item not above its remainder. Warn that a partly billed item becomes non-editable; recommend splitting advance and remainder into two items first.
8. Apply advance-sale consumption when the client holds an advance invoice (P-06b, AR-R9): each `Imp. a Descontar` ≤ its remaining balance and their sum equals the draw. With `Incluye S. Ag. = Sí` the document totals zero, which Chile and Colombia forbid; route to the internal point of sale (suggested 99) (AR-R28).
9. Apply split billing (AR-R26): at least two billing clients of the same owner client summing to 100%; allocate with `allocate` so minor units are conserved; one draft per billing client.
10. Compute VAT per line from the VAT account linked to the revenue account and add perceptions per the client profile from host tables (AR-R14, AR-R15). For CO/GT list invoicing withholdings only when the client master requires them (AR-R17). Verify every draft with `invoice_check`; rounding only within the supervisor cap and never where the authority recalculates VAT (AR-R13).
11. Compute the due date with `payment_terms` from the client term, or the product term when the client's mode is by product (AR-R20). Flag weekend and holiday rolls.
12. Choose the version: `Final` locks the source; `Inicial` keeps it editable and later deltas return as differences (P-01, AR-R11). For order differences (P-05) bill positive deltas as invoice/ND and negative deltas as credit.
13. For corrections, propose the right document: `N/C Anula Factura` releases the source to pending; partial cancellation is not allowed in Colombia (AR-R29); a collected invoice needs `Restringe NC cliente con comprobante asociado` off. Under the NC/ND approval circuit, unassociated NC/ND stay provisional (`Ingresada`) until approved. Prefer void (`Anular`, number burnt) over delete (numbering gap) (P-16).
14. Assemble the draft pack (source ids, tool outputs, warnings), compute `payload_digest` and return `pending_approval`. Numbering (last used + 1 per point of sale × type × letter, AR-R25), posting and authorization happen only after approval, in the host ERP and `agency-tax-compliance`. Billed never means collected.

## Rules and locks
- Only approved-for-billing sources are billable; estimates pending billing approval cannot be invoiced (PR-R33).
- One source family, one currency, one billing client (or one split share) per document (AR-R1, AR-R2).
- Invoiced estimate lines lock sale, discount, agency service and supplier commission (PR-R20); partly billed items cannot be edited (AR-R10).
- `Final` locks the source; `Inicial` must later close with a difference document or mark-as-billed (AR-R11).
- An NC cancelling an invoice and an NC cancelling an advance-sale remainder cannot be deleted or voided once issued; warn before proposing (P-15, P-06d).
- Mark pending as billed (P-13) creates no entry, reduces margin and records the user; propose only with a reference number and supervisor approval.
- Rounding stays within the supervisor cap (configurable) (AR-R13).
- Foreign-currency billing restrictions conflict between screens and guides (confirm locally); never convert currency inside a document.
- Zero-value documents are prohibited in Chile and Colombia (AR-R28).
- No billing-client change once anything in the JobNumber is invoiced; route to `agency-job-lifecycle`.

## Calculations
- `discount_cascade`: media gross → net with up to eight compound or additive discounts, surcharges, agency fee on `net`, `gross` or `gross_after_first_discount`, and fee discount (`% Bonificación`).
- `estimate_totals`: production sale, cost, agency service, supplier commission and invoice groups per currency; blocks direct lines with sale ≠ cost and commission on internal lines.
- `payment_terms`: due and expected date from the invoice date with `net_days`, `end_of_month_then_days` or `next_fortnight`, holidays and weekend roll.
- `allocate`: split-code percentages, advance-sale draw across advance invoices, partial amounts across items, with exact conservation.
- `invoice_check`: recompute VAT by rate and the total against the draft total with an explicit rounding tolerance.

```bash
python3 scripts/agency_tools.py discount_cascade < input.json
```
```json
{"currency": "MXN", "gross_minor": 10000000, "mode": "compound", "discounts_bps": [1000, 500], "surcharges": [], "fee_base": "net", "fee_bps": 1500, "fee_discount_bps": 0}
```
Not calculated by tools: VAT rates, perception and withholding regimes, FX rates, commission policy and media due-date types beyond the three rules. Take them from host tax tables, the rate source and the client master.

## Approvals and segregation of duties
- Billing clerk prepares; billing lead approves issuance. Where maker ≠ checker is enforced (configurable), the issuer is not the person who approved the source for billing.
- Issue, void, delete, NC cancelling an invoice, mark-as-billed and rounding adjustments require an authenticated human approval bound to the `payload_digest`, revision, client, currency and total. Unassociated NC/ND also follow the NC approval circuit when enabled.

## Exceptions to escalate
- Pending not approved for billing or schedule not ad-verified → planner or producer.
- Mixed currency, product or due date in one selection → split drafts; billing lead confirms grouping.
- Cost ≠ sale on an audit-practice client → account director.
- Zero-value consumption in CL/CO → tax lead confirms the internal point of sale.
- Advance-sale balance insufficient → billing lead; never a negative balance.
- Partial NC requested in Colombia, or NC on a collected invoice with the restriction on → controller.
- Deleted cancelling NC leaves an invoice without support → controller; mark the source billed with the original number to prevent double billing.
- Rounding above the cap or authority-recalculated VAT → tax lead.
- Missing VAT/perception table or currency fiscal identifier → tax lead.

## Return and handoff
Return `billing_selection`, `invoice_drafts`, `credit_debit_note_drafts`, `fee_calculation`, `split_allocation`, `billing_exceptions`. Include tenant, billing and owner client, JobNumber/OT, source document ids and revisions, point of sale and document type, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), tool outputs as evidence, blockers, approvals required and next stage.
**Owner:** Billing lead. **Next:** agency-tax-compliance, agency-collections, agency-accruals-revaluation, agency-profitability.

## Connectors and files
- `xero` and `quickbooks` for invoice drafts in a host ledger; `stripe` and `paypal` only where the agency bills through them; `mx-cfdi-pac` and `arca-afip` belong to the authorization stage. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` or `--kind plan ...` for pending-to-bill extracts.
