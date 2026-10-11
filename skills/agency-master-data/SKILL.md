---
name: agency-master-data
description: "Map clients, suppliers, brands, ad accounts, projects and cost centers to canonical records or resolve duplicate identities. Do not merge clients based only on a matching name."
---

# Normalize agency master data

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Existing master records; legal/tax identifiers via protected lookup; tenant scope; authorized account lists; currencies and configured exponents; cost-center and period definitions.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Scope every lookup by tenant and client. Verify that each ad account, GA property, supplier and project belongs to the intended relationship using trusted records.

2. Deduplicate using stable IDs and legal identity evidence. Keep aliases and provenance; propose merges for steward review without deleting originals.

3. Record currency exponent, timezone, chart-of-accounts mappings, tax jurisdiction/configuration and period lock status. Treat missing settings as blockers for money operations.

4. Design cache and memory namespaces with tenant/client/account and permission scope. Never reuse another client’s cached answers or connector credentials.

5. Return canonical IDs and an access matrix; stage drafts may use pending identities, but commitments/postings cannot.

## Return and handoff

Return these named artifacts: `canonical_mapping`, `duplicate_candidates`, `permission_matrix`, `currency_policy`, `unresolved_identities`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Data steward. Next stage: contract-po and downstream stages. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
