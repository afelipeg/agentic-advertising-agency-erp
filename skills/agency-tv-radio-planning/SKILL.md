---
name: agency-tv-radio-planning
description: "Plan TV, radio and cable schedules by program or daypart from a ranking: duration-factor pricing, spot distribution within 99 spots per day, material distribution with royalty checks, traffic instructions and pre/post evaluation. Use for broadcast schedules. Do not book stations, invent ratings or edit controlled or billed spots."
---

# TV and Radio Planning

This stage builds the broadcast body of a media plan: ranking → Radio and TV planner grid (`Planificación de Radio y TV`) → materials and traffic → orders → spot control → post-evaluation. It owns the program/daypart schedule, the per-item duration and rate basis, material assignment, traffic instructions and the pre/post evaluation exchange. Client approval and billing release belong to the plan stage, and it never sends orders to stations or marks spots aired.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P06, P22–P24, P27–P29, P34, P38, R3, R4, R17, R20–R22, R25, R26, §9 Traffic Schedule, §10.3). [media-masters-ooh.md](references/erp/media-masters-ooh.md) (P09 dayparts, P14–P15 materials and royalties, P20 duration coefficients, rules 13–17 duration pricing, 20–21 dayparts and cut-off hour; cited below as MM rule n).

## Use when
- Generating a TV, radio or cable plan from a ranking, or appending a ranking to an existing plan (P34).
- Distributing N spots per program across allowed days in the spot distribution window (`Distribución de Avisos`) (P06).
- Pricing seconds-based media with base duration and duration coefficients (`Coeficientes de Duración`).
- Distributing or assigning materials (`Distribuir Materiales`), checking royalty validity, preparing the traffic schedule (`Pauta Tráfico`).
- Exporting a pre-evaluation or post-evaluation file and mapping results back (`Pre/Post Evaluación`).

## Do not use when
- Building the rating book or ranking → `agency-media-ranking`.
- Plan header, fee, client approval, credit override, approve-for-billing → `agency-media-planning`.
- Changing an ordered, controlled or approved schedule, rescheduling dropped spots → `agency-plan-changes`.
- Generating, sending or versioning insertion orders → `agency-media-buying`.
- Importing monitoring files and matching aired spots → `agency-transmission-control`.
- Producing or clearing creatives and talent rights → `agency-production`; maintaining coefficient tables and dayparts → `agency-master-data`.

## Required inputs
- Blocking: saved ranking linked to an open JobNumber with planning target (P34).
- Blocking: outlets, programs with airing days and start/end hours, daypart set covering 7 × 24 hours (MM rule 20) and the media type's cut-off hour.
- Blocking: valid contract or rate card per outlet and item dates; media type base duration and pricing mode (proportional, respects factors, does not respect factors) (MM rules 13–16); coefficient table where applicable.
- Spot durations and materials registered in the master with duration, products and royalty contracts (MM P14–P15).
- Spot counts per program or investment/TRP objective; weekday exclusions.
- For evaluation: external evaluation provider configured, target names, projected date.

## Procedure
1. Open the ranking and choose approach A (refine ranking first) or B (full ranking, assign spots, then drop programs without spots) (P34). Generate plan to a new plan or append to an existing plan; destination validity 1 day to 12 months.
2. Check program grid integrity: times between 00:00 and the cut-off hour sort after 23:59 of the previous broadcast day (MM rule 21); dayparts cover the week without overlap (MM rule 20). Report gaps instead of guessing a broadcast day.
3. Create one item per program × duration × publication type × material × negotiation period (P34 item limits, R17). A rate or negotiation change mid-flight starts a new item from that date.
4. Distribute spots: enter the total per program; the distribution proposal spreads them across airing days, and excluded weekdays or dates are redistributed among the rest (P06). Enforce ≤ 99 spots per item per day and ≤ 999 items per schedule (R3). Unlocking non-airing weekdays is an explicit item action (P34).
5. Resolve the rate: contract/rate card valid at each date, buy and sell basis, currency locked by contract (P34 detail tab). Derive the duration rate: proportional `base × d ÷ base_duration`; respects factors `base × factor(d)` with fallback to proportional for missing seconds; does not respect factors uses the card rate per duration, else proportional (MM rules 14–16). Resolve the coefficient table from the most specific match (MM rule 17, inferred order).
6. Price each item with `media_line_cost`: `per_second` for proportional seconds pricing; for factored durations pass the resolved spot rate as `per_unit` with `measure` 1; `package` for Package rate type (R4, R5). Apply discounts, surcharges and fee with `discount_cascade`.
7. Compute rating block per item (average rating, TRP, cost per point) with `audience_metrics` from the ranking ratings (P34 columns). Keep estimated ratings separate from measured ones.
8. Save Draft as an alternative only before the first definitive save (P34); commit the chosen alternative. Saving warns when materials are missing — record the warning, do not suppress it.
9. Distribute materials (P22): choose domain (spots without material vs all), ordered vs unordered, date range, criterion, application form, durations, weekdays and basis (spots, TRPs or investment). The quantity to distribute must equal the total exactly (R20). If "update item measure" is on, a different-duration material changes spot duration and price in schedule and order (R21).
10. Check royalty validity: every spot date with a royalty-linked material must fall inside the contract validity; otherwise saving is blocked until the assignment is shortened, the contract extended or another material used (P24, R22).
11. Prepare traffic instructions per vendor: day, hour, spots, program, duration, material and order (§9 Traffic Schedule), plus material delivery status and lead time where delivery control is enabled (P38).
12. Pre-evaluation: export with projected date on the same weekday as the plan's first spot, real hours, material and outlet; import results and map primary/secondary targets (P27, R25). Spots with no detected break are shifted later (morning) or earlier (late night) and re-evaluated.
13. Post-evaluation only after spot control (P28). Re-rating from post-evaluation (P29) updates CPP-based rates and flows to orders only with the add-to-order flag: prepare it as a change for `agency-plan-changes`, never as an in-place edit.

## Rules and locks
- One duration, one publication type and one material per item; mid-flight rate changes need a new item (R17, P34).
- ≤ 99 spots per item per day, including radio (R3, P06).
- Start date cannot move after the first spot nor end date before the last; period moves are whole weeks preserving weekdays (R2, R26).
- Ordered items are locked: vendor and contract cannot change; edits need an unlock in `agency-plan-changes` (§4.3).
- Items with client billing or a registered vendor invoice cannot be deleted; controlled spots are immutable (P34, §4.3).
- Material distribution totals must equal 100% / total spots / total TRPs / total amount (R20).
- Royalty validity failures block saving (R22).
- Pre-evaluation projected date must share the first spot's weekday (R25).
- Supplier-based coefficient criterion is a Dominican Republic option, off by default (MM rule 17) (configurable).
- Coefficient factor base (base rate vs proportional rate) is implied, not explicit (MM gap 16) (confirm locally).
- Rating provider file formats are unspecified; map each provider export explicitly (gap 13) (confirm locally).

## Calculations
- `media_line_cost`: `per_second` gross = rate per second × duration seconds × spots; `per_unit` with a resolved per-spot rate for factored durations; `package` for package totals.
- `discount_cascade`: cascaded discounts, surcharges and agency fee per item; declare `compound` vs `additive`.
- `audience_metrics`: TRP, average rating, CPR and CPM per item or schedule against the planning target; `reach_hundredths` only from a licensed reach figure.

```bash
python3 scripts/agency_tools.py media_line_cost < input.json
```
```json
{"currency": "MXN", "calc_type": "per_second", "rate_minor": 120000, "measure": 20,
 "spots": 15, "volume": 0, "package_minor": 0}
```
- Not calculated by tools: duration factors and coefficient lookup (from masters), ratings and reach (licensed provider), material distribution proposal, taxes and FX. Show factor arithmetic with source table and rounding.

## Approvals and segregation of duties
- The broadcast planner prepares the schedule, materials and traffic; the plan's client approval and credit override run in `agency-media-planning` by permissioned approvers.
- Sending traffic instructions to stations is an external message: requires an authenticated human approval bound to the payload digest (`payload_digest` tool) and revision.
- Material substitutions on ordered spots and re-rating from post-evaluation are plan changes requiring approval in `agency-plan-changes`.
- Talent and music rights clearance belongs to the producer and legal approver, not the planner.

## Exceptions to escalate
- Ranking not linked to an open JobNumber, or programs missing start/end hours → planner / `agency-media-ranking`.
- Daypart gaps or overlaps, missing cut-off hour or coefficient table → `agency-master-data`.
- No valid contract or rate card for an item date → `agency-rate-cards-contracts`.
- Material missing, wrong duration or not delivered by lead time → `agency-production`.
- Royalty contract expires inside the flight → `agency-production` to extend or replace.
- Pre-evaluation omits spots (no break detected) → planner shifts hours and re-evaluates.
- Target-name mismatch on evaluation import → research analyst.
- Request to edit controlled, ordered or billed spots → `agency-plan-changes`.

## Return and handoff
Return `broadcast_schedule`, `spot_register`, `rate_basis`, `material_distribution`, `traffic_instructions`, `evaluation_report`. Include tenant/client/job IDs, JobNumber, plan number and revision, schedule month, ranking id, targets, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Broadcast planner. **Next:** `agency-media-planning`, `agency-media-buying`, `agency-production`, `agency-transmission-control`.

## Connectors and files
- No registry provider books TV or radio or supplies licensed ratings; use station rate files, provider exports and evaluation files. Host marketplace documents/email carry traffic packs once approved. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind broadcast-order|rating|plan --file SOURCE --out OUT.json --tenant ID --client ID --job ID`.
