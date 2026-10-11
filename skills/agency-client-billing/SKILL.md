---
name: agency-client-billing
description: "Derive a client invoice or billing schedule from contract, PO and accepted delivery. Do not invoice direct-billed platform spend as agency revenue."
---

# Prepare client billing and receivables

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Commercial terms; client PO; accepted delivery/milestones; fee/markup/tax policy; direct-billing flag; supplier costs; previous invoices/credits.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Identify whether media is agency-billed pass-through, reseller/principal or client direct-billed. Follow the configured accounting policy rather than treating managed spend as agency fees.

2. Calculate contracted fees, markups, retainers or milestones on the correct eligible base. Remove previously billed amounts and apply authorized credits without double billing.

3. Check invoice entity, currency, PO coverage, accepted deliverables, tax configuration and client submission requirements. Block missing tax/legal settings.

4. Prepare the invoice and supporting delivery pack; bind approval to amount, revision and recipient. Drafting, posting and emailing are distinct gated actions.

5. Return a receivable draft unless a finance connector verifies issuance. Link subsequent payments and credits by invoice ID; do not assume billed means collected.

## Return and handoff

Return these named artifacts: `billing_draft`, `po_consumption`, `receivable_schedule`, `fee_calculation`, `billing_exceptions`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Billing operator and client/finance approver. Next stage: cash-settlement and profitability. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
