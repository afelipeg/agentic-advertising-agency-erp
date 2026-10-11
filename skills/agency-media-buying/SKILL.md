---
name: agency-media-buying
description: "Prepares insertion orders from client-approved schedules with credit gates, versioning (cancels and replaces), sending and close/reopen rules. Use when spots must be ordered or changed."
---

# Media Buying: Insertion Orders

This stage turns client-approved schedule (`pauta`) spots into insertion orders (`Órdenes de Publicidad`, OP) to outlets and vendors: planning → **orders → send → modify/version → close** → transmission control, supplier invoice registration and client billing. It owns the order document, its versions and its open/closed state. It never registers supplier invoices, bills the client or sends anything to a vendor without an authenticated approval and a trusted connector receipt.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-buying.md](references/erp/media-buying.md) (§2.3 P-OP-01..12, §4.3–4.5 lifecycles, BR-O-01..13, BR-T-12, BR-D-01..05, §10.3–10.4 controls and exceptions, §11 gaps 9, 14, 19).

## Use when
- "Order the approved schedule", "generate the OP", `ordenar pauta`, `orden manual`, `orden automática`.
- Changing an issued order: rate, discounts, notes, vendor (`modificar proveedor`), with or without a new version (`Mod. Rev.`, `anula y reemplaza`).
- Preparing the send pack (PDF, email draft, vendor interface export) or a cancellation request (`pedido de anulación`).
- Closing orders after verification (`cerrar órdenes`) or reopening one (`abrir orden`).
- Publisher-side order entry where the order is both sale and placement (`Editora` variant).

## Do not use when
- The plan, spots or client approval are still being built → `agency-media-planning`, `agency-tv-radio-planning`, `agency-digital-planning`, `agency-ooh-planning`.
- Rates or contract terms are wrong at the source → `agency-rate-cards-contracts`.
- Structural changes (program, duration, spot count, publication type, billing condition) → `agency-plan-changes` (they are edited on the plan, BR-O-04).
- Verifying airings, makegoods or spot control → `agency-transmission-control`.
- Digital platform campaign setup → `agency-campaign-activation`.
- Registering the vendor invoice → `agency-payables`; client invoicing → `agency-client-billing`; seller-side OOH orders → `agency-ooh-inventory`.

## Required inputs
- **Blocking:** tenant_id, client_id, JobNumber, plan number, schedule (month/year/number) and its approved revision; client approval record when the approval circuit is on (BR-O-02).
- **Blocking:** credit limit, open AR and approved-unbilled amounts for the billing client when credit control is on, or the credit override approval (BR-O-02).
- **Blocking:** outlet and vendor per line with the vendor linked to the outlet in masters; rate card or manual buy price; currency and exponent; VAT attributes.
- Split criterion, date cut-off, footer-note model, vendor payment condition, purchase-order numbers (media investment and agency commission).
- For modifications: order number, current version, sent/unsent status, reason category and reason, supplier-invoice status, month schedule close status.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Load the schedule and verify the plan is client-approved at the stated revision; if any approval or credit override is missing, stop `blocked` (BR-O-02, P-OP-01).
2. Credit gate: run `credit_exposure` with credit limit, open AR, approved unbilled and the order amount. `requires_override_approval: true` → block and request the override from the credit approver (BR-O-02: order amount + AR ≤ limit).
3. Diff the approved schedule revision against the lines to order with `plan_diff`; any blocker or unapproved change returns to planning, not to the order.
4. Choose split keys: medium, provider, publication type (+ medium/provider), material, contract, VAT rate, item, day/date range, spot (BR-O-03). One order = one medium + one vendor (BR-O-01); a multi-medium schedule yields several orders. Manual mode orders one medium at a time with grouping per item, per spot, per date (max date), all-in-one or day-picking (P-OP-01).
5. Buy pricing: automatic mode takes the buy price from the rate card; with no card buy = sell (BR-T-12). Recompute gross with `media_line_cost` and net with `discount_cascade` (up to 4 order-only discounts). Schedule-vs-order rate differences need explicit validation (media-planning R27).
6. Override checks: order rate and discount edits only on indirect items and only for clients without in-system audits (BR-O-05); direct items keep cost = sale (media-planning R10).
7. Draft each order: number (assigned by the system), version 1, vendor, payment condition (defaults from provider master, overridable, BR-O-11), PO numbers for investment and commission, footer notes, items (item numbers never reused, BR-O-07), spot calendar. Spot state moves `pautado` → `ordenado` only when the system confirms the save.
8. Send pack: render with values / commission breakdown / conduit / direct variant as configured, plus special-conditions text; prepare an email draft or interface export (P-OP-04, P-IE-01). Bind the pack with `payload_digest`; sending requires authenticated approval and a reviewed connector. Record Issued vs Sent from the system, never from assumption.
9. Modify: route cost, discounts, taxes, notes and vendor to the order; route structural attributes to the plan (BR-O-04). If the order was sent, create version n+1 with an optional "cancels and replaces" legend and a reason; if unsent, re-issue the same number and version (BR-O-06, P-OP-05). Reusing an order number triggers a version warning and a notify-vendor decision (P-OP-03).
10. Vendor change: confirm the new vendor is associated with the medium (BR-O-10); prepare the revision-by-modification record and a vendor notification draft.
11. Delete only to release spots for plan edits; never once approved by client or for billing in the publisher variant (P-OP-06). Prefer cancellation with rejection of spots to keep history.
12. Close: before proposing close, list spots still uncontrolled and warn that close auto-certifies them as aired with the default audit code (BR-O-08, §10.3). Recommend running `agency-transmission-control` first. Close is required before supplier invoice registration.
13. Reopen: allowed only if no supplier invoice is attached and the month's schedules are not closed (BR-O-09, P-OP-08); otherwise return blocked naming the invoice to cancel or the period owner.
14. Return order drafts, the approval package and handoffs; mark `completed` only for orders the system of record confirms with number, version and status.

## Rules and locks
- No order without client approval of the plan/schedule (configurable) and within credit limit or with excess approved (BR-O-02).
- One medium and one vendor per order (BR-O-01).
- Structural attributes are edited on the plan only and replicated to the order (BR-O-04).
- Order rate/discount edits only on indirect items for clients without in-system audits (BR-O-05).
- Sent orders change only by new version; unsent orders may be re-issued without a bump (BR-O-06).
- Item numbers are never reused (BR-O-07).
- Close freezes the order and auto-certifies uncontrolled spots; irreversible once a supplier invoice exists (BR-O-08). Close mandatory before accounting (configurable, recommended).
- Reopen requires no supplier invoice and open month schedules (BR-O-09).
- Vendor change requires a medium↔vendor link (BR-O-10).
- Client billing gates `Aprobada para Facturar` and manual state (`Usa Gestión Manual de Estados`) are checked downstream (BR-O-13) (configurable).
- Publisher variant: every save creates a revision when `Modifica Revisión` is on; delete blocked once client- or bill-approved (P-OP-10) (configurable).
- Date-criterion labels in order lists look swapped in the reference (§11 gap 9) (confirm locally).

## Calculations
- `media_line_cost`: gross per line by calc type (`per_second`, `per_unit`, `per_thousand`, `per_action`, `package`).
- `discount_cascade`: buy net after up to 4 order discounts (`mode` compound unless agency policy says additive), surcharges, and fee base when the order print shows a commission breakdown.
- `credit_exposure`: credit gate before ordering; `requires_override_approval` drives the block.
- `plan_diff`: approved schedule vs proposed order lines; blockers on committed lines.

```sh
python3 scripts/agency_tools.py credit_exposure < input.json
```
```json
{"currency": "MXN", "credit_limit_minor": 500000000, "ar_open_minor": 310000000, "approved_unbilled_minor": 95000000, "requested_minor": 120000000}
```
Expected: exposure 525000000, headroom -25000000, `requires_override_approval: true`.

Not calculated by tools: VAT and tax attributes, FX rates, CPP rates from ratings, credit-note discounts as separate documents, approval validity. Take them from authoritative masters and the host approval store.

## Approvals and segregation of duties
- The media buyer prepares orders and versions; client approval and the credit override come from users holding those permissions; sending to the vendor needs an authenticated approval bound to the `payload_digest` of the exact send pack (order ids, versions, totals, recipient).
- Close and reopen are control actions: the buyer proposes, the buying lead or controller confirms per agency policy; reopen after accounting interest needs finance sign-off.
- Any change in price, currency, vendor or recipient invalidates prior approval. The preparer cannot approve their own order.

## Exceptions to escalate
- Plan not client-approved or approved revision mismatch → planner / account director.
- Credit limit exceeded → credit approver (finance).
- No valid rate card or schedule-vs-order rate difference → buying director and `agency-rate-cards-contracts`.
- Contract cap or share breach on the ordered amount → buying director.
- Vendor not linked to the medium → `agency-master-data`.
- Close requested with uncontrolled spots → traffic via `agency-transmission-control`.
- Reopen blocked by a supplier invoice or closed month → `agency-payables` or `agency-period-close`.
- Send outcome unknown (timeout, no receipt) → mark uncertain; query by order number or electronic order ID before resending.
- Rate edit requested on an audited client or direct item → buying director; do not override.

## Return and handoff
Return `order_drafts`, `order_versions`, `send_packs`, `close_reopen_proposals`, `commitment_updates`, `supplier_exceptions`. Include tenant/client/job IDs, JobNumber, plan, schedule, order month/number/version, vendor, revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Media buyer. **Next:** `agency-transmission-control`, `agency-campaign-activation` (digital lines), `agency-payables` (closed orders), `agency-client-billing`.

## Connectors and files
- Provider ids from `integrations/registry.json`: `composio` or `zapier` for reviewed ERP/order-system actions (approve the inner tool and arguments); `broadsign` for DOOH bookings; host marketplace email/documents for send packs. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind broadcast-order ...` for exported orders and `--kind plan` for approved schedules.
