---
name: agency-period-close
description: "Prepare a month-end/job close checklist, lock proposal or authorized period correction. Do not overwrite posted entries in a closed period."
---

# Close and reopen accounting periods safely

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Period scope and status; reconciled orders/delivery; AP/AR/cash; accruals and rebates; expense/labor completeness; open exceptions; controller authorization.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Reconcile budget reservations/commitments, accepted delivery, supplier invoices, client invoices, credits, cash and rebates to canonical ledgers.

2. Check cutoff, uninvoiced delivery, unbilled milestones, FX/tax rules, labor and expense completeness. Record unresolved balances with owner and materiality under approved policy.

3. Prepare supported accruals and close evidence; unknowns do not become zero. Require controller approval for postings and the final lock.

4. If a late error arrives in a closed period, preserve original entries and propose an authorized reversal/adjustment. Reopening requires explicit controller permission and audit trail.

5. Return closed only with verified lock/ledger receipts. Otherwise provide a ready-to-review checklist and the exact blockers.

## Return and handoff

Return these named artifacts: `close_checklist`, `accrual_proposals`, `unresolved_balances`, `lock_proposal`, `adjustment_plan`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Controller. Next stage: completed or authorized adjustment workflow. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
