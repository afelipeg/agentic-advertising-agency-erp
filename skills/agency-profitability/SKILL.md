---
name: agency-profitability
description: "Prepare a project margin, client profitability or working-capital analysis. Do not substitute campaign ROAS for agency financial profit."
---

# Analyze agency job profitability

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Contracted/recognized agency revenue; supplier and production costs; labor and expenses; rebate recognition; receivables/payables; managed media spend; accounting basis.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Define period and accrual/cash basis; reconcile revenue/cost mappings to ledger evidence. Include production, labor, expenses, fees, credits and recognized rebates.

2. Separate managed spend, pass-through amounts and agency revenue under configured principal/agent policy. Direct-billed media is not automatically revenue.

3. Use scripts/agency_tools.py margin for normalized same-currency agency revenue and cost. Report missing cost items separately instead of presenting an incomplete margin as final.

4. Build a bridge from planned to actual margin and identify unpaid receivables, disputed payables, concentration and cash exposure. Strong ROAS can coexist with agency losses.

5. Return financial findings with provenance and uncertainty. Proposed collections, price changes or cuts need their own approved workflows.

## Return and handoff

Return these named artifacts: `job_pnl`, `margin_bridge`, `managed_spend`, `cash_exposure`, `completeness_gaps`, `corrective_proposals`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Controller and account director. Next stage: period-close or scope revision. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
