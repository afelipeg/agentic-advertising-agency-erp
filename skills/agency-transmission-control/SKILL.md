---
name: agency-transmission-control
description: "Checks ordered TV and radio spots against monitoring data: auto and manual matching, missing or extra spots, makegoods, close readiness. Use before closing orders. An invoice is not proof."
---

# Transmission Control (Spot Verification)

This stage proves performance: insertion orders → **monitoring import, code mapping, matching and control (`Control de Avisos`)** → order close, supplier invoice registration and client billing. It owns the per-spot control status (aired, deficient, uncontrolled), the audit code and the actual air time, break and position. It never closes orders by itself, reschedules spots in the plan, or approves a supplier invoice.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-buying.md](references/erp/media-buying.md) (§2.4 P-SV-01..08, §4.3 spot lifecycle, §4.5 certification, BR-V-01..06, BR-O-08, §10.4, §11 gaps 11, 13) and [media-planning.md](references/erp/media-planning.md) (P25 rescheduling, P28 post-evaluation, P30 spot control, R23–R25).

## Use when
- "Import today's monitoring file", `importación de archivos de monitoreo`, Ibope or Monitor logs.
- Mapping unknown channels, clients, products or materials from the monitoring vendor (`códigos externos`, `Cód. Int. 04`).
- Running automatic control (`control automático`, normal or with tolerance) for an order, plan, medium or client.
- Manual spot-by-spot control or bulk control from a paper certificate (`certificado`, `Resumen`, control OK / deficient).
- Listing ordered-not-aired (`no emitidos`) and aired-not-ordered spots, proposing makegoods (`reprogramación`) and checking readiness to close.

## Do not use when
- Issuing, versioning or closing orders → `agency-media-buying` (this skill supplies the close prerequisites).
- Moving the failed spot to a new date in the plan → `agency-plan-changes` or `agency-tv-radio-planning`.
- Matching ordered, delivered and invoiced amounts for payment → `agency-delivery-reconciliation`.
- Digital delivery and pacing → `agency-campaign-optimization`; OOH posting batches → `agency-ooh-inventory` (seller side) or `agency-ooh-planning` (buyer side).
- Configuring audit codes, monitoring providers or outlet interfaces → `agency-master-data`.

## Required inputs
- **Blocking:** tenant_id, client_id, JobNumber, order month/number/version or plan and schedule; ordered spots with station, air date, window start/end, material, publication type.
- **Blocking:** monitoring file or certificate with provider, broadcast-day timezone and cut-off hour, source hash and rights to use it.
- **Blocking:** configured default "aired OK" audit code (`Código Auditoría por defecto en Cierre de Orden`) and the deficient codes with their allows-reschedule flag (P-SV-01).
- Code links (channel, client, product, material) and matching policy: tolerance minutes, match material, match program, match publication type.
- Makegood policy and contractual deadlines; licensed post-evaluation ratings if post-buy is requested.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Check prerequisites: medium flagged as spot-controlled and linked to the monitoring provider, radio zones mapped to provider markets, default OK code configured (P-SV-01). Missing setup → blocked, route to `agency-master-data`.
2. Import: select provider, apply "exclude clients" (list non-agency clients for future exclusion) and "do not associate materials" as policy says (P-SV-02). Record file hash, row count, date range and timezone.
3. Mapping: list unmapped chains, clients, products and materials. Propose candidates with evidence (duration-filtered for materials) but leave the mapping decision to a human; never force a fuzzy name match (§10.4).
4. Quarantine duplicates, rows outside the ordered period and inconsistent durations; times between 00:00 and the media type cut-off belong to the previous broadcast day (media-masters rule 21).
5. Auto match with `spot_match`: normal = air time within [start, end] (BR-V-01); tolerance = within [start, end + tolerance] (BR-V-02); keys = station, date, window, plus material when "match material" is on (BR-V-03). One aired event counts against one ordered spot only.
6. Classify (BR-V-04): unique exact/tolerance match → propose OK with the default code and copy air time, break, position; ambiguous → human picks the event; ordered-not-aired → deficient candidate; aired-not-ordered → buyer review (vendor error or unordered bonus), never auto-billable.
7. Manual control: for spots without monitoring, record audit code, controller user, air time, break, position and observations (P-SV-04).
8. Bulk control from certificates: enter the uncontrolled quantity per summary group and mark OK or deficient (P-SV-05, BR-V-06). Recommended: mark only the failed quantity deficient so the planner can reschedule; leave the rest uncontrolled, knowing close will certify it.
9. Makegood register: per deficient spot list order, version, original date/window, audit code (allows reschedule?), contractual deadline, replacement proposal and client acceptance needed. Rescheduling happens in planning (media-planning P25); verify the replacement aired before marking the original resolved.
10. Post-buy (optional): with licensed ratings use the planning post-evaluation export/import (media-planning P28); keep missing ratings missing.
11. Close readiness: per order report aired / deficient / uncontrolled counts and warn that close turns every uncontrolled spot into aired with the default code (BR-O-08). Propose close only when uncontrolled = 0 or the buying lead accepts auto-certification in writing.
12. Finance handoff: ordered vs aired value per order with `reconcile` (ordered, delivered, invoiced if known, tolerance); dropped spots generate vendor and client differences at close (media-planning R24).

## Rules and locks
- A control cannot be removed on a closed order (BR-V-05, P-SV-06).
- Close auto-certifies uncontrolled spots with the default audit code; warn and verify first (BR-O-08, §10.3).
- Supplier invoices register only against closed orders; an invoice does not prove airing (§4.5).
- Controlled spots are immutable in the plan; billed spots can still be controlled but not rescheduled (media-planning P30, P25).
- Bulk control does not identify which spots failed; selection is arbitrary (P-SV-05). Record that limitation in evidence.
- Tolerance extends only after the window end; the planning variant defaults to 20 minutes (BR-V-02, R23) (configurable).
- Temporary-control configuration allows no-match without marking dropped (R23) (configurable).
- Monitoring file mandatory columns are undocumented (§11 gap 11) (confirm locally).
- Deleting all imported spots for a date is destructive maintenance and needs approval (P-SV-02).

## Calculations
- `spot_match`: `tolerance_minutes`, `match_material`, `ordered[]` (spot_id, station_id, air_date, window_start, window_end, material_id), `aired[]` (event_id, station_id, air_date, air_time, material_id). Split windows that cross midnight first.
- `reconcile`: ordered vs delivered vs invoiced in minor units with an explicit tolerance; `hold` reasons feed the finance handoff.

```sh
python3 scripts/agency_tools.py spot_match < input.json
```
```json
{"tolerance_minutes": 10, "match_material": true,
 "ordered": [{"spot_id": "S1", "station_id": "CH5", "air_date": "2026-10-05", "window_start": "20:00", "window_end": "20:30", "material_id": "M20A"},
             {"spot_id": "S2", "station_id": "CH5", "air_date": "2026-10-05", "window_start": "21:00", "window_end": "21:30", "material_id": "M20A"}],
 "aired": [{"event_id": "E1", "station_id": "CH5", "air_date": "2026-10-05", "air_time": "20:12", "material_id": "M20A"},
           {"event_id": "E2", "station_id": "CH5", "air_date": "2026-10-05", "air_time": "22:05", "material_id": "M20A"}]}
```
Expected: S1↔E1 exact; S2 ordered-not-aired; E2 aired-not-ordered.

Not calculated by tools: ratings and audience (licensed sources only), valuation of dropped-spot differences (undocumented, media-planning gap 14), makegood acceptance, program-name similarity.

## Approvals and segregation of duties
- Traffic or the media buyer prepares matches and controls; a second person (buying lead) confirms manual mappings, ambiguous picks and bulk certificates per agency policy.
- Accepting a makegood or credit, deleting imported spots, removing controls and proposing close with uncontrolled spots require authenticated human approval bound to the `payload_digest` of the exact control set.
- The controller user is recorded per spot; the same user must not approve their own bulk certification.

## Exceptions to escalate
- Unmapped channel/client/product/material codes → media admin for the mapping decision.
- Ambiguous matches → buyer picks the event.
- Aired-not-ordered spots → buyer: vendor error, bonus or claim.
- Ordered-not-aired spots → planner (makegood) and buyer (credit claim) with deadline.
- Wrong material or short duration aired → buyer and account director (client acceptance).
- Monitoring file incomplete for the period → keep spots uncontrolled; request the missing days.
- Close requested with uncontrolled spots → buying lead decides and documents acceptance.
- Supplier invoice arrives for unverified spots → `agency-payables` hold until control is complete.

## Return and handoff
Return `emission_match`, `missing_or_extra_insertions`, `material_exceptions`, `makegood_register`, `close_readiness`, `postbuy_report`, `finance_handoff`. Include tenant/client/job IDs, JobNumber, plan/schedule, order month/number/version, provider and file hash, revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Media buyer and traffic. **Next:** `agency-media-buying` (close), `agency-plan-changes` (makegoods), `agency-delivery-reconciliation`, `agency-payables`.

## Connectors and files
- Provider ids from `integrations/registry.json`: `broadsign` for DOOH proof-of-play; `composio` or `zapier` for reviewed ERP or monitoring-vendor access; host marketplace documents for certificates. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind emission ...` for monitoring logs, `--kind broadcast-order` for ordered spots, `--kind rating` for post-evaluation ratings.
