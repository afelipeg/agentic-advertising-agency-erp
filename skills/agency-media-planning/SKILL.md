---
name: agency-media-planning
description: "Builds a media plan from a JobNumber: monthly schedules, spots priced per media type, agency fee, client approval and credit gates, billing release. Use for plans and approvals."
---

# Media Planning

This stage turns an open `JobNumber` into a priced, schedulable media budget: ranking or program list → plan (`Plan de Medios`) with one monthly schedule (`Pauta`) per calendar month → client approval (and credit override) → orders → spot control → approval for billing. It owns the plan header, items (`Ítems`), spots (`Avisos`), totals, objectives and the approval and billing-release records. It never issues or sends insertion orders, posts invoices or approves its own proposal.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P05–P07, P09–P14, P31, P34 objective widget, §4 lifecycles and spot state machine, R1–R17, R29–R30, §10.3 controls, gaps 1, 2, 6). [media-masters-ooh.md](references/erp/media-masters-ooh.md) (classification rules 1–12, surcharges and additional costs rules 24–30, agency service %, VAT condition 39; cited below as MM rule n).

Agency policy: apply `currencies`, `jobs`, `commercial` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- Building a new plan header from a JobNumber, copying a plan (`Copiar Plan`) or generating one from a ranking.
- Adding items and spots across monthly schedules and pricing them per media type (TV/radio seconds, press cm × columns, OOH circuits, digital units).
- Computing totals: gross, discounts, surcharges, net, bonus, billable, agency fee (`Servicio de Agencia`) and taxes; tracking budget, TRP or reach objectives.
- Running client approval by plan or by schedule (`Aprobación por Cliente`), credit-limit override, rejecting/recovering spots, or approving spots for billing (`Aprobar para Facturar`).
- Requests such as "arma la pauta de noviembre", "approve the plan for the client", "release spots for billing".

## Do not use when
- Building books or rankings → `agency-media-ranking`.
- Detailed broadcast schedules, duration factors, materials, traffic, pre/post evaluation → `agency-tv-radio-planning`.
- OOH/DOOH/print circuits and evidence → `agency-ooh-planning`; digital platform/format/buy-type plans → `agency-digital-planning`.
- Revising an approved or ordered plan, rescheduling, unlocking ordered spots → `agency-plan-changes`.
- Generating, sending, closing or versioning insertion orders → `agency-media-buying`.
- Client PO and reserve balances → `agency-budget-control` or `agency-contract-po`; invoicing released spots → `agency-client-billing`.

## Required inputs
- Blocking: tenant, open JobNumber (billing client, product, work typology, division, billing code), media type, validity from/to.
- Blocking: outlets linked to the media type with at least one vendor and a default vendor; publication types defined (P05 preconditions).
- Plan currency and, for foreign currency, the approved monthly reference FX (indicative only) (P05 step 5, R15).
- Agency-fee calculation type, % or fixed amount, fee discount (`% Bonificación`) and billing mode `Junto` or `General`, defaulted from the billing client (master agency-service %).
- Rating criterion (book, ranking or manual) and targets for TV/radio/cable; valid contracts and rate cards per item.
- Approval configuration: `Circuito Aprobación Medios` (none/restricted/strict), approval period (plan or schedule), `Aprobación para Facturar`, credit-limit flag (§4.5).
- For credit checks: authoritative credit limit, open AR and approved-unbilled amounts from AR, not from a user sheet.
- Client PO number for the plan and per-month budget numbers when the client requires them.

## Procedure
1. Verify the JobNumber is open and its billing code allows media; inherit billing client, product and typology read-only (P05 step 1). A closed job or a billing code pending assignment blocks the plan.
2. Validate validity: at most 12 calendar months, one schedule per month touched, so at most 12 schedules (R1). Minimum length is 1 or 2 days depending on the source page (gap 1) (confirm locally). Confirm one media type per plan (MM rule 2).
3. Compose the header: topic, contact, client PO (`Nº Pedido cliente`) and per-month budget numbers, division, billing split code (`Código de Apertura`) only if the JobNumber billing code allows group billing (P06), payment term in single integer days (R14), order-only flag (`Solo Para Ordenar`), direct/indirect mixing flag, fee settings, currency and monthly reference FX (P05 steps 2–5).
4. Set rating criterion and targets, default negotiations per outlet and objectives (budget, TRP, optional detail by vendor or zone × month) (P05 steps 6–8). Frequency = TRP ÷ reach only when licensed reach is supplied (P34).
5. Add items from ranking, program list or manually (only registered programs when the media type forbids free entry, MM rule 9): outlet, vendor, program/placement, publication type, unit of measure, hours, purchase dates, measure, rate type Normal or Package, rate, discounts and surcharges (P05 body). One duration, one publication type and one material per item; a rate or negotiation change mid-flight needs a new item from that date (R17).
6. Enter spots per day: at most 99 per item per day and 999 items per schedule (R3); only program airing days are selectable when programs were imported (P05).
7. Price each item deterministically with `media_line_cost` (R4): TV/radio `per_second`, press `per_unit` with measure = cm × columns, OOH `per_unit` with circuits as measure and spots = 1, digital `per_thousand` or `per_action`, Package `package` (R5). Missing rate, measure or spots is a blocker, never zero.
8. Apply surcharges, cascaded discounts and the agency fee with `discount_cascade` (R6–R8, R11). Set item detail: billing type Billable/Bonus/Barter (R9), direct vs indirect (R10; direct means sale equals cost), fee applies, VAT applies (R12), vendor commission (R13), contract and rate card (selecting a card replaces the rate, manual resets it, R16). Split Package amounts across months equally or by purchased days (R5, configurable).
9. Totals: investment, bonus, gross, discounts, net, billable, fee after fee discount and taxes, per schedule and plan; achieved vs objective and surplus (P05 totals). Save with a revision reason when the revision scheme is on (P09); never save past a validation error.
10. Credit check before approval: run `credit_exposure` with authoritative AR figures. If the limit would be exceeded and the credit flag is on, the approval request must include a credit override (P12, R30).
11. Prepare the client approval pack per the configured period (whole plan P10 or per schedule P11): reject spots the client did not accept first (P13); rejection is preferred to deletion and keeps history (R29). The approved revision is recorded and the revision counter resets to 0 for ordering (P09).
12. Hand approved schedules to ordering; orders cannot be issued on unapproved plans when the circuit is restricted or strict (P10, §4.5).
13. After orders exist (and, where configured, client approval), prepare approve-for-billing for selected spots per schedule (P31). Released spots go to billing; billed spots are locked (§4.3).

## Rules and locks
- JobNumber must be open; billing client, product and typology are read-only on the plan (P05).
- Validity ≤ 12 calendar months; schedules = calendar months touched (R1). Shortening dates can drop spots (R2).
- ≤ 99 spots per item per day and ≤ 999 items per schedule (R3).
- Payment term is a single day count, editable only by access levels 1A/1B and only if configured (R14) (configurable).
- Direct items: plan investment must equal order cost; mixing direct and indirect needs the header flag (R10).
- Bonus items are priced but billable 0; barter is not billed unless configured (R9) (configurable).
- Contract or rate card with fixed currency locks the item currency (R15); vendor and contract are locked once ordered (§4.3).
- Unapproved spots are rejected before client approval; orders are blocked on unapproved plans when the circuit ≠ none, and until the credit override when over limit (P10, P12, §4.5).
- Spots with client invoice or registered vendor invoice cannot be modified or deleted; controlled spots are immutable (§4.3).
- Rejected spots are excluded from totals and printouts; deletion loses history and is discouraged (R29, P26).
- When the media type locks manual rates, only access level 1A edits rates, discounts and surcharges (MM rule 10) (configurable).
- Discount cascade semantics are implied, not formalised (R6, gap 2): default compound, additive only by agency policy (confirm locally).
- Fixed agency fee periodicity is unspecified for generic plans (gap 6) (confirm locally).

## Calculations
- `media_line_cost`: gross per item by `calc_type` (`per_second`, `per_unit`, `per_thousand`, `per_action`, `package`) with `rate_minor`, `measure`, `spots`, `volume`, `package_minor` (0 unless package).
- `discount_cascade`: surcharges (percent or amount, accumulative flag), up to eight discounts `compound` or `additive`, `fee_base` none/net/gross/gross_after_first_discount, `fee_bps`, `fee_discount_bps`.
- `audience_metrics`: TRP, CPR, CPM and frequency against the planning target from book or ranking ratings.
- `credit_exposure`: credit limit vs open AR + approved unbilled + this plan; `requires_override_approval` drives P12.
- `plan_diff`: compare the saved revision with the approved revision before re-approval; any change to approved lines invalidates the prior approval.

```bash
python3 scripts/agency_tools.py discount_cascade < input.json
```
```json
{"currency": "MXN", "gross_minor": 36000000, "mode": "compound", "discounts_bps": [1000, 500],
 "surcharges": [], "fee_base": "net", "fee_bps": 1000, "fee_discount_bps": 2000}
```
- Not calculated by tools: VAT and local taxes (tables from the tax lead), FX rates, rate-card lookup, contract balances, vendor commission terms, package month split policy. They come from authoritative masters and AR/tax sources.

## Approvals and segregation of duties
- The planner prepares; only a user holding client-approval permission records client approval, and only a user with credit-limit authority approves an override (P10, P12). The planner who built the plan cannot approve it.
- Client approval, credit override and approve-for-billing each require an authenticated human approval bound to the payload digest (`payload_digest` tool), plan revision, schedule, currency and totals.
- Payment-term edits are restricted to access levels 1A/1B (R14); manual rates to 1A when locked.
- Any material change after approval (amount, dates, outlet, vendor, spots) invalidates the approval; re-run `plan_diff` and re-approve.

## Exceptions to escalate
- JobNumber closed, non-billable or billing client pending → `agency-job-lifecycle`.
- Plan exceeds credit limit → credit approver via `agency-budget-control`; no ordering until override.
- Plan exceeds client PO or reserve → `agency-budget-control` / `agency-contract-po`.
- Item without valid contract or rate card at its dates, or inactive masters on copy → `agency-rate-cards-contracts` / `agency-master-data`.
- Validity > 12 months or spanning 13 calendar months → split into separate plans with the planner.
- Foreign-currency plan without approved monthly reference FX → finance.
- Direct item whose sale differs from cost → planner corrects before approval.
- Change requested after client approval or ordering → `agency-plan-changes`.
- Billing requirement attachments missing → `agency-billing-requirements`.

## Return and handoff
Return `media_plan`, `schedule_register`, `item_pricing`, `plan_totals`, `objective_summary`, `approval_payload`, `billing_release`. Include tenant/client/job IDs, JobNumber, plan number and revision, schedule month/number, currency and FX reference, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Media planner. **Next:** `agency-budget-control`, `agency-media-buying`, `agency-client-billing`; `agency-production` in parallel for materials.

## Connectors and files
- Plans live in the agency ERP; no registry provider writes ERP plans. Use `google-ads`, `google-analytics` or `supermetrics` read-only for planning history; `composio` or host marketplace documents/email for client approval packs only through validated inner tools. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan --file plan.csv --out plan.json --tenant ID --client ID --job ID`.
