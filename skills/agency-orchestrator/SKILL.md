---
name: agency-orchestrator
description: "Run or resume a complete agency job, route specialist work, or identify the next operational stage. Do not use for a standalone ad metric query."
---

# Coordinate the agency workflow

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Authorized brief; tenant/client/job IDs; current stage receipts and revisions; deadline/token/cost ceilings; available tools and model profiles.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Build a dependency graph from the actual commercial scope. Include client PO, agency-billed versus direct-billed media, production, expenses, reconciliation, tax and close. Skip stages only with a recorded reason.

2. Inspect checkpoints, upstream revisions and live tool access. Dispatch only independent read-only work concurrently; serialize mutations for the same PO, account, ledger and period.

3. Use one shared budget and client-scoped memory across all specialist agents. Have each specialist return evidence and structured artifacts; join by canonical IDs rather than narrative agreement.

4. Pause before financial commitments or external writes for an authenticated human approval bound to the exact revision. Reserve funds atomically in the host before execution.

5. On failure resume the verified checkpoint. Route ambiguous tool outcomes to reconciliation, missing evidence to the responsible owner, and completed delivery to finance before closing. Do not call the whole job complete because media launched.

## Return and handoff

Return these named artifacts: `job_state`, `dependency_graph`, `task_assignments`, `blockers`, `approval_requests`, `checkpoints`, `next_stage`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Account director and controller. Next stage: onboarding, integrations, then dependency-ready stages. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
