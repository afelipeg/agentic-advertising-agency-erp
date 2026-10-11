# Changelog

## 0.3.0 — 2026-10-11

### Added
- **App downloads without a terminal:** a GitHub release with one .zip per skill (valid for the Claude app and the Gemini app), an all-skills bundle, `assistant-instructions.txt` + `agency-erp-knowledge.md` + `agency_tools.py` for ChatGPT GPTs/Projects and Gemini Gems, and checksums. Built by `scripts/build_release.py` and published by `.github/workflows/release.yml` on every `v*` tag.
- **Gemini:** Gemini CLI extension (`gemini-extension.json`, `GEMINI.md`, calculator MCP) and `agency-erp install --agent gemini`.
- Beginner "Start here" sections in both READMEs: what the package is, why skills instead of prompts, step-by-step installation for Claude, Gemini, ChatGPT and Gems, example requests and a download table for all 42 skills.

### Changed
- Skill descriptions shortened to 200 characters or fewer so uploads pass the Claude app limit; the package check enforces it. All 42 bundles pass the official `skills-ref validate`.

## 0.2.0 — 2026-10-11

### Added
- **ERP functional reference** (`docs/erp-reference/`): functional reverse engineering of a reference agency ERP from ~1,330 public help pages, paraphrased into 11 domain chapters (accounts and jobs, production, media planning, media buying, media masters and OOH, expenses, receivables, supplier invoicing, payables and treasury, accounting, management and security) plus an end-to-end circuit map with gates, account role tags and a module → skill coverage matrix.
- **14 new skills:** job-lifecycle, tasks-timesheets, revenue-budget, rate-cards-contracts, digital-planning, ooh-inventory, payment-run, collections, tax-compliance, general-ledger, accruals-revaluation, fixed-assets, management-reporting, access-governance (42 total).
- **19 new deterministic calculators** (25 total): media_line_cost, discount_cascade, audience_metrics, tiered_commission (five overcommission engines validated against the reference's worked examples), estimate_totals, hourly_fee_settlement, payment_terms, withholding, fx_revaluation, aging, allocate, installment_schedule, depreciation_schedule, journal_check, cash_projection, spot_match, credit_exposure, invoice_check, job_number. All exposed by the local MCP.
- **Claude Code plugin marketplace** (`.claude-plugin/`, `.mcp.json`), `AGENTS.md`/`CLAUDE.md` for maintainers, `agency` connection profile.
- **Connectors:** Meta Ads MCP, Intuit QuickBooks MCP (now verified), Notion, HubSpot, Zernio, Monid, Zapier, Banxico SIE, Mexico CFDI PAC route, ARCA web services, vastlint, Meridian; every provider now lists the skills (`stages`) it serves.
- 84 new synthetic behaviour scenarios (two per skill) and 11 deterministic fixtures.

### Changed
- All 28 existing skills rewritten on the reference rules (states, locks, gates, rule ids, calculations, segregation of duties, exceptions). `agency-cash-settlement` now owns bank, cash and cheques; payment proposals moved to `agency-payment-run`; collections moved to `agency-collections`. `agency-period-close` delegates provisions to `agency-accruals-revaluation`.
- `contracts/workflows.json` adds `references` and `tools` per skill; `docs/workflow.md` is generated from it.
- Skills mirror only the ERP chapters they need (`references/erp/`); the package check verifies references, tool mentions, catalogue/frontmatter equality and scenario coverage per skill.

### Fixed
- `agency-plan-changes` description lacked use/avoid guidance.
- Integration guide claimed no first-party QuickBooks MCP and six calculators.
