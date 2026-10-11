---
name: agency-production-estimating
description: "Build itemized production estimates, compare supplier alternatives and prepare selected purchase items. Use for audiovisual, design, print, creative or internal work; do not purchase before supplier selection and financial mapping."
---

# Estimate and revise production costs

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Open job with billable/internal classification; deliverable scope/specs; service types and cost/revenue mappings; supplier alternatives; labor rates; currency; fee/contingency/tax policy; client requirements.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Validate job status and billable/internal classification. An internal cost-only job does not authorize a client invoice. Separate mixed-currency items into explicit currency groups; issuance follows the provider’s permitted currency rules.

2. Itemize quantities, supplier base cost, internal hours/rates, client price, agency fee, contingency, tax basis and delivery criteria. Use a dated price list only within its documented validity.

3. Keep supplier alternatives as distinct scenarios with scope, cost, deadlines, rights and assumptions. Require a selected supplier per externally purchased item; overall estimate approval alone cannot select one.

4. Validate service-type posting/tax mapping before approving commitments. Document estimate revision and prior approved baseline; additions and rework consume PO headroom and need applicable fresh approval.

5. Prepare the client review pack and selected supplier purchase handoff. Preserve accepted milestones for later uninvoiced/unbilled accruals. Billed or closed items cannot be silently deleted; propose linked adjustment instead.

## Return and handoff

Return `estimate_items`, `supplier_comparison`, `selected_costs`, `client_price`, `margin_forecast`, `approval_pack`, `purchase_handoff`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Estimator/producer and controller. Next: production, budget-control and media-buying. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
