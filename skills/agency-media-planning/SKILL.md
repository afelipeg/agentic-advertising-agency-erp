---
name: agency-media-planning
description: "Build a channel plan, allocation, forecast or revision from a validated brief and PO. Do not execute campaigns or commit supplier inventory."
---

# Plan media within commercial limits

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Validated brief; commercial terms; available budget; historical results with dates; channel quotes; audience/reach evidence; measurement design.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Translate objectives into measurable outcomes, audiences, channel roles, flight dates and named owners. Define the conversion event, attribution window and source of truth.

2. Use comparable historical data and dated quotes. Document uncertain CPM/CPC/reach/conversion assumptions and forecast ranges; do not imply guaranteed performance.

3. Allocate integer amounts within the authorized cap, separating media, agency fees, production, taxes and contingency. Identify direct-billed media independently.

4. Account for traditional media, OOH, retail and fixed placements with quote/evidence workflows where no connector exists. Include minimums and cancellation constraints.

5. Return a revisioned plan and approval proposal. Revalidate budgets and commercial scope after any revision; route approved allocations to buying and materials to production.

## Return and handoff

Return these named artifacts: `media_plan`, `allocation`, `assumptions`, `forecast_ranges`, `measurement_plan`, `approval_payload`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Media planner and client approver. Next stage: budget-control and media-buying; production in parallel. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
