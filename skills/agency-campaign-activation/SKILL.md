---
name: agency-campaign-activation
description: "Prepare campaign configuration or activate a campaign with approved settings and verified write access. Do not use a query-only MCP server for campaign creation."
---

# Activate approved campaigns safely

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Approved plan and assets; valid rights; authorized account; current budget reservation; tracking and destination QA; exact configuration; authenticated approval.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Discover actual tools and read account identity, currency, timezone, billing status, existing campaigns and conversion configuration. Block any mismatch or absent write permission.

2. Build an exact revisioned configuration: account, objectives, budget/caps, dates, targeting, bids, creative checksums, URLs and conversion events. Default new drafts to paused where supported.

3. Validate rights, tracking, landing pages, platform policy, balance and approvals. Creating a paused campaign is still an external write and requires the applicable host gate.

4. Execute only after host approval using persisted idempotency and checkpointed steps. Record verified platform IDs and actual state; require explicit approved enablement.

5. If creation times out, mark uncertain and query by key/identifier before retrying. Never create a second campaign blindly; unavailable tooling yields a proposal, not fictional activation.

## Return and handoff

Return these named artifacts: `activation_proposal`, `preflight_results`, `external_ids`, `execution_receipts`, `uncertain_actions`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Media operator and budget approver. Next stage: campaign-optimization and delivery-reconciliation. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
