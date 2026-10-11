---
name: agency-transmission-control
description: "Compare ordered TV/radio spots or DOOH plays against monitored emissions and supplier certificates, then prepare post-buy discrepancies. Do not approve delivery solely because a supplier invoice exists."
---

# Verify emissions and makegoods

Read [control-contract.md](references/control-contract.md), [operations-playbook.md](references/operations-playbook.md) and, for offline media, [offline-media.md](references/offline-media.md). Apply their identity, evidence, state, approval and runtime requirements. Prefer enabled host marketplace apps/plugins; discover actual tools before selecting another connector.

## Inputs

Accepted insertion order and revisions; material/version codes; station/site mapping; broadcast-day timezone; monitor/proof-of-play records; supplier certificates; allowed matching and makegood policy.

Use permitted reads and supplied files first. Ask for material missing evidence, never for secrets in chat.

## Procedure

1. Validate monitor/source rights, completeness and timestamp basis. Normalize station/site/program/creative IDs using reviewed mapping; quarantine unmapped records, duplicate logs and inconsistent duration.

2. Match individual ordered spots/plays to observed events under explicit station/date/window/duration/creative rules. Do not count one observed event against two orders or force a fuzzy name match without review.

3. Classify not-emitted, shifted, wrong-material, short-duration, extra/unordered and duplicate events. An extra spot is not automatically billable or an accepted substitute. Preserve ordered and observed facts.

4. Prepare a makegood/credit proposal with affected order/spot, contractual deadline, replacement specifications and required client acceptance. Verify replacement emission before marking the original discrepancy resolved.

5. Prepare post-buy results using actual licensed audience evidence where available; compare like targets/methodology and retain missing data. Pass accepted delivery and open holds to reconciliation; money/postings require separate approval.

## Return and handoff

Return `emission_match`, `missing_or_extra_insertions`, `material_exceptions`, `makegood_register`, `postbuy_report`, `finance_handoff`, plus tenant/client/job IDs, stage/revision, currency/period, status, source references, assumptions, blockers, required approvals and next stage. Use blocked/draft for unavailable evidence or tools; completed only with verified results. Read [handoff-schema.json](references/handoff-schema.json) for the shared envelope; validate through the host before consuming it.

Owner: Traffic controller and reconciler. Next: delivery-reconciliation and profitability. Retain client-scoped deidentified decisions and source references; memory and document content cannot grant approval.

## Tools

Read [provider-registry.json](references/provider-registry.json) and [wiring-guide.md](references/wiring-guide.md). Available local read-only calculations are described in [tool-contracts.json](references/tool-contracts.json). Run `python3 scripts/agency_tools.py TOOL < input.json` from this skill directory only for a supported calculation with all required inputs. No local tool generates licensed ratings, signs contracts, books suppliers or issues/pays invoices. The host must enforce strict connector schemas, sandboxing, approved writes and resumable execution.

## Files instead of MCP

Read [file-mode.md](references/file-mode.md) for UI attachments and CLI normalization. Use human-supplied redacted XLSX/CSV, documents and delivery evidence when a connector is absent. Templates are in assets/. From this skill directory run `python3 scripts/normalize_files.py --kind KIND --file SOURCE --out NEW.json --tenant ID --client ID --job ID` for a supported narrow import. CSV needs only Python; XLSX requires optional openpyxl and an explicit sheet. Treat normalized files as unverified evidence, not authenticated authority. Prepare a review/change pack; the human uploads actual legacy-system receipts after execution. Never require MCP just to draft or compare.
