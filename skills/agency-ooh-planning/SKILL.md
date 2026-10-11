---
name: agency-ooh-planning
description: "Plans agency-side out-of-home, DOOH and print: circuits x rate, faces, press size, month splits and evidence to request. Use for OOH and press lines. Booked faces are not exposure."
---

# OOH Planning

This stage prices and specifies the out-of-home (`Vía Pública`), digital out-of-home and print (`Prensa`) items of a media plan from the agency side: brief and no-book ranking → plan items → client approval → orders → installation or publication evidence → reconciliation. It owns the site/circuit plan, the cost schedule per month and the evidence requirements. It never operates a media owner's face inventory, books suppliers or accepts evidence as an invoice.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-masters-ooh.md](references/erp/media-masters-ooh.md) (§1 seller-side framing, OOH rules 44–57, surcharges rule 24, VAT condition 39, §11 gaps 1–6; cited below as MM rule n). [media-planning.md](references/erp/media-planning.md) (P04 ranking without book, P05 body, P06 press and OOH variants, R4, R5, R6, R7, R9, R17, gaps 2 and 4).

## Use when
- Adding OOH items to a plan: days (`Días`), boards (`Ctls.`), circuits (`Ctos.`) and rate per circuit (P06).
- Adding press items with cm (`Cmts.`) × columns (`Cols.`), position or colour surcharges (`Recargos`) (P06, R7).
- Splitting a package (`Tarifa Paquete`) across the months of a multi-month flight (R5).
- Defining DOOH loop/slot and share-of-voice lines and proof-of-play requirements.
- Defining installation, removal, permit and tear-sheet evidence per supplier before ordering.

## Do not use when
- Operating billboard faces, reservations, posting batches or advertiser agreements as a media owner → `agency-ooh-inventory`.
- Plan header, fee, client approval and billing release → `agency-media-planning`.
- Digital platform plans → `agency-digital-planning`; TV/radio → `agency-tv-radio-planning`.
- Issuing or sending orders → `agency-media-buying`; matching evidence and invoices → `agency-delivery-reconciliation`.
- Printing and installation production estimates → `agency-production-estimating`.
- Revising an approved or ordered OOH line → `agency-plan-changes`.

## Required inputs
- Blocking: open JobNumber and plan header (media type OOH or press); validity and months.
- Blocking: supplier quote or rate card per circuit, face or press unit with validity, currency, gross/net basis and tariff type Normal or Package.
- Site data: circuit or face IDs, zone, format, orientation, address or geo reference, booked period; for DOOH screen/player IDs, slot length, loop length and share of voice.
- Press data: publication, issue/date, section/page, dimensions in cm × columns, surcharges defined in masters.
- Production, installation, lighting, permit and dismantling costs as separate quoted lines where they exist.
- Evidence policy agreed with the client: photo, proof-of-play, tear sheet, removal confirmation.

## Procedure
1. Confirm agency-side scope; if the agency itself owns faces, route to `agency-ooh-inventory` (MM §1). Build the candidate list from a ranking without book by site or zone, keeping placements by location and vendor (P04).
2. For each OOH item record outlet, vendor, publication type, circuits, boards and exposure days; days cannot exceed plan days and the day grid marks an X regardless of the number typed (P06).
3. Price Normal OOH items as circuits × rate per circuit; boards and exposure days do not change the price in the reference plan (R4). Use `media_line_cost` with `per_unit`, `measure` = circuits, `spots` = 1. If the supplier quotes per face and outing, record its basis (outings × rate × faces, MM rule 46) and price with `per_unit`, `measure` = faces, `spots` = outings, stating the deviation.
4. Price press items as cm × columns × spots × rate per cm-column (R4, gap 4): `per_unit` with `measure` = cm × columns. Apply predefined surcharges with value, accumulated and percent flags (R7, MM rule 24).
5. Price DOOH by the supplier's documented basis: slot/loop package (`package`) or CPM (`per_thousand`) only when the supplier documents its audience method; plays are never converted to impressions by assumption (agency policy).
6. Package items: the entered amount is the item total (R5). Split across months equally by default, or proportionally to purchased days when configured: run `allocate` with weights = purchased days per month so the split conserves the total exactly (R5) (configurable).
7. Apply up to the contracted discounts and the agency fee with `discount_cascade` (R6). Supplier credit-note discounts (MM rule 49) are tracked as a separate line, not netted into invoice discounts; their base is unclear (MM gap 2) (confirm locally).
8. Set billing type (Billable, Bonus with billable 0, Barter) and direct vs indirect per item (R9). Add production, installation, lighting, permit and dismantling costs as separate items or estimates; the reference does not model them on OOH orders (MM gap 5).
9. Validate each line's tariff and contract for every month of the flight; flag uncovered months rather than extending an expired rate (R17). Foreign-currency lines need an approved FX reference (MM rule 57).
10. Define evidence requirements per supplier and line: dated installation photos with geo reference, removal confirmation, permit validity, DOOH proof-of-play logs, press tear sheets. The reference ERP has no proof-of-posting entity (MM gap 6), so these are agency policy.
11. Return the site plan and cost schedule as `draft` for inclusion in the plan's client approval; ordering waits for that approval in `agency-media-planning`.

## Rules and locks
- OOH Normal gross = circuits × rate; boards and days do not affect price (R4).
- Package rate = item total; multi-month split equal by default or by purchased days (R5) (configurable).
- Press gross = cm × columns × spots × rate (R4); the guide's day multiplier is ambiguous (gap 4) (confirm locally).
- Surcharges must be predefined masters with value, accumulated and percent flags (R7).
- One publication type per item; rate or negotiation change mid-flight needs a new item (R17).
- A rate card or quote is mandatory before an OOH line can be ordered (MM rule 45).
- CPM outings calendar (3 days vs week blocks) is unclear (MM gap 3) (confirm locally).
- Monthly slicing proration is unspecified in the reference (MM gap 4); state the chosen rule.
- A dated photo proves a point in time, not the whole exposure period or audience (agency policy).
- Ordered, installed or billed lines are not edited here; changes go to `agency-plan-changes`.

## Calculations
- `media_line_cost`: `per_unit` (circuits, faces × outings, or cm × columns), `per_thousand` for documented DOOH CPM, `package` for package totals.
- `discount_cascade`: cascaded or additive discounts, surcharges (percent or amount, accumulative) and agency fee.
- `allocate`: split a package or monthly cost across months by purchased-day weights with exact conservation.

```bash
python3 scripts/agency_tools.py allocate < input.json
```
```json
{"currency": "MXN", "amount_minor": 9000000,
 "weights": [{"target_id": "2026-11", "weight": 16}, {"target_id": "2026-12", "weight": 31},
             {"target_id": "2027-01", "weight": 14}]}
```
- Not calculated by tools: VAT condition (100%, 50% or untaxed per outlet, MM rule 39) and municipal fees, permit costs, FX rates, audience estimates, supplier availability. They come from the tax lead, suppliers and masters.

## Approvals and segregation of duties
- The OOH planner prepares lines and evidence requirements; client approval of the plan runs in `agency-media-planning` by a permissioned approver.
- Requests for supplier holds or confirmations are external messages: require an authenticated human approval bound to the payload digest (`payload_digest` tool) and revision.
- Accepting evidence as delivered belongs to `agency-delivery-reconciliation`, not to the planner who designed the line.

## Exceptions to escalate
- Faces out of circuit, permit expired or availability unconfirmed → supplier via media buyer.
- Supplier quote basis incompatible with the plan model (per face vs per circuit) → planner and buying director decide.
- Package without explicit amount or month-split policy → planner states the policy before saving.
- Uncovered months or expired tariff inside the flight → `agency-rate-cards-contracts`.
- DOOH supplier without documented audience method but CPM requested → price as package or block.
- Missing production, installation or permit costs → `agency-production-estimating`.
- Change requested on installed or billed lines → `agency-plan-changes`.

## Return and handoff
Return `site_plan`, `ooh_line_pricing`, `cost_schedule`, `evidence_requirements`, `booking_proposals`, `exceptions`. Include tenant/client/job IDs, JobNumber, plan number and revision, schedule months, supplier and site IDs, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** OOH planner. **Next:** `agency-media-planning`, `agency-media-buying`, `agency-production-estimating`, `agency-delivery-reconciliation`.

## Connectors and files
- `broadsign` documents DOOH proof-of-play exports/APIs (no MCP or authenticated access bundled; start with file imports). `canva` or `figma` may hold creative specs. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind ooh --file sites.csv --out sites.json --tenant ID --client ID --job ID`.
