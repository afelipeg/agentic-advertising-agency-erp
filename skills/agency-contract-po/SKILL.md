---
name: agency-contract-po
description: "Turns signed client agreements and client POs into PO limits, document links, transfers and budget reserves. Use when a client PO must govern spend. Unsigned quotes are not authority."
---

# Client Agreements and POs

This stage sits between the JobNumber and the documents that consume client money: signed agreement and client PO (`PO Clientes`) or budget reserve (`Reserva Presupuestal`) → **PO/reserve rules** → production estimates and media plans checked at client approval → orders consume the PO → billing. It owns the normalized commercial terms, the PO record and its consumption and transfer ledger, and the reserve record. It never signs, sends or amends binding documents, and it never moves PO balance without a recorded source document.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-17 client POs and transfers, P-18 budget reserve, entities 3.8–3.9, rules 59–62, jobs J8–J9) and [receivables.md](references/erp/receivables.md) (rule 13 rounding to a client's round PO, rule 26 split codes, final PO number on the sales document, section 10.3 approved-for-billing precondition).

## Use when
- A client sends a purchase order or signed agreement: "cargar PO del cliente", "orden de compra del cliente", "contrato firmado", "`Nº Pedido cliente`".
- Linking an estimate or media plan (`pauta`) to a client PO, or checking whether a document may be linked.
- Transferring balance between two POs (`Traspaso entre PO`) or reviewing PO consumption (`Consumo PO Clientes`).
- Setting up or applying a budget reserve with pool areas (`áreas de bolsa`).
- Extracting fees, cancellation windows, rebate ownership and billing route from an agreement.

## Do not use when
- Checking available balance or credit limit before client approval → `agency-budget-control`.
- Building fixed or hourly fee contracts and their instalments → `agency-fee-contracts`.
- Opening or re-billing the JobNumber the PO will cover → `agency-job-lifecycle`.
- Creating billing clients, split codes or rate-card modes → `agency-master-data`; supplier rate contracts → `agency-rate-cards-contracts`.
- Invoicing against the PO → `agency-client-billing`; supplier rebate contracts → `agency-rebates`.

## Required inputs
- Blocking: `tenant_id`, titular client, billing client (`Cliente de Facturación`), signed PO or agreement with signer evidence, amount excluding tax, currency, validity dates.
- Blocking for linking: the document type (production estimate or pauta), number, creation date and amount; the PO creation date.
- Blocking for transfers: origin document number, origin PO, destination PO, amount and reason.
- Optional: contract number, product and media-type breakdown, online/offline scope, balance-control flag, amendments.
- For reserves: reserve number and year, control type (percentage, amount, none), validity, amount per pool area, designated pool-area approvers.
- Confirm the client is flagged for PO control and that the agency configuration manages client POs (P-17 prerequisite).

## Procedure
1. Verify authority: match signer, revision and legal entity against trusted records. Block unsigned quotes, contradictory amendments, expired POs and increases without a signed amendment.
2. Extract terms with citations: PO amount net of tax, currency, validity, deliverables, billing route, fees, markups, payment milestones, tax basis, cancellation windows, minimums, makegoods and rebate/discount ownership. Do not assume all spend is cancellable or that rebates belong to the agency.
3. Check that the billing client belongs to a titular client with PO control enabled; record the PO amount excluding tax (rule 59).
4. Propose the PO record: billing client, description, amount ex-tax, currency, validity, optional contract number, balance control on (recommended), optional product/media-type breakdown, online/offline scope (P-17). Breakdown enforcement is (confirm locally).
5. When a payment schedule is agreed, use `installment_schedule` to split the gross into an advance plus monthly amounts that sum exactly; treat it as the expected billing calendar, not an invoice.
6. For each document to link, compare its creation date with the PO creation date: only documents created after the PO may be linked (rule 59). Once linked, the header PO assignment is locked against manual edit (rule 60).
7. Check consumption with `budget_check` using disjoint balances: authorized = PO amount, spent = invoiced, open commitments = issued orders, reservations = client-approved documents not yet ordered. The reference validates at client approval and records consumption when purchase or insertion orders are issued (rule 60).
8. For a transfer, require both POs to belong to the same billing client, name the source document and show the origin balance; never let the origin go negative (rule 61, P-17a). Prepare it as an adjustment proposal with its `payload_digest`.
9. For a budget reserve, record control type (percentage capped at 100%, amount, or none), validity and pool-area amounts; the job responsible assigns it on the JobNumber and estimates and plans inherit it (P-18).
10. At invoicing, the expense rendering shows reserve consumption and the user picks the reserve to decrement; the balance falls as consumption invoices are issued (rule 62). Report which reserve a proposed invoice will decrement.
11. Separate client authorization from supplier commitments and platform budgets; define caps by job, channel and period only where the agreement requires them.
12. Return normalized terms, PO and reserve proposals, link decisions and exceptions; stop at `pending_approval` for any record creation, link or transfer.

## Rules and locks
- PO amounts are net of tax; compare document amounts on the same basis and currency (rule 59).
- POs apply prospectively only; a document dated before the PO cannot be linked (rule 59).
- The PO assignment in a document header is locked once set (rule 60).
- Transfers only between POs of the same billing client, always naming the source document (rule 61).
- Reserve percentage control is capped at 100%; first-level approval of a reserve-funded estimate or pauta is given by the pool-area approver (rule 62).
- The budget reserve was built for a specific client; its use elsewhere is (configurable).
- An unsigned quote, email intent or verbal commitment is never spending authority.
- Rounding to match a client's round PO is limited by the supervisor-set maximum and not allowed where the tax authority recalculates VAT (receivables rule 13).
- A split code needs percentages summing to 100 and at least two billing clients of the same titular client (receivables rule 26).
- Expired or exhausted POs block new links; extensions need a signed amendment (agency policy).

## Calculations
- `budget_check`: PO or reserve availability from disjoint balances (`authorized_minor`, `spent_minor`, `open_commitments_minor`, `reservations_minor`, `requested_minor`); read `available_minor`, `after_request_minor`, `within_budget` and `atomic_reservation_required`.
- `installment_schedule`: split an agreed contract amount into `advance_bps` plus `installments` monthly amounts from `start_month` that sum exactly to `gross_minor`.

```bash
python3 scripts/agency_tools.py budget_check < input.json
```
```json
{"currency": "MXN", "authorized_minor": 50000000, "spent_minor": 12000000, "open_commitments_minor": 18000000, "reservations_minor": 5000000, "requested_minor": 9000000}
```
Expected: `available_minor` 15000000, `after_request_minor` 6000000, `within_budget` true, `atomic_reservation_required` true.

- Not calculated by tools: tax to strip from a gross PO, FX between PO and document currency, signer validity, and the reserve percentage base. These come from the signed document, the tax adviser and the host FX source.

## Approvals and segregation of duties
- The account director prepares PO records, links and transfers; finance verifies the signed evidence and approves PO creation, increases and transfers. Each approval is bound to the `payload_digest`, revision, currency and amount.
- The pool-area approver gives first-level approval of reserve-funded documents; the preparer of the document cannot approve it.
- Legal or finance resolves ambiguous terms; the agent never signs or sends a PO acknowledgement.

## Exceptions to escalate
- Document predates the PO → account director: request a new PO or amendment.
- Insufficient PO balance → `agency-budget-control` and the client for an increase or a transfer.
- Transfer between POs of different billing clients or without a source document → refuse.
- Expired PO with pending documents → account director and client.
- Contradictory amendments or unsigned increase → legal and finance.
- Reserve cap exceeded or pool area without approver → finance controller.
- PO currency differs from document currency → finance for FX policy.
- Agreement silent on rebate ownership or cancellation → account director before planning.

## Return and handoff
Return `commercial_terms`, `po_limits`, `po_link_decisions`, `po_transfer_proposal`, `reserve_setup`, `billing_route`, `scope_exceptions`. Include tenant, titular and billing client, job ids and JobNumber, PO code, document ids and revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Account director and finance. **Next:** `agency-budget-control`, `agency-fee-contracts`, `agency-media-planning`, `agency-production-estimating`.

## Connectors and files
- Provider ids: `hubspot` or `notion` for agreement records, `xero` or `quickbooks` for billing-client references, `composio` or `zapier` only for host-approved document intake. Host marketplace documents/email may hold the signed PO. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating when the documents to link arrive as exported plans or invoices.
