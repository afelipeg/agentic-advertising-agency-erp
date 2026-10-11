---
name: agency-rebates
description: "Evaluate supplier volume rebates, agency commissions or client rebate returns under documented contracts. Do not assume a flat percentage for tiered agreements."
---

# Calculate and allocate rebates

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Rebate contract; eligible net spend/delivery; credits and exclusions; period; attainment tiers; client-return terms; recognition policy and supplier confirmation.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Read eligibility, attainment period, supplier grouping, net/gross basis, exclusions, credit treatment and ownership directly from the agreement.

2. Distinguish flat, marginal-tier and retroactive-tier rates. Use scripts/agency_tools.py flat_rebate only for a documented flat rate; do not approximate other structures with it.

3. Normalize qualifying spend and reconcile returns/credits. Calculate in minor units with documented rounding, then allocate client return and agency retained share so the amounts sum exactly.

4. Separate forecast accrual from earned, confirmed and collected rebate. Resolve ambiguous recognition policy with the controller.

5. Return calculations and proposed accrual/credit documents. Approval and real connector receipts are required for posting or settlement.

## Return and handoff

Return these named artifacts: `eligible_base`, `rebate_calculation`, `client_return`, `agency_retained`, `accrual_proposal`, `exceptions`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Commercial finance and controller. Next stage: client-billing, profitability and period-close. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
