---
name: agency-budget-control
description: "Checks client PO, budget reserve and credit-limit headroom before client approval, keeping reservations apart from spend. Use when an estimate, plan or order needs a budget gate."
---

# Budget and Credit Control

This gate runs before a document consumes client authority: JobNumber, client PO or reserve and billing-client credit limit → **availability and credit check** → client approval (`Aprobación por Cliente`) → orders → billing. It owns the snapshot of disjoint balances (spent, open commitments, uncommitted reservations), the credit exposure check and the reservation proposal. It never reserves funds itself, never approves a credit override, and never sums amounts across currencies.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-17 PO control points, P-18 reserve control types, P-06 step 9 estimated investment, rules 20 and 59–62, jobs J8–J9) and [media-planning.md](references/erp/media-planning.md) (P05 step 8 budget/objective, P10–P12 client approval and credit override, 4.5 approval configuration, R30, R32, section 10.3).

## Use when
- "¿Hay saldo en la PO?", "check PO balance", "disponible del presupuesto", "reserva presupuestal" before approving an estimate or `pauta`.
- A plan or estimate is about to be approved by the client and the billing client has a credit limit (`Límite de Crédito`).
- Two or more documents compete for the same PO, reserve or job budget.
- Explaining why a plan cannot be ordered: not client-approved, or credit excess not yet approved.
- Converting reservations to commitments after orders are issued, or releasing unused reservations.

## Do not use when
- Creating or transferring the PO or setting up the reserve → `agency-contract-po`.
- Building the plan or estimate being checked → `agency-media-planning`, `agency-production-estimating`.
- Changing a committed plan or order → `agency-plan-changes`.
- Monitoring overdue receivables that feed exposure → `agency-collections`.
- Forecasting cash from approved documents → `agency-cash-forecast`.

## Required inputs
- Blocking: `tenant_id`, billing client, JobNumber, document id, revision, currency and amount (net of tax for PO checks).
- Blocking for PO/reserve: authorized amount, posted spend, remaining open commitments, uncommitted reservations, ledger revision. For reserves, control type and pool area.
- Blocking for credit: credit-limit level amount and its responsible approver, open receivables, approved-but-unbilled plans and estimates.
- Configuration: media approval circuit (`Circuito Aprobación Medios` none/restricted/strict), client approval period (whole plan or per `pauta`), credit-limit control for media/production on or off.
- Optional: plan budget/objective grid by vendor or zone and month, advance-payment contract balances.

## Procedure
1. Confirm the JobNumber is open and the document belongs to it; a closed job blocks new documents (media-planning 10.3).
2. Normalize every balance to one currency and one net/gross/tax basis from configured policy. If currencies differ or the FX policy or date is missing, stop instead of summing nominal amounts.
3. Build disjoint balances: spent = invoiced or delivered; open commitments = issued orders not yet delivered; reservations = client-approved documents not yet ordered. Never count one amount in two buckets.
4. Run `budget_check` for each PO, reserve pool area or job budget that governs the document. A negative `after_request_minor` blocks the proposal. For reserves under percentage control, the cap is 100% of the reserve (accounts-jobs rule 62).
5. If the billing client has a credit limit and credit control is on, run `credit_exposure` with open receivables, approved unbilled work and the request. The reference computes exposure as approved-but-unbilled plans and estimates plus unpaid invoices, adjusted for unapplied credit notes and advances (sign (confirm locally)) and checks it at client approval.
6. When `requires_override_approval` is true, the credit-limit level's responsible user must approve the excess before client approval (media-planning P12, R30); return `pending_approval` naming that role.
7. Respect the circuit order: credit override → client approval → order issuance. Orders cannot be issued on unapproved plans when the circuit is not None, nor over the limit without an override (media-planning 4.5).
8. Note the job's estimated-investment type: with "no budget", estimates may be pre-approved (accounts-jobs rule 20); treat the job budget as advisory unless the client is flagged with a mandatory job budget.
9. Items paid under advance-payment contracts consume the contract balance and are not invoiced again (media-planning R32); deduct them from availability, not from new billing.
10. For concurrent requests, require one transactional host reservation with compare-and-swap on the ledger revision and an idempotency key. Two individually affordable proposals may jointly exceed the PO.
11. After order issuance, propose converting the reservation to a commitment (PO consumption is recorded at order issuance, accounts-jobs rule 60); after delivery, propose converting the commitment to spend.
12. Release unused reservations only through audited host transitions; never silently reset balances.
13. Return the check, the proposal and blockers with the ledger revision used.

## Rules and locks
- The arithmetic check is a snapshot, not a lock; only the host store reserves.
- PO checks compare net-of-tax amounts (accounts-jobs rule 59).
- PO validation happens at client approval; consumption at order issuance (rule 60).
- Credit-limit approval comes before client approval; the approver is the user responsible for the credit-limit level (receivables 10.3).
- Credit control applies only under restricted or strict media circuits when enabled (configurable).
- Client approval scope is the whole plan or each monthly `pauta` (configurable).
- Never mix currencies; never assume two decimals.
- A negative balance after request blocks; an approved increase must reference revised PO authority and the payload digest.
- The exposure sign for unapplied credit notes and advances is (confirm locally).

## Calculations
- `budget_check`: inputs `authorized_minor`, `spent_minor`, `open_commitments_minor`, `reservations_minor`, `requested_minor`; read `available_minor`, `after_request_minor`, `within_budget`, `atomic_reservation_required`.
- `credit_exposure`: inputs `credit_limit_minor`, `ar_open_minor`, `approved_unbilled_minor`, `requested_minor`; read `exposure_after_minor`, `headroom_minor`, `within_limit`, `requires_override_approval`.

```bash
python3 scripts/agency_tools.py credit_exposure < input.json
```
```json
{"currency": "MXN", "credit_limit_minor": 300000000, "ar_open_minor": 180000000, "approved_unbilled_minor": 70000000, "requested_minor": 65000000}
```
Expected: `exposure_after_minor` 315000000, `headroom_minor` -15000000, `within_limit` false, `requires_override_approval` true.

- Not calculated by tools: FX conversion, tax stripping, which receivables count as open, and the credit-limit amount; take them from receivables, the billing-client master and the host FX source.

## Approvals and segregation of duties
- The finance controller or planner prepares the check; only a human holding credit-limit approval authority approves an override, and only a user with client-approval permission approves the document afterwards.
- Budget increases and PO transfers require finance approval bound to the `payload_digest`, revision, currency and amount.
- The preparer of the document cannot approve its own credit override.

## Exceptions to escalate
- Currency or basis mismatch → finance for FX and tax policy.
- PO exhausted or expired → `agency-contract-po` for transfer or amendment.
- Credit excess → credit-limit responsible approver; if refused, the account director renegotiates or splits the plan.
- Concurrent requests jointly exceeding the PO → controller decides priority.
- Ordering requested before client approval or override → refuse and route back.
- Ledger revision changed between check and approval → re-run the check.
- Reservation never consumed after validity → controller to release.

## Return and handoff
Return `budget_check`, `credit_check`, `reservation_proposal`, `balance_revision`, `blocking_exceptions`. Include tenant, billing client, job id and JobNumber, PO or reserve code, document id and revision, currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Finance controller. **Next:** `agency-media-planning`, `agency-media-buying`, `agency-production-estimating`.

## Connectors and files
- Provider ids: `xero` or `quickbooks` for open receivables and invoices, `stripe` for prepaid balances, `google-ads`, `meta-ads` or `amazon-ads` for platform spend caps and `supermetrics` for spend evidence (use read tools only; caps change only through agency-campaign-activation). Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
