---
name: agency-delivery-reconciliation
description: "Matches supplier invoices to closed orders, production items or expense requests and classifies differences by origin. Use when an invoice must be checked. Never edits supplier figures."
---

# Reconcile Pending-to-Receive and Differences

This stage sits between commitment and payable. Media insertion orders (`Órdenes de Publicidad`), approved production estimates and purchase orders (`Órdenes de Compra`) and approved expense requests (`Solicitudes de Gastos`) create a pending-to-receive (`pendiente de recibir`) balance; this skill controls each incoming supplier document against that balance at the finest grain and records differences, and agency-payables then registers the document. It owns the control record (`Control de Medios`), the difference records (`Diferencias`) and write-off proposals. It never posts the invoice, never changes the order or plan, and never edits supplier values to make totals agree.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [supplier-invoicing.md](references/erp/supplier-invoicing.md) (section 2.1 load types, P-01 to P-17, P-30, P-31, lifecycles 4.1 and 4.3, R-01 to R-14, R-24, R-36, gaps 1–4) — [media-buying.md](references/erp/media-buying.md) (P-OP-07 close, P-OP-08 reopen, P-SV-03 to P-SV-05 verification, lifecycle 4.5, BR-O-08, BR-O-09, BR-V-01 to BR-V-06, BR-D-01 to BR-D-04).

## Use when
- A supplier invoice, credit note (`NC`) or debit note (`ND`) must be matched to media spots (`avisos`), production estimate items or expense request lines.
- Someone asks what is still pending to receive, "facturas a recibir", "diferencias pendientes" or for a three-way match by supplier or period.
- A media invoice bills a different quantity, size (columns × duration), rate or discount than the closed order.
- Differences must be closed by an NC/ND, accepted, or proposed for write-off (`marcar como no facturado por el proveedor`).
- The operational control must be saved separately from accounting registration (`Grabar Control` / `Recuperar Control`).

## Do not use when
- Issuing, modifying, closing or reopening insertion orders: use agency-media-buying.
- Importing monitoring files or certifying spots: use agency-transmission-control.
- Logging receipt, deduplicating, choosing the load type or registering the invoice: use agency-payables.
- Rebilling or crediting differences to the client: use agency-client-billing.
- Volume, overcommission or incentive calculations: use agency-rebates.
- Month-end accrual of uninvoiced cost: use agency-accruals-revaluation.

## Required inputs
- Blocking: tenant, supplier id, document type, number, document date, currency and declared total; the target pendings (order/month/item/spot, estimate/item, or request/line) with expected net amounts in minor units.
- Blocking for media: order status (closed or open) and spot certification evidence; ordered spots, size, rate and up to four discounts per spot.
- Blocking for production: client approval of the estimate, external supplier on the item and PO status when POs are mandatory (R-30, R-11).
- Agency tolerance policy for differences (the reference documents only a rounding threshold — confirm locally).
- Optional: monitoring results, prior saved control, client billing status, direct/indirect flag.
Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Resolve identity: tenant, supplier, billing client, JobNumber and order currency. Reject a document that mixes commitments of different currencies or a foreign-currency document over commitments in another foreign currency (R-13); a rate is needed only when the document or order currency is foreign (R-14).
2. List the supplier's pendings by category to see which automatic load types apply: media order, media differences, production estimate, production differences, expense request (R-01). If none exist, return `blocked` and route to agency-payables for a manual load with written justification.
3. For media, check each order's state. Only closed orders are eligible for supplier invoice registration (BR-O-08). Flag open orders: invoicing them closes the order on the supplier's word, and closing auto-certifies uncontrolled spots with the default audit code (P-OP-07, R-02). Recommend verification and close via agency-transmission-control and agency-media-buying first.
4. Where per-spot proof is needed, run `spot_match` on ordered windows vs aired events; treat `ordered_not_aired` and `ambiguous` as blockers for those spots and `aired_not_ordered` as a buyer question, not a billable line (BR-V-04).
5. Select pendings at the right grain: spots for media (P-01), items for production (P-14), request lines for expenses (P-18). Standard expense requests are not partially invoiceable; multi-invoice requests spawn a child request per invoice (R-10, P-19).
6. Recompute the billed value per line with the reference proposal `gross = spots × size × rate`, `net = gross × Π(1 − d_k)` for up to four discounts (R-05; cascade mode is configurable — confirm locally). Compare per line and in total with `reconcile` (ordered, certified delivered, invoiced, approved tolerance).
7. Record every override as a difference with its origin: quantity, size, rate, discount, reprogramming, adjustment or deficiency, with the expected sign (NC or ND) (P-02, entity `Diferencia`). When several variables change, state the attribution order used; quantity → size → rate → discount is the reference proposal (gap 3, confirm locally).
8. Production: billed below expected leaves the pending open (P-15); billed above expected opens a pending to receive an NC for the excess (P-16, R-09). Never absorb an excess silently.
9. Apply the sum-of-documents principle: suppliers may split invoices and NCs, and the check is that all documents together equal the order total; residuals stay as differences (R-04). Discounts may arrive per line, as one global line, or as separate NCs without changing expected net (R-06, P-03).
10. Extras billed after a clean registered invoice use origin `Diferencias` with amounts starting at zero (P-10, R-07); flag them for buyer confirmation before registration.
11. When the planner or buyer controls but accounting registers later, save the control only (P-04, P-08) and return `draft`; registration recovers it (P-05, P-09).
12. For pendings that will never be invoiced, prepare a write-off proposal per line with amount, reason, optional transfer to client and margin effect on the work order; it creates no GL entry but changes job margin (P-30, R-36). Difference write-offs have a direct P&L effect and are reversible (`Desmarcar`) (P-31). Both need approval.
13. Compute `payload_digest` over the control and any write-off proposal, attach evidence references and hand off.

## Rules and locks
- Only closed orders are matched for registration; a registered invoice locks the order against reopening, and reopening needs the invoice cancelled and the month's schedules open (BR-O-08, BR-O-09).
- A spot control cannot be removed on a closed order (BR-V-05).
- An order is authority, not proof of delivery; certification evidence or close is required for media payables.
- `Versión Final` locks the order and plan; an initial load keeps them editable until a closing document or mark-as-invoiced (R-08).
- Production pendings need external supplier + client approval + PO when mandatory/approved (R-30, R-11) (configurable).
- One currency family per document (R-13).
- Differences stay open until closed by NC/ND, written off or transferred to the client; never net them away inside the control.
- Write-offs and difference write-offs need an authenticated human approval and an audit stamp (user, date, reason) (R-36).
- Matching tolerances beyond the rounding threshold are agency policy, not reference behaviour (gap 1) (confirm locally).
- Keep supplier-declared values and computed values side by side; never overwrite originals.

## Calculations
- `reconcile`: per line or per order with `ordered_minor`, `delivered_minor` (certified), `invoiced_minor`, `tolerance_minor`; `hold` reasons become differences; `payable_candidate_minor` is the lowest of the three and is a candidate only.
- `invoice_check`: recompute VAT by rate and the declared total before handing the document on; `mismatch` blocks, `rounding_adjustment` is allowed only within the configured threshold (R-03, R-12).
- `spot_match`: ordered windows vs aired events with `tolerance_minutes` and `match_material`; returns exact, tolerance, ambiguous, ordered-not-aired and aired-not-ordered sets.

```bash
python3 scripts/agency_tools.py reconcile < input.json
```
```json
{"currency": "MXN", "ordered_minor": 4500000, "delivered_minor": 4320000, "invoiced_minor": 4500000, "tolerance_minor": 5000}
```
The result is `hold` with `invoice_delivery_mismatch` and `short_delivery`: record a deficiency difference of 180000 and expect an NC.

Not calculated by tools: VAT rates per VAT account, perceptions, withholdings, FX rates, discount cascade policy, difference attribution order and tolerance policy. These come from the tax setup, an authoritative rate source and agency policy.

## Approvals and segregation of duties
- The media/finance analyst prepares controls and differences; the buyer or planner confirms delivery facts; the controller approves write-offs, client transfers and any difference above tolerance.
- Write-offs, difference write-offs, transfer-to-client percentages and acceptance of a production excess need an authenticated approval bound to the `payload_digest`, revision, currency and total. The preparer cannot approve their own proposal.

## Exceptions to escalate
- Invoice against an open order → buyer; verify and close in agency-media-buying before registration.
- Ordered-not-aired or deficient spots billed → buyer for makegood or NC request.
- Aired-not-ordered spot billed → buyer; possible bonus spot or vendor error.
- Production invoice above budget → producer and controller; NC pending opened.
- Supplier has no pending (manual origin) → AP lead in agency-payables with justification.
- Mixed currencies in one document → AP lead; split or return the document.
- Commission credit computed on ordered amounts above actual investment → agency-rebates.
- Old pendings that will never be billed → controller for write-off approval.
- Difference line without VAT (appears exempt in the VAT book, R-24) → tax lead in agency-tax-compliance.

## Return and handoff
Return `match_result`, `discrepancies`, `evidence_links`, `payable_candidate`, `writeoff_proposals`. Include tenant/client/job IDs, JobNumber, supplier, document ids and revision, order/estimate/request line ids, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Media/finance analyst. **Next:** agency-payables, agency-client-billing, agency-accruals-revaluation.

## Connectors and files
- Platform delivery evidence: `google-ads`, `meta-ads`, `amazon-ads`, `supermetrics`; OOH proof of play: `broadsign`; finance systems as read-only sources: `xero`, `quickbooks`. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
