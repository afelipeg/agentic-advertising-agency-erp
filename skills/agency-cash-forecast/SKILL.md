---
name: agency-cash-forecast
description: "Build an agency cash-flow forecast from receivables, commitments, payables and settlements. Use for short-term liquidity or collected-client/unpaid-supplier exposure; do not treat revenue, invoices or unsettled processor balances as cash."
---

# Forecast collections and obligations

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Opening bank balances; receivable due dates and collection evidence; approved payables/orders; processor settlement schedule; currencies; FX basis; tax obligations and scenario assumptions.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Read verified opening cash and ledger/account scope. Keep bank cash, processor balance, undeposited funds, approved commitments and outstanding invoices separate.

2. Create daily/weekly inflow/outflow buckets using due dates, settlement delays and documented probabilities/scenarios. Avoid double counting a client payment in both provider events and bank receipts.

3. Link client collections and remaining supplier exposure by job/order; disclose which suppliers remain unpaid after related client collection. Include labor, expenses, tax and fixed overhead under configured policy.

4. Keep currencies separate unless an approved dated FX policy supports consolidation. Stress-test delayed collection, disputed delivery and cancellation costs with explicit assumptions.

5. Return liquidity gaps and draft prioritized actions. Collection emails, financing, refunds and supplier payments require their own approvals; the forecast never executes money movement.

## Return and handoff

Return `cash_forecast`, `currency_buckets`, `collection_scenarios`, `supplier_exposure`, `liquidity_gaps`, `action_proposals`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Treasury owner. Next: cash-settlement and profitability. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
