---
name: agency-campaign-activation
description: "Prepares and, after approval, launches digital campaigns via verified tools (Meta Ads, Google Ads, Zernio) with paused staging and readback. Use when a digital plan must go live."
---

# Digital Campaign Activation

This stage takes ordered digital plan items to the ad platforms: digital plan and insertion order → **activation proposal → paused staging → readback → approved enablement** → optimization, delivery reconciliation and invoice-based order adjustment. It owns the activation configuration, the platform IDs it verified and the record of uncertain writes. It never changes the plan or order economics, invents a platform receipt, or enables delivery without authenticated approval.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P35 Digital Planner steps 3–9, P26 taxonomy via media masters, R4 digital pricing, R15 currency, R27–R28 order cost and Google/Meta adjustment, §10.3 controls, §11 gap 11).

Agency policy: apply `approvals`, `connectors` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Launch the approved digital plan", "build the campaigns paused", `activar campaña`, `subir pauta digital`.
- Creating campaigns, ad sets/ad groups and ads from ordered digital items with the client taxonomy (`taxonomía`) naming and UTMs.
- Reading back a staged configuration before enabling it, or enabling a verified paused campaign after approval.
- Recovering from a timed-out create (uncertain write) without duplicating campaigns.

## Do not use when
- The digital plan, buy types or rates are still being defined → `agency-digital-planning`.
- The digital order is not issued or must be versioned → `agency-media-buying`.
- Changing bids, budgets or audiences on live campaigns based on performance → `agency-campaign-optimization`.
- Matching platform invoices to orders → `agency-delivery-reconciliation` and `agency-payables`.
- Connecting accounts or reviewing connector scopes → `agency-integrations`; budget authority questions → `agency-budget-control`.

## Required inputs
- **Blocking:** tenant_id, client_id, JobNumber, plan number, schedule and ordered item ids with order number/version (digital orders require an approved plan, P35 step 5).
- **Blocking:** platform account id, verified write permission for the exact tool, account currency and timezone matching the plan item currency (R15).
- **Blocking:** per item: platform, publication type, format and measure, buy type, planned clicks/impressions, gross rate, flight dates, ordered net cost (R27).
- **Blocking:** budget snapshot (authorized, spent, open commitments, reservations) from the authoritative store; atomic reservation by the host before any write.
- Client taxonomy templates (product, plan, item, creative, UTM) and external codes; creatives with rights and checksums; landing URLs; conversion events.
- Authenticated approval reference for the exact payload. Never ask for credentials in chat.

## Procedure
1. Discover live tools for the target platform and confirm they are write-capable and reviewed; a query-only server (reporting connectors) cannot create. Record tool name, version and account scope.
2. Read the account: identity, currency, timezone, billing status, existing campaigns with the same taxonomy prefix, conversion setup. Mismatch with the plan currency or client → blocked.
3. Load ordered items: only items whose order is issued and whose plan is approved are eligible (P35 steps 4–5). Unordered or rejected items are excluded and listed.
4. Render names with the client taxonomy templates per level and UTM URLs (media-masters P26); quarter tags `Q = floor((month + 2) / 3)` (media-masters rule 33). Names must reproduce the taxonomy exactly, because Google/Meta invoice lines are later matched to orders by taxonomy (P35 step 9, R28).
5. Budget check: run `budget_check` with the item or flight budget as `requested_minor`. `within_budget: false` → blocked; `atomic_reservation_required: true` means the host must reserve before writing. Platform daily/lifetime budgets must not exceed the ordered net cost for the flight.
6. Build the exact configuration per item: account, objective, budget and caps, dates, targeting, bids, placements, creative checksums, URLs, conversion events, status **paused**. Keep platform-side fields that the plan does not specify as explicit "platform default" entries, not guesses.
7. Hash the configuration with `payload_digest` and return it `pending_approval`. Creating a paused campaign is still an external write and needs the host gate.
8. After authenticated approval bound to that digest, execute through the reviewed tool with a persisted idempotency key scoped to tenant, account, action and revision. Checkpoint after each created object.
9. Readback: query each created object and compare name, status (paused), budget, dates, currency, targeting and URLs to the approved payload. Any drift → stop, report, do not enable.
10. Enablement is a separate approved action on the verified paused objects; record the platform's actual status after the call.
11. If a write times out or returns no ID, mark `uncertain`, search by idempotency key, external id or exact taxonomy name; never recreate blindly. Unresolved → stop for reconciliation.
12. Hand off platform IDs mapped to plan item and order numbers, so optimization, AdServer sync and invoice-based order adjustment (P35 steps 8–9) can join on them.

## Rules and locks
- No activation for items without an approved plan and an issued digital order (P35 step 5).
- Digital order cost defaults to the planned value; activation must not change it (R27). Economic changes go back to `agency-media-buying`.
- Taxonomy names are mandatory and immutable once invoices may reference them (P35 step 9, R28) (configurable per client).
- Item currency is fixed by contract or rate card; account currency must match (R15).
- Default every new object to paused where the platform supports it; enabling is a separate approval (agency policy).
- One idempotency key per object and revision; never retry a write unchanged after an authentication, schema or policy error.
- Platform receipts are recorded only when returned by the tool; a plan or proposal is never evidence of activation.
- Composio or Zapier actions are approved and validated at the inner tool and arguments, not the meta-tool (control contract).
- Taxonomy rules for Google/Meta matching are not documented in the reference (§11 gap 11) (confirm locally).

## Calculations
- `budget_check`: available = authorized − spent − open commitments − reservations; compare with the requested flight budget.
- `payload_digest`: SHA-256 over the canonical configuration; it binds content but never authorizes execution.

```sh
python3 scripts/agency_tools.py budget_check < input.json
```
```json
{"currency": "MXN", "authorized_minor": 80000000, "spent_minor": 21500000, "open_commitments_minor": 30000000, "reservations_minor": 5000000, "requested_minor": 25000000}
```
Expected: available 23500000, after request -1500000, `within_budget: false` → blocked.

Not calculated by tools: platform minimum budgets, auction bids, VAT on platform invoices, FX between account and plan currency, delivery forecasts. These come from the platform or agency policy.

## Approvals and segregation of duties
- The campaign manager prepares the configuration; the budget owner or account director approves the exact `payload_digest` (account, total, currency, dates, destination, revision, expiry).
- Paused creation and enablement are separate approvals unless agency policy documents a single combined approval.
- The preparer cannot approve their own payload; any change in budget, dates, targeting, URL or account invalidates the approval.

## Exceptions to escalate
- Only read/report tools available → return proposal and connector request to `agency-integrations`.
- Account currency, timezone or client mismatch → campaign manager and account director.
- Budget insufficient or no atomic reservation → budget owner via `agency-budget-control`.
- Plan item not ordered or order version changed since approval → `agency-media-buying`.
- Taxonomy template missing or name collision with an existing campaign → digital ops.
- Creative rights expired, policy rejection or broken landing URL → creative/traffic owner.
- Readback drift after creation → stop; campaign manager reviews before any enablement.
- Uncertain write that cannot be resolved by key or name → reconciliation with the platform; no retry.

## Return and handoff
Return `activation_proposal`, `taxonomy_names`, `preflight_results`, `external_ids`, `readback_report`, `execution_receipts`, `uncertain_actions`. Include tenant/client/job IDs, JobNumber, plan/schedule, order number/version, platform account id, revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified by readback), evidence references, blockers, approvals required and next stage.
**Owner:** Campaign manager. **Next:** `agency-campaign-optimization`, `agency-delivery-reconciliation`.

## Connectors and files
- Provider ids from `integrations/registry.json`: `meta-ads`, `google-ads`, `amazon-ads`, `zernio`, `synter`, `ryze` for platform writes when live discovery shows a reviewed write tool; `google-analytics` is read only; `supermetrics` can expose campaign write tools in some accounts, so use them only after live discovery and under the same approval gate; `composio` only with inner-tool approval. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan ...` for the approved digital plan. Without a write tool, deliver the configuration pack for manual upload and record the human-uploaded platform export as evidence.
