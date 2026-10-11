---
name: agency-rate-cards-contracts
description: "Maintain media rate cards (buy and sell price sets, printed vs client cards, base-card inheritance, validity) and media buy contracts (caps, installments, parent/child, share, adjustments, transfers, balance). Use when pricing references or vendor contract terms change. Do not issue insertion orders or bill clients here."
---

# Rate Cards and Media Buy Contracts

This stage sits between media master data and planning: masters (outlets, publication types, programs) → **rate cards (`Tarifarios`) and buy contracts (`Contratos de Compra de Medios`)** → media plans, insertion orders and client billing. It owns the rate card header and its buy/sell rate lines, and the contract with its installments, adjustments, transfers and current account. It never issues orders, posts journal entries or invoices anyone; installment schedules it prepares become billable only through the billing stages.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-buying.md](references/erp/media-buying.md) (§2.1 P-RC-01..13, §2.2 P-CT-01..05, §4.1–4.2, BR-T-01..12, BR-D-01..05, BR-C-01..12, §10.3, §11 gaps 1, 2, 8, 10, 12, 15) and [media-masters-ooh.md](references/erp/media-masters-ooh.md) (§3.2 classification entities, rules 13–17 duration pricing, 24 surcharges, 45 and 59 OOH rate card and agreement, §11 gap 1).

## Use when
- Creating or renewing a rate card (`tarifario`) for an outlet, printed (`tarifa impresa`, all clients) or client-negotiated.
- Mass updating rates: apply amount, apply discounts 1–4, copy with a coefficient (`Copiar Tarifario`, `Usa Tarifario Base`).
- Creating a buy contract: cap (`Valor Tope`) or free consumption (`Consumo Libre`), by amount or seconds/cm, installments (`Cuotas`), parent/child (`subcontrato`), barter (`Canje`).
- Preparing a contract adjustment (`ajuste de contrato`) or a balance transfer between contracts (`transferencia entre contratos`).
- Answering "how much is left on the contract", "which rate applies on this date", or a share-of-spend check (`share por contrato`).

## Do not use when
- Building or revising the plan or schedule (`pauta`) itself → `agency-media-planning`, `agency-tv-radio-planning`, `agency-digital-planning`, `agency-ooh-planning`.
- Issuing, versioning, sending or closing insertion orders → `agency-media-buying`.
- Seller-side billboard agreements (`convenio VP`) and face inventory → `agency-ooh-inventory`.
- Overcommission, incentive-scale or finder-fee contracts with vendors → `agency-rebates`.
- Invoicing installment schedules to the client → `agency-client-billing`; client agreements and client POs → `agency-contract-po`.
- Creating outlets, publication types, programs, surcharges or GL accounts → `agency-master-data`.

## Required inputs
- **Blocking:** tenant_id; medium (outlet) or provider with its media type; holder client or the printed/generic scope; currency and configured exponent; validity start (and end, recommended).
- **Blocking for rate cards:** calculation type (flat per second, per unit, CPP, CPM, digital types), per-program or per-time-band entry, publication type, base card + coefficient or copy source + coefficient when derived.
- **Blocking for contracts:** billing client (or the Agency client), consumption type, control type, payment condition, gross amount or seconds cap, VAT inclusion flag, agency commission %, discounts 1–4, assignment (billing clients/products), rate cards by date range.
- **Blocking for installments:** advance %, number of installments, first month, JobNumber or confirmation that a generic job is used.
- **Blocking for adjustments/transfers:** month, contract (and subcontract), current balance from the authoritative contract current account, amount, direction (in favour of Agency or Medium), billed status.
- Signed vendor negotiation evidence (document reference, not pasted credentials). Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Confirm prerequisites exist and are active: outlet with media type, publication types, programs/locations or time bands, providers, and for contracts an active billing client (P-RC-01, P-CT-01). Missing masters → blocker routed to `agency-master-data`.
2. Rate card header: choose criterion by medium (by media type is practically unused), scope (no client = printed card), description, validity, currency, calculation type, program vs time band, reference CPP; for CPR cards attach target and book (P-RC-01, P-RC-13). Always propose an end date: a plan date outside validity finds no rate (BR-T-10).
3. Derivation: with `Usa Tarifario Base` the child keeps the base gross read-only, adds its own discounts and inherits later base changes (BR-T-08); with copy, each target rate = source rate × coefficient (BR-T-07, P-RC-04). Keep the same calculation and publication type in source and target (P-RC-05).
4. Rate lines: for every program/band capture the **order (buy)** gross + discounts 1–4 and the **schedule (sell)** gross + discounts 1–4; compute both nets with `discount_cascade` (BR-T-06, BR-D-01). Price sample lines with `media_line_cost` to sanity-check the calculation type (BR-T-01..05). Rounding mode for the Round action is unspecified (confirm locally) (P-RC-09).
5. Precedence check: contract-pinned card for the date range → client card → printed card (BR-T-09). Report overlaps or gaps in validity across cards of the same scope.
6. Contract header: validate combinations before drafting — free consumption forces cash payment; installments require a cap; seconds consumption requires a seconds measure; a child needs an existing parent and has no cap of its own (BR-C-03, BR-C-05, §10.1 item 6). One contract = one medium + one client (P-CT-01).
7. Contract terms: VAT inclusion flag, payment condition and term, currency with fixed FX yes/no (BR-C-11), gross cap, client discounts 1–4, agency commission %, discount application criterion (values unknown; confirm locally), default discounts/surcharges, confidential discount and its settlement mechanism (BR-C-10), assignment and rate cards by date range.
8. Share tab: record global, per-band and per-day share %. The denominator is undefined in the reference (§11 gap 8); state the agency's definition before any compliance statement (BR-C-09).
9. Installments: run `installment_schedule` (advance = gross × advance %, one installment per validity month, remainder on the last). Verify advance + Σ installments = gross after any manual edit (BR-C-04). Note that saving generates one schedule per installment in Pending and immediately billable; this is a billing commitment needing approval.
10. Balance: compute balance = gross − Σ consumption ± adjustments − transfers out + transfers in, with consumption counted with or without VAT per the flag, or in seconds (BR-C-01). Children consume the parent balance. Use `budget_check` for headroom before any new consumption (authorized = cap, spent = consumed, open commitments = open orders).
11. Adjustment: draft month, sequential number, in favour of Agency/Medium, contract, subcontract, schedule/order, current balance, amount, reason (P-CT-02). An adjustment in favour of the agency creates no client pending (BR-C-06); in favour of the medium, consequences are unstated (confirm locally).
12. Transfer: origin and destination client + contract must differ (BR-C-07); both balances change immediately; balance-sheet accounts are involved but unnamed (P-CT-03, confirm locally with `agency-general-ledger`).
13. Bind every proposal (card version, contract, installments, adjustment, transfer) with `payload_digest`, return it as `pending_approval`, and record the system's real document number only when a trusted connector or uploaded export returns it.

## Rules and locks
- A rate card, contract, adjustment or transfer can be deleted only if never used or billed; otherwise deactivate or reverse (P-RC-01, BR-C-12).
- Base-card gross rates are read-only in derived client cards; edits belong on the base and propagate (BR-T-08). Flag every child card affected by a base change.
- Out-of-validity dates yield no rate; never silently extend validity to make a plan price (BR-T-10).
- Without a rate card, automatic ordering sets buy price = sell price (BR-T-12); warn planners when a card is missing for an outlet with negotiated buy terms.
- Cap control: consumption must not exceed the cap; free consumption has no cap (BR-C-02). A breach is an escalation, not an auto-adjustment.
- Installments: advance + Σ installments must equal gross exactly in minor units (BR-C-04).
- A prepaid Agency-client contract makes orders book zero cost at ordering (BR-C-08); keep that out of client-facing margin claims until confirmed.
- Discounts on items carrying a contract are editable only when `Permite modificar descuentos en ítems con contrato` is on (BR-D-05) (configurable).
- Discount cascade defaults to compound; additive and contract-replaces-card modes exist (BR-D-02) (configurable). Surcharge accumulation semantics (confirm locally) (BR-D-03).
- `Impide tarifas manuales` restricts rate, discount and surcharge edits to the top access level (media-masters rule 10) (configurable).
- Duration pricing: proportional, respects factors (fallback proportional), or per-duration entry (media-masters rules 13–17).
- OOH rate card structure is undocumented in the reference (media-masters §11 gap 1) (confirm locally).

## Calculations
- `discount_cascade`: buy and sell nets for a rate line or contract default, `mode` compound|additive, up to 8 `discounts_bps` (the reference uses 4 per price set), surcharges with `accumulative`; set `fee_base: none` when only computing a rate net.
- `media_line_cost`: test a rate under its calculation type (`per_second` flat cards: rate × seconds × spots; `per_unit`; `per_thousand` CPM; `per_action` CPC/CPA; `package`). CPP is not a calc type here: compute the CPP rate externally from licensed ratings and pass it as `per_unit` only with the formula documented (BR-T-02 inconsistency, §11 gap 2).
- `installment_schedule`: advance + monthly installments that sum exactly to gross.
- `budget_check`: contract headroom snapshot; it does not reserve balance.

```sh
python3 scripts/agency_tools.py installment_schedule < input.json
```
```json
{"currency": "MXN", "gross_minor": 120000000, "advance_bps": 2000, "installments": 6, "start_month": "2026-11"}
```
Expected: advance 24000000, six installments of 16000000, total 120000000.

Not calculated by tools: CPP and CPR values (need licensed ratings), share-of-spend denominators, FX rates, VAT tables, coefficient-table resolution, back-solving gross from a net "apply amount" (BR-T-11, method unstated). These come from authoritative sources or agency policy.

## Approvals and segregation of duties
- The media buyer or media admin prepares cards and contracts; the media buying director (or delegate per agency policy) approves new cards, mass updates, contract creation, adjustments and transfers.
- Contract creation with installments, adjustments, transfers and any rate change on a card already used by open plans require authenticated human approval bound to the `payload_digest` of the exact payload, revision, currency and total. A user-typed "approved" is not approval.
- The preparer cannot approve their own proposal. Finance co-approves transfers and installment contracts because they create billable schedules and balance-sheet movements (agency policy).

## Exceptions to escalate
- Plan or order date outside every valid card → planner and buying director; manual price needs approval.
- Contract cap exceeded or projected to be exceeded by open orders → buying director and account director.
- Share restriction breached or denominator undefined → buying director; do not certify compliance.
- Installment edits that break advance + Σ = gross → return blocked to preparer.
- Adjustment or transfer on a billed item or with a stale balance → finance; re-read the current account.
- Base-card change that would reprice open, ordered schedules → buying director and affected planners via `agency-plan-changes`.
- Confidential discount without a settlement mechanism or GL mapping → controller.
- Foreign-currency contract without fixed-FX decision → finance.
- Vendor evidence conflicts with the drafted terms → buying director; keep both versions.

## Return and handoff
Return `rate_card_drafts`, `contract_drafts`, `installment_schedules`, `contract_balance_report`, `adjustment_transfer_proposals`, `pricing_exceptions`. Include tenant/client/job IDs, JobNumber (installment contracts), card code and version, contract number and subcontract, revision, currency and exponent, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified in the system of record), evidence references, blockers, approvals required and next stage.
**Owner:** Media buying director. **Next:** `agency-media-planning`, `agency-tv-radio-planning`, `agency-digital-planning`, `agency-media-buying`, `agency-client-billing` (installment schedules).

## Connectors and files
- Provider ids from `integrations/registry.json`: `composio` or `zapier` only for reviewed read/write of the agency ERP or spreadsheets; `notion` for negotiation evidence; host marketplace documents for signed contracts and vendor rate sheets. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan ...` to normalize plan lines that consume a contract, `--kind ooh` for OOH rate items. Vendor rate sheets have no template: request a values-only CSV and map columns explicitly.
