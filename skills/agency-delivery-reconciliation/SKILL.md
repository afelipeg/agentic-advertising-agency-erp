---
name: agency-delivery-reconciliation
description: "Perform delivery verification or three-way matching across orders, supplier evidence and invoices. Do not rewrite supplier invoices to make the match pass."
---

# Reconcile ordered, delivered and invoiced media

Read [control-contract.md](references/control-contract.md) before acting. Apply its identity, money, trust, approval, runtime and checkpoint rules. These instructions do not supply a production runtime or authorize external actions. Use the host model; require host enforcement of privileges and approvals.

Read [operations-playbook.md](references/operations-playbook.md) for the complete document circuit, commercial rules and exceptions.

## Required inputs

Order/IO; platform or supplier delivery evidence; invoice/credit notes; units and dates; net/gross and currency; approved tolerance policy.

Inspect existing files and permitted read-only tools first. Ask only for missing material inputs; offer a draft/import path if the required MCP is unavailable. Never ask for credentials in chat.

## Procedure

1. Match canonical job/supplier/order/placement/date IDs and verify delivery units and acceptance evidence, including traditional media certificates where applicable.

2. Normalize currency, taxes, net/gross basis and unit definitions without overwriting originals. Unknown FX, tax or truncated data blocks matching.

3. Run scripts/agency_tools.py reconcile for same-currency monetary comparison using a documented tolerance. An order is authority, not proof of delivery.

4. Hold disputed invoices, overdelivery or short delivery; propose documented makegoods, credits or adjustments. Do not automatically accept an invoice merely because it is under the PO.

5. Return evidence-backed eligible amounts and exceptions to finance. Human authorization is required before a settlement/posting; preserve original and corrected facts separately.

## Return and handoff

Return these named artifacts: `match_result`, `discrepancies`, `evidence_links`, `payable_candidate`, `makegood_or_credit_requests`. Include job/client IDs, stage, revision, status, evidence references, assumptions, blockers, required approvals and next stage. Use `blocked` for missing prerequisites, `draft` for proposals and `completed` only for verified results. Keep calculations distinct from postings. Report receipts only when actually returned by a trusted connector.

Responsible owner: Reconciler and controller. Next stage: payables and client-billing. A parent orchestrator must validate the result and upstream revision before scheduling the handoff. Retain only deidentified client-scoped decisions and artifact references in memory.

## Tools and references

- Prefer already-enabled apps/plugins from the host marketplace when their reviewed capabilities satisfy this stage. Do not reconnect unnecessarily or assume identical tools across hosts.
- Read [provider-registry.json](references/provider-registry.json) to select documented connector options. Perform live discovery to establish available schemas, access and permissions. Installation connects no accounts.
- For local read-only calculations, run `python3 scripts/agency_tools.py TOOL < input.json` **from this skill directory**. Read [tool-contracts.json](references/tool-contracts.json) for exact fields. Available tools: plan_diff, budget_check, reconcile, flat_rebate, margin, payload_digest. Use only the applicable calculation; never manufacture missing numeric inputs.
- Output connector requests and approval proposals when execution is unavailable. Do not create imaginary tools or pass an unreviewed action through an aggregator.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.

Use [handoff-schema.json](references/handoff-schema.json) for the shared output envelope; domain artifact content needs a host-reviewed schema.
