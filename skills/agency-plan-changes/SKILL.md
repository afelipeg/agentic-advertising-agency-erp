---
name: agency-plan-changes
description: "Revises approved or ordered media plans as new versions: diff vs baseline, locks on ordered or billed spots, rescheduling and order versions. Use for changes after approval."
---

# Plan Changes

This stage handles every change to a plan once it has an approved revision or ordered spots: approved baseline → change request → new plan revision → re-approval where required → order modification (new version or in-place) → downstream updates. It owns the revision record, the line diff, the lock assessment and the incremental action pack. It never rewrites billed or controlled spots, deletes history to simplify a plan, or executes order changes without approval.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-planning.md](references/erp/media-planning.md) (P09 revisions, P13–P15 reject/recover/cancel, P16 order rate validation, P17–P21 order modification and add-to-order, P25 rescheduling, P26 delete, P29 re-rate, P30 control locks, P34 item locks, R2, R17, R26, R27, R29, §4.3 spot state machine and locks, §10.3). [media-buying.md](references/erp/media-buying.md) (P-OP-03, P-OP-05, P-OP-06, P-OP-08, §4.4 order lifecycle, BR-O-04 to BR-O-10).

Agency policy: apply `approvals`, `commercial` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- A client or agency requests changes to an approved or ordered plan: spot counts, dates, program, duration, publication type, billing type, direct/indirect, contract, material, rate or vendor.
- Dropped spots after control must be rescheduled (`Reprogramar avisos`), or rejected spots recovered (`Recuperar avisos`).
- An ordered spot must be cancelled (`Anular orden`) or new spots pushed into an existing order (`Agrega Avisos a Orden`).
- Pauta-vs-order rate differences need explicit validation, or a re-rate from post-evaluation must flow to orders.
- Concurrent or daily retail revisions must be rebased on the latest approved revision.

## Do not use when
- Building a new plan or a first approval → `agency-media-planning`.
- Issuing first orders, sending, closing or reopening orders → `agency-media-buying`.
- Matching monitoring data and declaring spots dropped → `agency-transmission-control`.
- Invoice-based repricing of digital orders → `agency-digital-planning`.
- Credit notes or rebilling for billed spots → `agency-client-billing`; supplier differences at order close → `agency-delivery-reconciliation`.
- PO or reserve headroom decisions → `agency-budget-control`.

## Required inputs
- Blocking: tenant, client, JobNumber, plan number, current approved revision and the latest saved revision (P09).
- Blocking: authenticated change request with requester, reason category (client/outlet/agency, from modification-reason masters), effective date and deadline.
- Blocking: per spot state from the ERP (planned, client-approved, ordered, controlled, approved-for-billing, billed, rejected) and order number/version, sent or unsent (§4.3, §4.4).
- Authoritative PO/reserve balances, spent, open commitments and reservations; never a client-editable sheet.
- Contracts and rate cards valid at the new dates; materials and royalty validity for new dates.
- Approval configuration (circuit, approval period) and who may unlock ordered items.

## Procedure
1. Load the approved baseline revision and the current latest revision. If the request was drafted against an older revision, stop and rebase it on the latest; never overwrite another planner's changes (P09).
2. Normalize lines by stable plan + schedule + item id and run `plan_diff` (baseline vs proposed). Add non-financial diffs separately: program, duration, material, publication type, billing type, direct/indirect, contract, dates. The tool flags removed commitments, amounts below commitment and changed committed dimensions.
3. Classify every affected spot by state and apply locks (§4.3): billed spots cannot be modified or rescheduled (P25); controlled spots are immutable (P30 rule); items with client invoice or registered vendor invoice cannot be deleted (P34); vendor and contract cannot change once ordered.
4. Route by state: unordered spots change in the plan directly (P19), never leaving a program with zero spots; unordered programs may be deleted only with a revision reason, and deletion is unrecoverable, so prefer rejection (P26, R29).
5. Unapproved spots the client declines are rejected, not deleted; rejected spots can be recovered to their prior state (P13, P14). Ordered spots cannot be rejected directly: annul the order first, then decide reject (recommended), cancellation request to vendor and revision bump (P15, P18).
6. For ordered spots needing structural changes, prepare an unlock (lock flag red → green) with add-to-order on; changes to program, duration, spot count, publication type, billing type, direct/indirect and contract flow to the related order (P17, P20). Rate, discounts, notes and vendor change on the order side only (BR-O-04); order rate edits only on indirect items for clients without in-system audits (BR-O-05); a new vendor must be linked to the outlet (BR-O-10).
7. Decide order versioning: if the order was sent, the change creates version n+1 with an "annuls and replaces" legend; if unsent, it may be re-issued with the same number and version (P17, BR-O-06). Item numbers are never reused (BR-O-07).
8. Reschedule dropped spots only after control: remove the dropped spot and add a replacement on the new day in the same program, save with revision reason (P25). The original shortfall stays on record until the makegood is verified.
9. Rate or negotiation change mid-flight: create a new item from the change date rather than editing the old one (R17). Date moves keep start ≤ first spot and end ≥ last spot, and whole-week moves preserve weekdays; warn on items left without contract or rate card (R2, R26).
10. Check money: keep currencies separate; run `budget_check` with authoritative balances for any increase. Do not count a cancellation as released headroom until the vendor's cancellation is verified; if headroom is short, sequence approved cancellation and verified release before reserving the replacement, or obtain temporary authority.
11. Build one approval pack: baseline vs proposed revision, line and spot diff, lock report, currency deltas, order versions to issue or annul, rate differences requiring validation (R27, P16), revision reason, affected downstream stages and deadline. Budget-neutral changes still need scope approval; re-approval by the client is required when the circuit demands it (P09, P10).
12. After authenticated approval, the host compare-and-swaps the revision, saves with reason (P09) and executes order modifications with idempotency keys. Read back plan and order versions; mark executed only the steps verified. A timeout on a write is `uncertain` until the order state is read back.

## Rules and locks
- Every save with revisions enabled records a reason and a new revision; the client-approved revision is the one to execute (P09).
- Billed spots: no modification, rescheduling or deletion (P25, §4.3).
- Controlled spots are immutable; reschedule only via a replacement spot (P25, P30).
- Ordered items are locked; vendor and contract are fixed once ordered; unlocking is explicit and audited (P17, §4.3).
- A program cannot be left with zero spots (P19, P25).
- Rejection over deletion; deleted spots cannot be recovered (R29, P26).
- Ordered spots must be released by annulling or modifying the order first (P15, P-OP-06).
- Sent orders change only through a new version that annuls and replaces the previous one (BR-O-06).
- Pauta-vs-order rate differences require explicit validation before the order is accepted (R27).
- Order reopen requires no supplier invoice and month schedules not closed (BR-O-09).
- Bulk negotiation change applies only to plans with open, unbilled orders (P21) (configurable by release).
- Closed or billed periods are corrected with linked credits or adjustments, never by editing posted history.

## Calculations
- `plan_diff`: baseline vs proposed lines (`line_id`, `account_id` = outlet, `supplier_id`, `channel`, `currency`, `amount_minor`, `committed_minor` = ordered amount, dates). Blockers `commitment_removed`, `below_commitment`, `commitment_rewritten`, `committed_dimensions_changed` stop silent edits.
- `budget_check`: available = authorized − spent − open commitments − reservations; a negative `after_request_minor` blocks the increase.

```bash
python3 scripts/agency_tools.py plan_diff < input.json
```
```json
{"before": [{"line_id": "P1042-S11-IT001", "account_id": "OUT-0423", "supplier_id": "SUP-12", "channel": "tv",
  "currency": "MXN", "amount_minor": 3600000, "committed_minor": 3600000, "start_date": "2026-11-01", "end_date": "2026-11-30"}],
 "after":  [{"line_id": "P1042-S11-IT001", "account_id": "OUT-0423", "supplier_id": "SUP-12", "channel": "tv",
  "currency": "MXN", "amount_minor": 2400000, "committed_minor": 3600000, "start_date": "2026-11-01", "end_date": "2026-11-30"}]}
```
- Not calculated by tools: spot-state locks (read from the ERP), creative/material and royalty impacts, cancellation fees, valuation of dropped-spot differences (gap 14), taxes and FX. They come from authoritative records and the responsible owners.

## Approvals and segregation of duties
- The media planner prepares; the account director confirms scope; the client approves when the circuit requires re-approval; the media buyer issues order versions.
- Unlocking ordered spots, annulling orders, issuing new versions, cancellation requests to vendors and any amount change require an authenticated human approval bound to the payload digest (`payload_digest` tool), revision and order version.
- The preparer cannot approve; urgency never waives a gate.

## Exceptions to escalate
- Request based on a stale revision or conflicting concurrent edits → rebase; planner owner.
- Change touches billed spots → `agency-client-billing` for credit/rebill; no edit.
- Change touches controlled spots or dropped spots without control → `agency-transmission-control`.
- Order cannot reopen (supplier invoice registered or month closed) → `agency-payables` / `agency-period-close`.
- Increase exceeds PO/reserve or credit headroom → `agency-budget-control`.
- New dates fall outside contract, rate card or royalty validity → `agency-rate-cards-contracts` / `agency-production`.
- Vendor change to a vendor not linked to the outlet → `agency-master-data`.
- Write outcome uncertain → query by order number/version before any retry.

## Return and handoff
Return `baseline_revision`, `proposed_revision`, `line_diff`, `lock_report`, `currency_deltas`, `order_version_actions`, `approval_pack`, `verified_receipts`, `blocked_actions`. Include tenant/client/job IDs, JobNumber, plan number and revision numbers, schedule months, order numbers and versions, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage. Report preparation, approval waiting and execution times separately.
**Owner:** Media planner and account director. **Next:** `agency-media-buying`, `agency-budget-control`, `agency-transmission-control`, `agency-client-billing`, `agency-delivery-reconciliation` (only where affected).

## Connectors and files
- Plan and order revisions live in the agency ERP; no registry provider writes them. Read digital delivery with `google-ads` or `supermetrics` when a change depends on actuals; use `composio` or host marketplace documents/email only through validated inner tools for approval packs. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan|broadcast-order --file SOURCE --out OUT.json --tenant ID --client ID --job ID` for baseline and proposed exports.
