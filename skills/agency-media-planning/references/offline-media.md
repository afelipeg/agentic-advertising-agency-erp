# TV, radio, OOH, DOOH and print operating detail

Use this alongside the stage skills and control contract. A generic digital connector does not replace broadcaster booking, licensed ratings, supplier agreements or installation/airing evidence. Prefer enabled native apps for document storage/work management; access to licensed datasets and legacy supplier systems is separate. Redacted XLSX/CSV and human confirmations are first-class inputs.

## Media masters and audience books

Maintain stable provider, medium, market, program/location, publication-type and external-code mappings. Do not join merely on similar program names. For a book, record provider, permitted use, market, measurement dates, rating type, target definitions, population/sample metadata, medium/program/day and unit scale. Mark unavailable or unreliable estimates as missing; keep zero only where genuinely measured. Planning target and negotiation target may differ. Store original and adjusted/weighted values with a reason and owner. Do not use a generic web search to fabricate licensed audience figures.

## Ranking and commercial inheritance

A ranking can be a reproducible candidate subset, not only a sorted leaderboard. Record book or no-book mode; medium/site and program/location selection; audience targets; timebands, weekdays and geography; data exclusions; sort criteria; client/job; rate basis and source version. If no program/location master exists, resolve it before generating the relevant candidate lines. No-book mode supports an inventory/rate shortlist with audience metrics explicitly unavailable.

Record currency, rate effective month/period, duration basis, publication type, buying/selling gross/net basis, chosen supplier contract and tariff, and the approved exchange-rate reference where needed. Carry these references into the plan rather than copying anonymous numbers. Revalidate inherited terms after client, date, medium or publication changes. If multiple applicable agreements conflict, ask the commercial owner rather than silently choosing the cheapest.

Metrics require a declared numerator/denominator and compatible source: rating percent/points, audience count, target universe, CPM, cost per rating point and affinity. Never sum audience into unique reach, equate planned with measured ratings, or compare different periods/targets without an explicit limitation. Produce the candidate table, excluded/missing-data rows and selection rationale for human review. No local calculator in this package creates a rating book, deduplicated reach or licensed post-buy measurement.

## TV/radio schedule and order register

At minimum retain line/spot IDs; station/medium and supplier; market; program or timeband; local/broadcast day, timezone and emission date/window; spot duration; material/version code; publication format; number of spots; rate unit and contracted buying/selling basis; currency; applicable order/contract; approval/revision and actual delivery/financial status. Repeaters are separate placements unless the authoritative schedule defines a shared identity. Import updated programming with a reviewed mapping and version history.

Rates may be per second, per spot, a package or a contracted audience-based formula. Require all operands; a missing imported rate is not free inventory. Track seconds/units and amount caps independently where the contract uses both. A contract may cover a parent pool and subcontracts; check the shared ceiling and relevant subset without double counting. Validate negotiated share/daypart/day constraints across the relevant order set, with the contract's actual denominator; do not apply a made-up quota rule.

Generate supplier-specific order/material instructions from the approved schedule. Confirm booking and material acceptance separately. Preserve dates and supplier references for changes across months, expired rate sheets, postponed programs and replacements. Agency prepayment or barter changes settlement/accounting treatment; it does not make delivery cost disappear. Fee, confidential rebate, client discount and supplier buying price need separate fields and appropriate client visibility.

## Traffic, material delivery and emission verification

Create a traffic register linking station/site, order/spot IDs, material checksum/code, duration, format, rights, delivery channel, cutoff, receipt, technical acceptance and scheduled use. A dispatched file is not necessarily accepted by the broadcaster. Hold missing/wrong material, expired rights or inconsistent duration; if a substitute is proposed, get applicable approval and revise the related orders.

Match ordered insertions to actual monitoring records using reviewed station, broadcast-day, time-window, duration and creative rules. Keep monitor source and supplier certificate separately; reconcile differences. Record unobserved, shifted, wrong-material, truncated, extra, duplicated and disputed transmissions. Do not count a single evidence event twice or automatically pay for unordered spots. Human judgment handles ambiguous name/time matches. A makegood needs its own replacement specification and verified emission; until accepted it does not erase the original shortfall.

Post-buy analysis separates ordered, monitored, accepted, billed and credited delivery. Use actual licensed ratings for the relevant target/window when available; distinguish estimated from measured outcomes. Report missing evidence and basis changes. Feed accepted delivery and disputed balances into the financial reconciliation, then client billing, supplier payable, rebate eligibility and job margin. A strong audience result cannot waive invoice/PO controls.

## OOH/DOOH and print

For static exterior retain face/site/circuit IDs, geographic/store relation, dimensions, orientation, ownership, booked period, production/installation/removal dates and supporting permits/rights where policy requires them. Costs may include rental, printing, installation, lighting, taxes, permit and dismantling. A dated installation photo proves a point-in-time observation, not the entire booked period or measured reach. Record missing/late installation, relocation and downtime as explicit exceptions.

For DOOH retain screen/player/site ID, creative ID/version, campaign/order/slot, play timestamp/duration, loop/share-of-voice basis, booked exposure and proof-of-play source. Do not turn plays into human impressions without the supplier's documented audience method. Broadsign documents proof-of-play exports/APIs, which can be ingested through a reviewed host adapter or file export; **no Broadsign MCP or authenticated account is bundled**. Other vendors follow their own actual integration contracts. Proof-of-play is not itself an accepted invoice.

For print retain publication/edition/issue/date, section/page, placement/format, dimensions and tariff unit, ordered quantity and tear-sheet/acceptance evidence. A newspaper per-centimeter/column rate and an OOH per-face rate are not interchangeable. Missing measurement/rate fields block a calculated line total; a negotiated package requires an explicit amount and terms. Apply discounts/additional costs in the documented order/basis, not a guessed sum of percentages.

## Daily changes and finance

Retail change requests can affect promotions, geography, material, dates and costs even when plan total is unchanged. Route the exact before/after revision through plan-changes. Keep irreversible printing/installation or noncancellable broadcast commitments as exposure until verified resolution. If a line is billed or closed, link credits/replacements/adjustments; never delete it to simplify the new plan. Reconcile accepted units, monetary basis, tax/FX, customer procurement prerequisites and supplier invoice identity before settlement.

## Data routes and known gaps

Use approved licensed audience/programming/monitor feeds if the user actually has them. Otherwise request exported books, supplier rate/contract files, order spreadsheets, creative/material registers, emission logs, proof-of-play, installation evidence and invoices. The agency operator authenticates to archaic systems and supplies receipts. The assistant can prepare a validated import/change pack; it must not imply it wrote into that system. See [file-mode.md](file-mode.md) for UI/CLI handling.

Provider reference: [Broadsign real-time proof-of-play](https://docs.broadsign.com/broadsign-control/latest/en/real-time-pop-api.html). Other private broadcast/ratings interfaces remain provider-specific and unverified. Add adapters only after schema, access, rights and sandbox verification; retain a file route for small agencies.
