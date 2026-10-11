---
name: agency-digital-planning
description: "Build digital media plans by platform, format and buy type (CPM, CPC, CPV, CPA), render naming taxonomy and UTM strings, add ad-server costs, sync planned vs actual and reprice ordered items from Google or Meta invoices matched by taxonomy. Use for digital plan items and invoice-based order adjustment. Do not launch campaigns or post invoices."
---

# Digital Planning

This stage runs the reference ERP's digital planner (`Planificación Digital`): no-book or book ranking → digital plan items → client approval → order → planned vs actual and ad-server sync → order adjustment from platform invoices → payables and billing. It owns digital items, taxonomy strings, ad-server cost lines, actuals snapshots and the invoice-to-order adjustment proposal. It never creates or edits campaigns in ad platforms, registers vendor invoices or approves its own repricing.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P35 digital planner steps 1–9, P06 internet classic plan, R4, R27, R28, §4.4, §10.4, gaps 3 and 11). [media-masters-ooh.md](references/erp/media-masters-ooh.md) (digital masters in §3.2, P19 fee by publication type, P26 taxonomy, rules 29, 31–33; cited below as MM rule n). [payables-treasury.md](references/erp/payables-treasury.md) (P7 portal invoice validation, P8 taxonomy line reconciliation, rule 3, §10.3 controls; cited below as AP Pn or AP rule n).

## Use when
- Creating a digital plan from a ranking linked to an open JobNumber: platform, publication type, format, buy type, clicks, impressions, CTR, gross rate and AdServer per item (P35 steps 1–3).
- Rendering naming strings and UTM URLs from the client's taxonomy templates (`Taxonomía`) for product, plan, item, creative and UTM levels (MM P26).
- Adding ad-server costs (`Costo Pauta`) per tracking type as a % of investment or fixed value (P35 step 3).
- Updating planned vs actual (e.g., CPC negotiated clicks vs delivered clicks) on ordered items, or syncing an ad server (P35 steps 7–8).
- Adjusting orders from Google or Meta invoices by taxonomy (`Ajustar Órdenes por Comprobantes`) (P35 step 9, AP P8).

## Do not use when
- Creating, launching or pausing campaigns in ad platforms → `agency-campaign-activation`.
- Pacing and optimisation recommendations → `agency-campaign-optimization`.
- Plan header, client approval and billing release for the whole plan → `agency-media-planning`.
- Registering, validating or paying the platform invoice → `agency-payables`, `agency-payment-run`.
- Order-level delivery differences and write-offs → `agency-delivery-reconciliation`.
- Changing approved digital lines beyond invoice repricing → `agency-plan-changes`.
- Maintaining platforms, formats, buy types, tracking types, AdServers or taxonomy templates → `agency-master-data`.

## Required inputs
- Blocking: open JobNumber and a saved ranking (with or without book) linked to it (P35 step 1–2).
- Blocking: digital masters — generic media type mapping, platforms, formats (format implies measure), buy types, digital calc types, publication types, tracking and placement types, AdServers, dynamic categories (P35 prerequisites).
- Per item: vendor, billable flag, direct/indirect, contract or rate card, currency, planned clicks/impressions/views/actions and gross rate.
- Agency-fee mode and %, with client-specific digital fee by publication type where configured (MM P19, rule 29).
- For taxonomy: active template for the holder client, tag dictionary, external codes, ad-server or site restriction (MM P26).
- For actuals: ordered plan, actuals export with account ID, date range, timezone and currency.
- For invoice adjustment: platform invoice registered automatically via e-invoicing with lines carrying taxonomy order codes, and prior reconciliation (P35 step 9).

## Procedure
1. Verify the ranking is linked to an open JobNumber and negotiations are set; then generate the plan with validity, topic, calculation form and fee defaults (P35 steps 1–2). Payment term edits stay with access levels 1A/1B.
2. For each item set platform, publication type, format, buy type, quantities and gross rate; mass changes may propagate a value from the first item only after the planner confirms (P35 step 3). Restrict publication types to those allowed for the buy type (MM rule 29).
3. Price each item with `media_line_cost`: CPM/CPV `per_thousand` (volume = impressions or views), CPC and CPA `per_action` (volume = clicks or actions), fixed `package` (MM rule 31). The classic internet formula height × width × days × spots × CPM is legacy and dimensionally odd (R4, gap 3); do not use it for new items.
4. Apply discounts and the agency fee with `discount_cascade`. Add ad-server costs per contracted site as % of investment or fixed amount; each needs placement type and tracking type, a direct/indirect flag and whether fee applies (P35 step 3). Ad-serving cost = impressions ÷ 1000 × ad-server cost for the tracking type; client price and supplier cost may differ (MM rule 32).
5. Render taxonomy strings by interpolating template tags with entity context and external codes; quarter tag `Q = floor((month + 2) ÷ 3)` and 4- or 2-digit year (MM rule 33). Treat the `{L}` modifier as lowercase only after local confirmation (MM gap 18). Validate every rendered string is unique per order item and that UTM values contain no personal data.
6. Save Draft for alternatives, then route the plan for client approval (P35 steps 3–4). Orders are generated only after approval, with cost per item defaulting to the planned value and optional vendor discounts shown on the internal order (P35 step 5, R27).
7. Planned vs actual (P35 step 7): only on ordered items. Snapshot actuals from a read-only source; for CPC, final rate = actual clicks × unit rate for both sale and purchase (R4, inferred). Present the before/after per item; keep vendor-reported and ad-server-served counts separate (P35 step 8).
8. Platform invoice repricing (P35 step 9, AP P8): list invoice lines matching this plan's taxonomy or with no taxonomy; auto-match by taxonomy order code, then propose manual links for leftovers. Only items pending adjustment and in the same currency as the line are eligible (R28).
9. Per matched line run `reconcile` (ordered vs delivered vs invoiced) and record `difference = billed − ordered` with ordered = 0 when unmatched (AP rule 3). Run `invoice_check` on the invoice's VAT and total before relying on line amounts.
10. Prepare the adjustment proposal: reopen the order if closed (blocked if billed), switch matched items to fixed-cost calculation, set billable amount for schedule and order to the matched invoice line amount, close the order (R28). Present it as one approval pack; never apply it without approval.
11. After approval and host execution, read back order state, mark the invoice Associated only when every line is linked (AP P8), and hand differences to reconciliation and billing.

## Rules and locks
- Ranking is mandatory for the digital planner and must be linked to an open JobNumber before Generate Plan (P35).
- Orders only on approved plans; order cost defaults to planned and may be edited with a recorded reason (P35 step 5, R27).
- Planned vs actual and ad-server sync require the plan to be ordered (P35 steps 7–8).
- Invoice adjustment requires taxonomy on orders, e-invoice registration with order complement and prior reconciliation (P35 step 9).
- Adjustment matches only same-currency lines and items pending adjustment; reopening a billed order is blocked (R28).
- Adjusted items become fixed cost with cost equal to sale on those items (media-planning §6).
- Taxonomy line difference = billed − ordered; unmatched ordered = 0 (AP rule 3).
- Unmatched lines are linked manually only by users with plan-modify permission (AP P8).
- Dynamic categories cannot change on items with client-invoiced months or closed orders (MM rule 6).
- Taxonomy rules used for platform matching are not documented beyond templates (gap 11) (confirm locally).
- Invoice validation and posting stay with AP, with formal validator ≠ requester (AP rule 2, §10.3).

## Calculations
- `media_line_cost`: `per_thousand` for CPM/CPV, `per_action` for CPC/CPA, `package` for fixed buys.
- `discount_cascade`: discounts and agency fee; ad-server cost as a % uses `surcharges` only if your policy treats it as a surcharge, otherwise price it as its own item.
- `reconcile`: ordered vs delivered vs invoiced per matched line with an explicit tolerance; status `hold` blocks automatic repricing.
- `invoice_check`: recompute invoice VAT by rate and total vs declared before using line amounts.

```bash
python3 scripts/agency_tools.py reconcile < input.json
```
```json
{"currency": "USD", "ordered_minor": 1250000, "delivered_minor": 1250000,
 "invoiced_minor": 1187340, "tolerance_minor": 0}
```
- Not calculated by tools: taxonomy rendering (template interpolation by policy), platform currency conversion, VAT rates and digital-service perceptions (from the tax lead), attribution and conversions. Never convert currencies to force a match.

## Approvals and segregation of duties
- The digital planner prepares items, taxonomy and adjustment proposals; client approval of the plan is recorded by a permissioned approver in `agency-media-planning`.
- Order generation, planned-vs-actual repricing, ad-server upload and invoice-based adjustment each change money or external state: require an authenticated human approval bound to the payload digest (`payload_digest` tool), plan revision, order version and currency totals.
- The person who validated the platform invoice in AP must not be the only approver of the repricing it drives.

## Exceptions to escalate
- Ranking not linked to an open JobNumber or masters missing (format, buy type, tracking type) → `agency-master-data`.
- Taxonomy template missing, inactive or rendering duplicates → digital ops owner.
- Invoice line without taxonomy or matching another plan → leave unmatched; AP owner and planner review.
- Currency of invoice line differs from item → block; never convert to match.
- Order already billed, so it cannot reopen → `agency-plan-changes` and `agency-client-billing` for a credit/debit path.
- `reconcile` returns hold (invoice exceeds order or delivery) → `agency-delivery-reconciliation`.
- `invoice_check` mismatch → `agency-payables`.
- Actuals source and ad server disagree on counts → planner records both; no silent choice.

## Return and handoff
Return `digital_plan`, `taxonomy_strings`, `adserver_costs`, `actuals_snapshot`, `invoice_match_register`, `order_adjustment_proposal`. Include tenant/client/job IDs, JobNumber, plan number and revision, order numbers and versions, invoice ids and line numbers, account IDs, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Digital planner. **Next:** `agency-media-planning`, `agency-media-buying`, `agency-campaign-activation`, `agency-delivery-reconciliation`, `agency-payables`.

## Connectors and files
- Read actuals with `google-ads` (read-only query toolset), `google-analytics`, `supermetrics`, `amazon-ads`, `ryze` or `synter` within approved accounts; for Meta use the Meta-hosted `meta-ads` MCP with a read-only grant. Platform writes belong to `agency-campaign-activation`. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan|invoice --file SOURCE --out OUT.json --tenant ID --client ID --job ID`.
