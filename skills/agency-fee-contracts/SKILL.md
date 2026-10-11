---
name: agency-fee-contracts
description: "Translate fixed fees, hourly fees, retainers or media commissions into an evidence-backed billing schedule. Use for recurring agency remuneration; do not use an unspecified percentage base or recognize advances as revenue automatically."
---

# Calculate fee and retainer schedules

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Signed service agreement; fee type/base; currency; period; hour/rate approvals; milestone/retainer schedule; billing route; scope revisions; tax and recognition policy.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Classify fixed fee, retainer, time-and-materials, percentage-of-eligible-spend or hybrid terms. Record exact base, exclusions, cap, minimum and period. Direct-billed media may affect a fee base only if the contract says so.

2. Reconcile approved worked hours to contractual rates and billable categories; distinguish internal labor cost and client selling rate. Keep disputed/unapproved hours out of automatic issuance.

3. Build a period/milestone schedule including prior billed amounts, authorized credits, scope changes and prorating rules. Do not infer installment cadence or prorate without terms.

4. Separate advances/deposits, invoice due dates, service delivery, recognition and cash. Ask the controller about unknown recognition or tax policy.

5. Return calculation and draft billing proposals linked to job/PO. Recurrent schedules still require the configured approval and real issuance/send receipts; do not silently enable automated charging.

## Return and handoff

Return `fee_schedule`, `eligible_base`, `hour_reconciliation`, `billing_proposals`, `recognition_questions`, `exceptions`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Account lead and billing controller. Next: contract-po and client-billing. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
