---
name: agency-campaign-optimization
description: "Diagnose pacing or performance and propose bid, budget, audience or creative changes. Do not move fixed supplier commitments as if they were free platform budget."
---

# Optimize campaigns within approved limits

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Approved objectives and caps; actual account reports; conversion lag/window; spend and commitments; change history; supplier cancellation restrictions.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Read complete dated reports and distinguish missing conversions, tracking errors and reporting delay from true performance changes. Cite source windows and attribution definitions.

2. Compare pacing, costs, quality and conversion performance to plan. Do not infer causal improvement from one noisy short window.

3. Prepare bounded changes with hypotheses, expected effects and rollback criteria. Separate cancellable platform budget from guaranteed TV/OOH/supplier orders.

4. Recheck PO headroom and contractual restrictions. Get approval for money/bid/budget changes and validate the exact tool schema and account scope before execution.

5. Record verified changes and evaluate after the declared window. Use controlled tests where feasible; retain the original baseline and report inconclusive results honestly.

## Return and handoff

Return these named artifacts: `diagnostic`, `optimization_proposal`, `experiment_plan`, `constraint_check`, `verified_change_receipts`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Performance lead and budget approver. Next stage: budget-control, activation or delivery-reconciliation. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
