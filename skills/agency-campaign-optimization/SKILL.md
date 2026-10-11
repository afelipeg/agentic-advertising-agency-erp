---
name: agency-campaign-optimization
description: "Diagnose pacing and performance against the approved plan (planned vs actual, objective deviation, TRP, CPR, CPM, frequency) and propose bounded bid, budget, audience or creative changes within fixed commitments. Use for in-flight reviews. Do not move ordered or contracted spend as if it were free platform budget."
---

# Campaign Optimization

This stage runs while campaigns are live: activation and orders → **diagnosis of pacing and performance vs plan objectives → bounded change proposals** → approved changes through activation tools or plan changes, then delivery reconciliation. It owns the diagnostic, the optimization proposal and the experiment record. It never rewrites committed order lines, contract caps or rate cards, and never executes a bid or budget change without authenticated approval.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P05 step 8 budget/objective, P34 objective widget, P35 step 7 planned vs actual, P28–P29 post-evaluation and re-rate, P33 distribution analysis, R19 audience metrics, R27–R28, R36 share control, §11 gaps 5, 14).

## Use when
- "How is the campaign pacing?", "are we on TRP target?", `avance de pauta`, `desvío vs objetivo`, `planificado vs real`.
- Reviewing digital delivery (clicks, impressions, CTR, CPC) or offline post-evaluation (TRP, CPR, CPM, reach, frequency) against the plan objective.
- Proposing bid, budget, audience, placement or creative rotation changes with rollback criteria.
- Checking whether a proposed shift breaks an order commitment, contract cap or share restriction.

## Do not use when
- Launching or creating campaigns → `agency-campaign-activation`.
- Changing ordered spots, durations or vendors in the plan → `agency-plan-changes`.
- Verifying offline airings → `agency-transmission-control`.
- Budget authority, reserves or PO headroom decisions → `agency-budget-control`; contract terms → `agency-rate-cards-contracts`.
- Margin or client profitability analysis → `agency-profitability`; management dashboards → `agency-management-reporting`.

## Required inputs
- **Blocking:** tenant_id, client_id, JobNumber, plan number and approved revision with objectives (investment, TRP, reach) and planning target (P34).
- **Blocking:** dated actuals with source, window, timezone, currency, attribution and conversion lag definitions; for offline, licensed ratings with universe.
- **Blocking:** committed amounts per line: ordered net, contract caps, cancellation terms; budget snapshot (authorized, spent, open commitments, reservations).
- Change history and prior experiments; platform policy limits.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Freeze the baseline: approved plan revision, objectives and line commitments; record report windows and data completeness. Treat missing data as missing, not zero.
2. Separate measurement problems (tracking gaps, reporting delay, conversion lag) from performance changes before diagnosing.
3. Pacing: compare spend to date against ordered net and flight elapsed per line; for digital buy types (CPC etc.), actuals recompute the final rate on both sale and purchase only after the order is issued (P35 step 7).
4. Audience performance: run `audience_metrics` with net cost, universe and licensed spot ratings to get TRP, impressions, CPR, CPM and frequency (when reach is supplied). Formulas are standard industry definitions; only Frequency = TRP / Reach is documented (R19, §11 gap 5).
5. Objective deviation: deviation = objective − plan/actual for investment, TRP and reach on the planning target (P34). Report by outlet or criterion as in distribution analysis (P33).
6. Classify each line: platform budget that is cancellable vs committed (issued orders, guaranteed TV/OOH, contract-capped). Only cancellable budget is movable.
7. Draft bounded changes with hypothesis, expected effect, measurement window and rollback criterion. Offline changes become plan revisions (rescheduling, re-rate from post-evaluation, P29) routed to `agency-plan-changes`.
8. Constraint check with `plan_diff` (before = approved lines, after = proposed lines): any `commitment_removed`, `below_commitment`, `commitment_rewritten` or `committed_dimensions_changed` blocker stops the proposal.
9. Budget check with `budget_check` for any increase; `within_budget: false` → blocked and routed to the budget owner.
10. Check contract share and cap effects for moves between outlets (R36); a breach is escalated, not optimized away.
11. Hash the proposal with `payload_digest` and return `pending_approval`. Approved platform changes execute through `agency-campaign-activation` tools with readback; record verified changes only.
12. Evaluate after the declared window against the frozen baseline; report inconclusive results honestly and keep the original baseline.

## Rules and locks
- Never reduce, move or cancel ordered or contracted commitments through optimization; those go through plan changes and order versioning (media-buying BR-O-04, BR-O-06).
- Controlled and billed spots are immutable; billed spots cannot be rescheduled (media-planning P25, P30).
- Digital order cost changes require an order modification with a new version (P35 step 6).
- Google/Meta billable amounts are realigned from invoice lines only through the invoice adjustment process, not from platform reports (R28).
- Planning target and book define the objective; do not switch targets to make deviation look better (P34).
- Ratings must come from licensed sources; no model-estimated ratings (R19).
- One noisy short window is not evidence of causal improvement (agency policy).
- Valuation of dropped spots is undocumented (§11 gap 14) (confirm locally).

## Calculations
- `audience_metrics`: `net_cost_minor`, `universe`, `spots[]` with `rating_hundredths`, optional `reach_hundredths` → TRP, impressions, CPR, CPM, frequency.
- `budget_check`: headroom for any increase.
- `plan_diff`: approved vs proposed lines; blockers on committed lines.

```sh
python3 scripts/agency_tools.py audience_metrics < input.json
```
```json
{"currency": "MXN", "net_cost_minor": 45000000, "universe": 5000000, "spots": [{"spot_id": "S1", "rating_hundredths": 350}, {"spot_id": "S2", "rating_hundredths": 420}], "reach_hundredths": null}
```
Expected: TRP 770 hundredths (7.70), impressions 385000, CPR 5844156, CPM 116883, frequency null without reach.

Not calculated by tools: attribution models, conversion lag adjustments, statistical significance, reach curves, platform auction forecasts. State the source or mark as unavailable.

## Approvals and segregation of duties
- The performance lead prepares diagnostics and proposals; the budget owner or account director approves any bid, budget or audience change bound to its `payload_digest`.
- Offline plan revisions follow `agency-plan-changes` approvals; client-facing objective changes need client approval.
- The preparer cannot approve their own proposal; any material change invalidates approval.

## Exceptions to escalate
- Tracking or reporting gap larger than the evaluation window → analytics owner; pause conclusions.
- Proposed shift touches committed spend → buying director via `agency-plan-changes`.
- Budget increase beyond authorization → budget owner via `agency-budget-control`.
- Contract cap or share restriction at risk → buying director via `agency-rate-cards-contracts`.
- Objective deviation beyond agency threshold mid-flight → account director and client.
- Ratings unavailable or methodology changed → research owner; report missing.
- Platform change outcome uncertain → `agency-campaign-activation` reconciliation; no retry.

## Return and handoff
Return `diagnostic`, `objective_deviation`, `optimization_proposal`, `experiment_plan`, `constraint_check`, `verified_change_receipts`. Include tenant/client/job IDs, JobNumber, plan/schedule, order numbers/versions, report windows and sources, revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Performance lead. **Next:** `agency-campaign-activation` (approved platform changes), `agency-plan-changes` (offline revisions), `agency-budget-control`, `agency-delivery-reconciliation`.

## Connectors and files
- Provider ids from `integrations/registry.json`: `google-analytics`, `supermetrics`, `meta-ads`, `google-ads`, `amazon-ads`, `synter`, `ryze` for reads; writes only through `agency-campaign-activation` with reviewed tools; `meridian` for media mix context where available. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan ...` for the baseline and `--kind rating` for post-evaluation ratings.
