---
name: agency-ooh-planning
description: "Plan exterior inventory, print and other offline placements with site-level evidence and buying terms. Use for store coverage, faces, circuits, DOOH loops or print units; do not equate booked inventory with actual exposure."
---

# Plan OOH, DOOH and offline placements

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Brief/store geography; inventory/site IDs and availability; supplier rates/contracts; install/production costs; format/dimensions; dates; rights/permits policy; audience evidence if licensed.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Identify OOH faces/sites/circuits by supplier ID and location, orientation, format and dates. For retail link store/trade area and promotion cutoff. For print record publication, issue, section/page, dimensions and units.

2. Separate static OOH, DOOH and print pricing: face/period, package, spot/loop/share-of-voice, CPM or contracted print measure. Include documented production, install, illumination, taxes/permits and dismantling costs; never assume one unit conversion.

3. Validate tariff and negotiation applicability for supplier/client and every period. A multi-month flight may outlast a contract; flag uncovered months rather than propagating an expired discount.

4. Define delivery acceptance: dated/geolocated installation evidence, removal dates, proof-of-play logs, availability/downtime or print tear sheets. Photos prove an installation moment, not necessarily the full exposure period or measured audience.

5. Prepare reviewable site/order/material packs; use an eligible marketplace tool or reviewed official DOOH API adapter if actually available. If not, use inventory CSV and human supplier confirmations. No universal TV/OOH MCP is bundled. Preserve cancellations/replacements as revisions.

## Return and handoff

Return `site_plan`, `offline_specifications`, `cost_schedule`, `evidence_requirements`, `booking_proposals`, `exceptions`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Offline planner and production owner. Next: media-buying, production and delivery-reconciliation. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
