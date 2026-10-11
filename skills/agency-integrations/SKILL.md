---
name: agency-integrations
description: "Inventory or configure MCP connectors for an agency workflow, verify capabilities, or diagnose missing ad-account/document/finance access. Do not request secrets in chat."
---

# Connect required accounts and inputs

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Host/client type; desired stages; provider choice; tenant/client/account IDs; existing MCP inventory; authorized user; approved tool/access policy.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Prefer enabled marketplace apps/plugins first, then read references/provider-registry.json and discover the host’s actual MCP tools. Distinguish first-party MCP, official API, third-party aggregator and imported-file workflows.

2. Map required reads/writes by stage. Google Ads query MCP does not imply campaign mutation; Supermetrics capabilities must be discovered; finance and traditional media may require imports or separate connectors.

3. Offer official connectors or Synter, Ryze, Supermetrics and Composio according to access needs. Treat unverified Ryze endpoint/tools as a gap pending primary verification. Avoid vendor lock-in.

4. Have the user authenticate through the provider/host OAuth or backend credential store, never by pasting keys into model context. Verify selected account, timezone, currency, actual scopes and schema with a permitted read.

5. Approve the least necessary tool allowlist and host gates. For Composio inspect inner actions and deny broad workbench/bash by default. Return documented, connected, authenticated, read-tested and write-approved statuses separately; no connection is implied by installing skills.

## Return and handoff

Return these named artifacts: `capability_inventory`, `connection_requests`, `access_matrix`, `schema_review`, `wiring_plan`, `gaps`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Workspace owner and security/finance administrators. Next stage: onboarding or the requesting stage. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
