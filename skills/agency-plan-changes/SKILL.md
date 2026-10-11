---
name: agency-plan-changes
description: "Process daily retail or other media-plan revisions, compare approved and proposed versions, assess downstream commercial and creative impact, and prepare incremental actions. Use for budget transfers, placement/date/creative changes, urgent retail updates or concurrent revisions. Do not rebuild completed jobs or treat budget-neutral changes as automatically authorized."
---

# Revise daily plans and dependent documents

Read [control-contract.md](references/control-contract.md), then the revision procedure in [operations-playbook.md](references/operations-playbook.md). Prefer the host's enabled marketplace apps, then reviewed MCP options in [provider-registry.json](references/provider-registry.json). This skill prepares changes; the host enforces locks, approvals, budgets, runtime and execution.

## Required inputs

Obtain the authorized change request, effective date/time/timezone, retail promotion/SKU/store/channel scope, requested deadline, current approved plan revision, proposed revision, canonical line IDs, current account state, PO/balance revision, actual remaining commitments, orders, assets/rights, billing/close status, and client/agency approval policy. Retrieve trusted current snapshots; a client-editable sheet cannot lower the authoritative commitment balance. Distinguish promotion content from personal customer data.

## Procedure

1. Read the current approved/executed baseline and log who requested which change and when. If the request references an old revision, stop the write and rebase its proposal on the latest baseline; do not overwrite another coordinator's changes.
2. Compare lines by stable line ID, not row position. Identify adds, removals and changes to amounts, account, supplier, currency, flights, store/geography, product/promotion, targeting, rate, bids, creative version, tracking and destination. Preserve unchanged lines and completed receipts. Run `python3 scripts/agency_tools.py plan_diff < normalized-input.json` from this directory for the **limited financial line comparison** described in [tool-contracts.json](references/tool-contracts.json). Add creative/targeting/promotion diffs separately; that calculator cannot inspect them.
3. Build an impact register for every affected line: PO headroom and uncommitted reservation, noncancellable/remaining order exposure, supplier cutoffs, delivery already incurred, production rework, creative rights/QA, analytics labels, invoice/credit implications, rebate eligibility and accounting period. Totals that net to zero can still change scope, supplier liability, country, audience or tax treatment.
4. Keep money separated by currency and configured minor-unit exponent. Do not make cancelled exposure available until a trusted supplier/platform receipt verifies its release. A new increase may need temporary extra headroom while the old commitment remains. For invoiced or closed lines propose linked cancellation/credit/replacement/adjustment documents; never rewrite posted history.
5. Prepare a minimum incremental action set in dependency order: new material QA/approval, revised plan approval, atomic balance reservation, approved cancellable reductions, verified release, replacement/addition, tracking readback, order/billing amendments and notifications. If current headroom cannot cover the replacement, obtain approved cancellation and verified release before reserving the replacement, or obtain verified temporary additional authority; never reserve against an expected release. Mark risky intermediate states and a compensating plan; a rollback may itself need approval and may be impossible for delivered/noncancellable inventory.
6. Present one consolidated review pack with old/new values, currency deltas, remaining exposure, changed assets, destinations, relevant rights, exact connector actions, expected receipts, approval digest/revision, deadline and owner. Do not hide operations inside a broad batch meta-tool. Budget-neutral changes still require the applicable scope/asset/write approvals. Urgency never waives a gate.
7. After authenticated approval, let the host compare-and-swap the current revision, reserve funds atomically and execute allowed actions with persisted idempotency keys. Serialize overlapping PO/account/order changes. Parallelize only independent reads/preparation. Checkpoint each verified result; if a write times out, mark uncertain and query outcome before retrying.
8. Read back actual live account/order state. Record verified changes and unresolved divergence between proposed, approved and executed versions. Do not mark the revision executed when only some steps succeeded. Update downstream handoffs and send communications only after the relevant approved action. Save deidentified revision history in client-scoped memory.

## Return and handoff

Return `baseline_revision`, `proposed_revision`, `line_diff`, `currency_deltas`, `commitment_exposure`, `dependency_impacts`, `incremental_actions`, `approval_pack`, `verified_receipts`, `blocked_actions`, `checkpoint`, and `timing_breakdown`, alongside identity, evidence and status. Report preparation, waiting-for-input, waiting-for-approval, tool execution and recovery times separately. The reported 48-hour process delay is an unverified user baseline until actual timestamps confirm it; do not claim an achieved speedup from a dry run.

Responsible owner: media coordinator; commercial/controller approvers and producer join affected changes. Handoff to budget-control, media-buying, production, activation, reconciliation, billing, rebates and close **only where affected**. Provide a operator-ready change pack if write tooling or runtime controls are unavailable.

## Blockers

Block stale revisions, missing authoritative balances, undefined FX/tax/tolerance, commitment removal without cancellation evidence, unsupported tool writes, absent rights or approval, locked period edits and unknown execution outcomes. Name the missing input and responsible owner. Never reset a token/cost/deadline budget when resuming the revision.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
