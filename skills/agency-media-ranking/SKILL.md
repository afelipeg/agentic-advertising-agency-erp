---
name: agency-media-ranking
description: "Prepare a book-based audience/rate comparison or a book-free inventory shortlist for digital, TV or radio. Use before generating plans; do not confuse missing audience data with zero or treat ranking as purchase approval."
---

# Build a media shortlist and ranking

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Open job and client; medium/program/location masters; licensed audience book with market, period, methodology and target definitions; rate/negotiation versions; planning and negotiation targets; currency and approved FX basis.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Establish whether this is a licensed audience-book analysis or an inventory-only shortlist. Verify source rights, geography, dates, program/location IDs, rating units and target definitions before extracting data.

2. Select media, programs/locations, timebands and emission days relevant to the brief. Maintain planning and negotiation targets separately; record explicit inclusion/exclusion criteria and unknown audience values.

3. Compare only compatible audience, cost-per-rating-point, CPM and affinity measures with documented formulas/denominators. Do not infer deduplicated reach from summed ratings or rank missing data as low performance. Preserve excluded candidates and reasons.

4. Bind candidates to current client/job, supplier, tariff, publication type, valid contract, gross/net basis, duration, currency and authorized negotiated FX reference. Flag expired/missing terms; do not carry another client’s negotiated discount.

5. Return a reproducible preselection with source/version and inherited commercial terms for the plan. No booking or budget reservation occurs from a shortlist. If no licensed book exists, return an explicitly limited inventory/rate comparison without invented ratings.

## Return and handoff

Return `ranking_spec`, `candidate_table`, `data_quality_exceptions`, `selected_inventory`, `commercial_inheritance`, `planning_handoff`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Media researcher and planner. Next: tv-radio-planning or media-planning. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
