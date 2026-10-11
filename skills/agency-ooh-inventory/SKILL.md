---
name: agency-ooh-inventory
description: "Run seller-side billboard inventory for a media owner: faces and states, availability, reservations converted to orders with monthly sub-orders, face and motif assignment, posting batches, and advertiser agreements with prepaid balance. Use when selling or posting OOH faces you own. Do not use for an agency buying OOH from vendors."
---

# OOH Inventory (Media-Owner Vertical)

This optional vertical serves agencies or groups that own billboard faces (`carteles`): face master and states → **availability → reservation (`reserva`) → order (`orden VP`) with per-month sub-orders → face and motif assignment → posting batch (`fijación`)** → monthly invoicing, credit notes and agreement balances. It owns the face inventory, reservations, OOH orders, posting batches and advertiser agreements (`convenios`). It never issues invoices or credit notes, and it is not the agency buy-side OOH plan.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-masters-ooh.md](references/erp/media-masters-ooh.md) (§1 framing fact 2, P40–P50, §3.2 OOH entities, §4.1–4.6 lifecycles, rules 44–61, §6 OOH accounting, §9 OOH reports, §10.1–10.3, §11 gaps 1–8, 20).

## Use when
- "Which faces are free in zone X for November?", `disponibilidad`, `ocupación`, distressed inventory.
- Creating a reservation for a salesperson or converting it to an order when the advertiser PO arrives (`generar orden`).
- Pricing an OOH order line (normal or package tariff, outings, faces, 4 discounts, 4 credit-note discounts) and slicing it per calendar month.
- Assigning faces and motifs (`motivos`) with share %, building, closing or reopening a posting batch (`orden de fijación`).
- Maintaining face states (OK, needs maintenance, out of circuit, repaired) or an advertiser agreement with prepaid or capped balance.

## Do not use when
- The agency is buying OOH space from vendors for a client plan → `agency-ooh-planning`, then `agency-media-buying`.
- Creating billboard types, formats, circuits, states or motifs masters → `agency-master-data`.
- Issuing the monthly invoice, credit notes or advance-sale invoice → `agency-client-billing`; collections → `agency-collections`.
- Salesperson commission or profitability analysis → `agency-profitability`.
- Rate card design for buy-side media → `agency-rate-cards-contracts`.

## Required inputs
- **Blocking:** tenant_id, JobNumber (it supplies holder, advertiser, product, billing client and campaign, P41); billboard type and zone (one each per document, rule 44); salesperson.
- **Blocking for orders:** OOH rate card and rate item (rule 45), tariff type N or P, faces, start date, outings, rate in minor units, currency and exponent, FX rate for foreign currency (rule 57), payment terms, client PO number.
- **Blocking for posting:** posting date, billboard type, zone, orders with faces and motifs assigned.
- **Blocking for agreements:** level, validity, type M (amount cap) or C (consumption), payment N/A/C, currency, billable and bonus amounts, linked rate card.
- Face states and permit validity from the master; opening code only if the JobNumber billing code is `*` (rule 58).
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Availability: filter faces by type, format, zone, street and dates; a face is assignable only if its state kind is OK, needs-maintenance or repaired, it is free on the dates, and its permit is valid (rule 54, §4.1). For bulk-quantity types (e.g., CPM circuits) decrement available quantity per circuit instead of faces (rule 50).
2. Reservation: from the JobNumber create one reservation per billboard type × zone with salesperson and rate item; status `pending face assignment` → `pending order` once faces are blocked (P41, §4.2).
3. Price lines: normal tariff gross = outings × rate × faces, computed with `media_line_cost` (`per_unit`, measure = outings, spots = faces); package tariff = entered rate (`package`) (rules 46–47). CPM outing semantics (3 days vs one week for 2 outings) are unclear (rule 48, §11 gap 3) (confirm locally).
4. Discounts: cumulative discounts 1–4 with `discount_cascade` (`mode` compound by default); compute each credit-note discount separately as gross × cᵢ, because each becomes its own credit note (rule 49). Whether the credit-note base is gross or post-discount net is unknown (§11 gap 2) (confirm locally).
5. Agreement check: link only active, in-validity, same-currency agreements; type M blocks linking once the billable amount is consumed; type C has no cap (rule 59). Compute remaining balance from linked orders and report any gap against advance-sale invoices (§4.6).
6. Order: convert the reservation ("generate order") or create directly, with client PO number, payment terms (default from billing client), currency/FX, optional supplier commission (invoice vs credit note), agreement and lines (P42). Rate card is mandatory (rule 45).
7. Monthly sub-orders: slice the order per calendar month (rule 52) with `allocate`, using weights that follow the agency's proration rule (days, outings or start month — undocumented, §11 gap 4). Multi-order billboard types may straddle month end (rule 51).
8. Face assignment: by a profile-restricted responsible user; release options block occupied, release reserved, release free-of-charge, release all (P43). Disabling the restriction to faces linked to the rate item needs access level 1 (rule 55).
9. Motifs: assign one or more motifs with share % summing to 100% of faces; motifs are mandatory before posting (P44, rule 53).
10. Posting batch: Build (one batch per billboard type, zone, posting date; carried-over faces flagged) → Control close by the commercial lead (adjust faces to post, grant free extra faces) → issue the posting sheet (remove image X, put motif Y) (P46, §4.3). A closed batch accepts no edits until the responsible role reopens it (rule 60).
11. Face state changes: record state, timestamp and note for the audit; out-of-circuit faces are unassignable and future assignments must be flagged (P47, §4.1).
12. Prepaid agreement (payment A): prepare the advance invoicing schedule with `installment_schedule` and hand it to billing; consumption is then tracked against it (§4.6).
13. Reject, copy, delete: rejection frees faces; copy creates a repeat order on new dates; delete only if not invoiced and no motifs assigned (P49).
14. Hash every reservation, order, assignment, posting close and agreement proposal with `payload_digest`; status `completed` only when the system of record confirms it.

## Rules and locks
- One billboard type × one zone per reservation or order (rule 44).
- Rate card mandatory to order; rate item ≠ face assignment (rule 45).
- Out-of-circuit faces cannot be assigned; expired permits should not be sold (rule 54, §4.1) (confirm locally for permits).
- Motif shares sum to 100%; motif required before posting (rule 53, P44).
- Closed posting batch is locked; only the responsible role reopens (rule 60).
- Face-restriction override requires access level 1 (rule 55) (configurable).
- Split billing by opening code only when the JobNumber billing client code is `*` (rule 58).
- Agreements: single currency, type M capped, inactive or expired not linkable (rule 59).
- Order delete only if not invoiced and without motifs; prefer reject to free faces (P49).
- Proof-of-posting photos, removal orders and maintenance work orders do not exist in the reference (§11 gap 6); treat them as agency policy additions.
- OOH taxes, municipal fees, printing and installation costs are not modelled (§11 gap 5) (confirm locally).

## Calculations
- `media_line_cost`: normal tariff (`per_unit`: rate × outings × faces) or `package`.
- `discount_cascade`: cumulative discounts 1–4 on the order line; run once per credit-note discount to obtain each credit-note amount.
- `allocate`: monthly sub-order amounts by integer weights with exact conservation.
- `installment_schedule`: advance and installments for a prepaid agreement.

```sh
python3 scripts/agency_tools.py allocate < input.json
```
```json
{"currency": "MXN", "amount_minor": 36000000, "weights": [{"target_id": "2026-11", "weight": 12}, {"target_id": "2026-12", "weight": 31}, {"target_id": "2027-01", "weight": 17}]}
```
Expected (weights = days per month, an agency proration choice): 7200000, 18600000, 10200000; total 36000000.

Not calculated by tools: VAT and municipal taxes, FX rates, salesperson commission (undocumented, §11 gap 7), occupancy KPIs, permit validity. These come from authoritative masters or agency policy.

## Approvals and segregation of duties
- Salespeople prepare reservations and orders; the responsible planner assigns faces; the commercial lead closes and reopens posting batches; finance approves agreements with prepaid or barter payment.
- Orders, agreement creation, free extra faces, face-restriction overrides and posting close require authenticated human approval bound to the `payload_digest` of the exact payload.
- The salesperson cannot approve their own order discounts or free faces; any change in price, faces or dates invalidates the approval.

## Exceptions to escalate
- Requested faces occupied, out of circuit or with expired permit → OOH sales manager; offer alternatives.
- Stale reservations blocking inventory → salesperson and sales manager; propose rejection.
- Orders without motif close to posting date → traffic and salesperson.
- Agreement cap reached or agreement vs advance-sale balance mismatch → finance.
- Foreign-currency order without FX rate → finance.
- Posting changes after close → commercial lead (reopen decision).
- Face state degraded on an assigned face → operations; reassign with client notice.
- Unknown proration or CPM outing rule → OOH sales manager to set policy before billing.

## Return and handoff
Return `availability_report`, `reservations`, `ooh_orders`, `monthly_suborders`, `face_motif_assignments`, `posting_batches`, `agreement_balances`, `inventory_exceptions`. Include tenant/client/job IDs, JobNumber, reservation and order numbers, revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** OOH sales manager (media-owner vertical). **Next:** `agency-client-billing` (monthly sub-orders, credit notes, advance invoices), `agency-collections`, `agency-profitability`.

## Connectors and files
- Provider ids from `integrations/registry.json`: `broadsign` for digital faces and proof-of-play; `composio` or `zapier` for reviewed inventory-system actions; `canva` or `figma` for motif artwork references. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind ooh ...` for face, order and posting exports; `--kind invoice` to reconcile invoiced monthly slices.
