---
name: agency-contract-po
description: "Translate an approved client agreement or purchase order into enforceable scope, billing and budget rules. Do not treat an unsigned quote as spending authority."
---

# Validate contracts and client POs

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Contract and amendments; client PO; authorized signer evidence; supplier agreement; billing entity; currency, validity dates, tax/fee terms and cancellation rules.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Extract PO amount, currency, covered dates, deliverables, billing route, fees, markups, payment milestones, tax basis and acceptance requirements with citations.

2. Check signatures, revision and entity against trusted approval records. Block contradictory amendments, expired POs or unapproved increases.

3. Separate client authorization from supplier commitments and platform budgets. Define caps by job, channel and period where the agreement requires them.

4. Flag cancellation windows, guaranteed inventory, minimums, makegoods and rebates/discount ownership. Do not assume all spend is cancellable or all rebates belong to the agency.

5. Return normalized terms and exceptions. Require human/legal/finance resolution for ambiguity; do not create or send binding documents.

## Return and handoff

Return these named artifacts: `commercial_terms`, `po_limits`, `billing_route`, `fee_rules`, `cancellation_terms`, `scope_exceptions`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Commercial owner and controller. Next stage: budget-control and media-planning. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
