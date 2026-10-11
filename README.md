# Agentic Advertising Agency ERP

Open-source agent skills that run the **complete back office of an advertising agency** — jobs, production, media planning and buying, spot verification, supplier invoices, client billing, collections, payments, treasury, tax, ledger, month-end close and profitability — from the assistant you already use (Claude Code, Codex, Claude.ai or a GPT/Project).

Version 0.2 is built on a **functional reverse engineering of a mature Latin American agency ERP**: about 1,330 public help pages were analysed and paraphrased into an [ERP functional reference](docs/erp-reference/README.md) with processes, document lifecycles, numbered business rules, accounting impacts, cross-module handoffs and country behaviour. Every skill is grounded in that reference and cites its rule ids.

**42 self-contained Agent Skills · 25 read-only deterministic calculators (also as a local MCP) · ERP functional reference · connector registry for official MCPs · 118 synthetic behaviour cases · npm/npx installer and Claude Code plugin marketplace.** MIT licensed. The package adds expertise, calculations and handoffs to your host; it is not a hosted ERP, payment service or autonomous runtime. No credentials, LLM keys or provider subscriptions are bundled. [Guía en español](README.es.md).

> Independent project, not affiliated with any ERP vendor. The reference describes publicly documented functional behaviour in our own words; no vendor code, screens or manual text are redistributed.

## The circuit

```mermaid
flowchart LR
  A[Masters and JobNumber] --> B[Fee contracts, POs, credit]
  B --> C[Production estimate]
  B --> D[Media plan]
  C --> E{Client approval}
  D --> E
  E --> F[Orders and POs]
  F --> G[Airing and spot control]
  G --> H[Supplier invoices]
  E --> I[Approved for billing]
  I --> J[Client invoices and e-invoicing]
  J --> K[Collections]
  H --> L[Payment run and release]
  K --> M[Treasury and bank]
  L --> M
  M --> N[Ledger, provisions, close]
  N --> O[Profitability and reporting]
```

Read the [end-to-end circuit](docs/erp-reference/e2e-circuit.md) for gates, shared identifiers, account role tags and the module → skill coverage matrix.

## Skills

★ = new in 0.2.

| Phase | Skill | What it does |
|---|---|---|
| Govern and connect | `agency-orchestrator` | Routes an agency job through the ERP circuit by JobNumber and document state, builds the stage dependency graph, checks period gates and dispatches sibling skills. |
|  | `agency-integrations` | Plans connector wiring per agency ERP stage from the provider registry, verifies live tools and scopes by discovery, applies least privilege and falls back to file mode. |
|  | `agency-access-governance` ★ | Reviews agency ERP access: roles and profiles, action levels 1-6, cost visibility A-D, approval powers as capabilities, SoD conflicts, configuration-change control, audit evidence and offboarding. |
|  | `agency-master-data` | Maintains agency ERP masters: clients, products, billing-client links, suppliers, media masters (type, outlet, programme, dayparts, duration factors, publication types), observation-coded GL links, cost centers and divisions. |
| Clients, jobs and commercial terms | `agency-onboarding` | Prepares client intake in the agency ERP: trade-name (owner) client versus legal billing clients, products and brands, attention groups, strategic brief and contact reports, routed through the provisional master approval chain. |
|  | `agency-job-lifecycle` ★ | Compose, open, move, substitute, re-bill and close agency JobNumbers under typology and billing-code rules, with the two-step accounts then finance close. |
|  | `agency-contract-po` | Turn signed client agreements and client purchase orders into enforceable PO limits, document links, PO transfers and budget-reserve rules. |
|  | `agency-budget-control` | Check client PO, budget-reserve and credit-limit headroom before client approval and separate reservations from commitments and spend. |
|  | `agency-fee-contracts` | Draft fixed and hourly client fee contracts: instalments, media/production split, JobNumber attachment by list or pattern, monthly hourly settlement and two-step approval. |
|  | `agency-billing-requirements` | Check client-specific prerequisites (client PO and balance, service entry, mandatory attachments, custom fields) per job, plan, schedule, order or estimate before an invoice is issued, and flag locked fields. |
| Work, time and production | `agency-tasks-timesheets` ★ | Dispatch and track internal job tasks through their state machine and validate, approve and value timesheet hours at cost and sale with chargeability. |
|  | `agency-production-estimating` | Builds and governs production estimates: line kinds, price lists, supplier quotes and award, client approval with credit check, approval for billing, purchase orders, advances and Post Buy variance. |
|  | `agency-production` | Runs creative delivery after estimate approval: asset QA, royalty and talent contracts (months or repetitions, expiry, extension), event staff request, assignment and evaluation, and a rights check that blocks release. |
| Media planning | `agency-media-ranking` | Ingest a licensed rating book (one market, recent period), derive discontinuous-market books and build rankings with planning and negotiation targets, affinity, CPR and CPM. Use before TV, radio or digital planning. |
|  | `agency-media-planning` | Compose a media plan from an open JobNumber: header defaults, up to 12 monthly schedules, items and spots priced per media type, agency fee, objectives, client approval circuit, credit override and approve-for-billing release. Use for plan builds and approvals. |
|  | `agency-tv-radio-planning` | Plan TV, radio and cable schedules by program or daypart from a ranking: duration-factor pricing, spot distribution within 99 spots per day, material distribution with royalty checks, traffic instructions and pre/post evaluation. Use for broadcast schedules. |
|  | `agency-ooh-planning` | Plan agency-side OOH, DOOH and print lines: circuits times rate, faces and exposure days, press cm by columns with surcharges, package month splits and the evidence each supplier must deliver. Use for out-of-home and press plan items. |
|  | `agency-digital-planning` ★ | Build digital media plans by platform, format and buy type (CPM, CPC, CPV, CPA), render naming taxonomy and UTM strings, add ad-server costs, sync planned vs actual and reprice ordered items from Google or Meta invoices matched by taxonomy. Use for digital plan items and invoice-based order adjustment. |
|  | `agency-plan-changes` | Revise approved or ordered media plans as new revisions: diff against the baseline, honour locks on ordered, controlled and billed spots, reschedule dropped spots and prepare order versions that cancel and replace. Use for changes after approval or ordering. |
| Media buying and delivery | `agency-rate-cards-contracts` ★ | Maintain media rate cards (buy and sell price sets, printed vs client cards, base-card inheritance, validity) and media buy contracts (caps, installments, parent/child, share, adjustments, transfers, balance). |
|  | `agency-media-buying` | Prepare insertion orders from client-approved schedules: split keys, approval and credit gates, buy pricing, versioning that cancels and replaces, send packs, close and reopen guards, vendor changes. |
|  | `agency-campaign-activation` | Prepare and, after approval, execute digital campaign setup through verified write tools (Meta Ads, Google Ads, Zernio): taxonomy naming, paused staging, budget checks, readback and external IDs. |
|  | `agency-campaign-optimization` | Diagnose pacing and performance against the approved plan (planned vs actual, objective deviation, TRP, CPR, CPM, frequency) and propose bounded bid, budget, audience or creative changes within fixed commitments. Use for in-flight reviews. |
|  | `agency-transmission-control` | Verify that ordered TV and radio spots aired: import monitoring files, map codes, auto match in normal or tolerance mode, manual and bulk control, ordered-not-aired and aired-not-ordered lists, makegood proposals and close prerequisites. Use before closing orders. |
|  | `agency-ooh-inventory` ★ | Run seller-side billboard inventory for a media owner: faces and states, availability, reservations converted to orders with monthly sub-orders, face and motif assignment, posting batches, and advertiser agreements with prepaid balance. |
| Payables and treasury | `agency-delivery-reconciliation` | Control supplier documents against the pending-to-receive balance per spot, production item or expense request line and classify differences by origin. |
|  | `agency-payables` | Log supplier documents in the reception register, check duplicates and arithmetic, pick the load type and prepare registration with accounts derived from media, production or expense type. |
|  | `agency-payment-run` ★ | Propose supplier payment lists, payment orders, withholdings and release instruments for human two-person approval. |
|  | `agency-cash-settlement` | Prepare bank and cash records: deposits, inter-bank transfers, bank charges, manual bank reconciliation with balance proof, own and third-party cheque lifecycle and rejection, corporate card statements and availability. |
|  | `agency-expenses` | Prepare agency overhead spend: expense contracts and requests with the PO gate, employee expense sheets and settlements, cost sheets against approved estimate items, petty cash, deferral over N months and expense budget. |
| Receivables and tax | `agency-client-billing` | Prepare client invoices and credit/debit notes from approved-for-billing plans, estimates and fee instalments: selection controls, agency fee, VAT, partial and split billing. |
|  | `agency-collections` ★ | Prepare customer receipts applying cash, cheques, transfers and withholding certificates to open invoices, customer advances and re-application, plus credit exposure, aging and collection follow-up worklists. Use for cobranzas and overdue chasing. |
|  | `agency-rebates` | Calculate supplier overcommissions, volume rebates, incentives and finder fees under documented contracts with the five scale engines, monthly provision vs bill flags, retroactivity and client rebate shares. Use for rebate pendings and settlement proposals. |
|  | `agency-tax-compliance` ★ | Prepare e-invoice authorization (MX CFDI via PAC, AR CAE), fiscal numbering checks, VAT books, withholding and perception regimes, certificates, VAT and gross-receipts positions and statutory exports from host-supplied country tables. Use for tax steps around invoices and month end. |
| Ledger and close | `agency-general-ledger` ★ | Prepare and validate agency general-ledger structure and manual journal entries: chart of accounts, rubros, observation codes, voucher types, provisional entries, templates, recurring and opening balances. |
|  | `agency-accruals-revaluation` ★ | Prepare month-end agency close jobs: unbilled revenue and uninvoiced cost provision, WIP, expense and overcommission provisions, FX revaluation, work-order closing and intercompany reclass, each with day-1 reversal checks. Use after pre-close. |
|  | `agency-fixed-assets` ★ | Prepare the agency fixed-asset register, depreciation run, disposal and annex: assets created from expense requests on B1 accounts, first-month criteria, sale or disuse disposal and inflation notes. |
|  | `agency-period-close` | Sequence and verify the agency monthly and fiscal-year close: subledger pre-close, ordered close jobs, mandatory gates, post-close reconciliations, reopen cascade and year re-close. |
| Management | `agency-profitability` | Analyzes job, client and media profitability: gross income, valued hours, direct expenses, contribution margin and overhead allocated by contribution share, with managed media spend kept apart. Use for job P&L, client profitability or margin reviews. |
|  | `agency-revenue-budget` ★ | Build and version the yearly agency revenue budget by client, product and month: investment, commission %, cost-difference %, fees and rebates, with copy-with-actuals, supervisor lock and projection. |
|  | `agency-cash-forecast` | Projects agency cash by day, week or month from bank balances, AR/AP open items, cheques, the client-approved unbilled pipeline, payroll, capex and adjustments, with expected date = due or billing date + terms + chronic delay. Use for liquidity planning. |
|  | `agency-management-reporting` ★ | Prepares the monthly management pack and parent-company reporting exports (HFM-style mapping per tab), validates mapping coverage, and computes KPIs: gross income, DSO, chargeability, WIP aging. Use after month close for management or headquarters reporting. |

Each skill folder contains `SKILL.md`, Codex UI metadata, the shared execution contract, the circuit map, only the ERP reference chapters it needs, the calculator script and CSV templates. [Workflow catalogue](docs/workflow.md) lists inputs, outputs, owners and next stages.

## Deterministic calculators

Money arithmetic never comes from the model. `tools/agency_tools.py` (copied into every skill) and the optional stdio MCP expose 25 read-only tools with strict input and output schemas, integer minor units and no network: `media_line_cost`, `discount_cascade`, `audience_metrics`, `tiered_commission` (flat, value scale, slab, marginal and stepped overcommission engines, validated against the reference's worked examples), `estimate_totals`, `hourly_fee_settlement`, `payment_terms`, `withholding`, `fx_revaluation`, `aging`, `allocate`, `installment_schedule`, `depreciation_schedule`, `journal_check`, `cash_projection`, `spot_match`, `credit_exposure`, `invoice_check`, `job_number`, plus `plan_diff`, `budget_check`, `reconcile`, `flat_rebate`, `margin` and `payload_digest`.

```sh
echo '{"currency":"MXN","method":"marginal","base_minor":550000,"reduction_bps":0,"deductions_minor":0,"flat_bps":0,"brackets":[{"from_minor":0,"bps":500,"amount_minor":0},{"from_minor":200000,"bps":300,"amount_minor":0},{"from_minor":500000,"bps":200,"amount_minor":0}],"cap_minor":null,"prior_adjusted_base_minor":null,"client_share_mode":"percent","client_share_bps":5000,"client_share_fixed_minor":0}' | node bin/agency-erp.mjs tool tiered_commission
```

Tax tables, FX rates and agency policy are inputs, never bundled assumptions.

## Install

Requires Node 22+ for the installer and Python 3 for calculators, local MCP, bundles and evaluations (standard library only).

**Claude Code plugin (skills + local calculator MCP):**

```sh
claude plugin marketplace add afelipeg/agentic-advertising-agency-erp
claude plugin install agency-erp@afelipeg-agency-erp
```

Skills appear as `/agency-erp:<skill-name>`; the calculator server is registered from `.mcp.json` and runs `python3` (on Windows, install Python 3 and make sure `python3` is on PATH, or edit the command to `py -3`).

**Project install for Codex or Claude Code:**

```sh
node bin/agency-erp.mjs list
node bin/agency-erp.mjs install --agent codex --dry-run
node bin/agency-erp.mjs install --agent codex          # .agents/skills
node bin/agency-erp.mjs install --agent claude-code    # .claude/skills
node bin/agency-erp.mjs connect-plan --profile agency  # or solo | studio | performance
node bin/agency-erp.mjs demo
```

Add `--global` for user-level installation or `--skill agency-payment-run` for one skill. Existing skill folders are never overwritten; archive old copies yourself before upgrading. `doctor` reports dependencies; it does not claim connector access.

**From GitHub with npx or the skills CLI:**

```sh
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent codex
npx skills add afelipeg/agentic-advertising-agency-erp --agent codex claude-code
```

npm registry publication is a separate release step; pin a reviewed tag or commit for reproducible installs.

## Claude.ai and ChatGPT/GPT

Claude.ai supports custom skill uploads: `node bin/agency-erp.mjs bundle --skill agency-client-billing --out agency-client-billing.zip`, then upload and enable it in Claude's skill settings. Upload more stages as needed; connectors are configured separately.

For ChatGPT, prefer available marketplace apps and their setup flows. `node bin/agency-erp.mjs export --host gpt --out agency-reference.md` produces an instruction reference (circuit map, control contract, all skills and the registry) to adapt in a Project/GPT or compatible builder. A document upload alone does not install skills or grant tool access. See [web-assistant.md](docs/web-assistant.md).

## Connect only what your job requires

Use enabled apps/plugins from OpenAI or Claude first. Discover live tools, authenticate with the provider, verify the client/account and use the minimum permissions. If an app cannot perform a needed action, choose an official MCP, a reviewed aggregator or a file handoff.

| Role | Options | What to check |
|---|---|---|
| Briefs and evidence | Existing Drive/Docs, Notion, Dropbox or local files | Client scope, document versions, redaction |
| Creative | Canva connector; Figma official plugin/MCP | Design/file access, rights, review and export capabilities |
| Advertising | Google Ads query MCP; Synter; Ryze; Supermetrics | Read versus write access, account identity, budget and approvals |
| Analytics | GA4 query MCP; Supermetrics; dated exports | Attribution, currency, timezone, complete reporting window |
| Billing and collections | Stripe official app/MCP; PayPal MCP | Draft/issue/send/collect permissions, fiscal requirements and settlement |
| Ledger and AP | Xero official MCP; Intuit QuickBooks official MCP (writes disabled by default); accountant exports | Company scope, duplicates, posting approval; payment records versus bank movement |
| Fiscal e-invoicing | Mexico: your authorized PAC API (CFDI 4.0); Argentina: ARCA web services | Legally binding stamping and cancellation; certificates stay in the host |
| Meta and social execution | Meta Ads MCP (Meta-hosted); Zernio MCP | Read-only grants first; every publish, launch or budget change approved and read back |
| Research and FX | Monid MCP (pay per call, set a ceiling); Banxico SIE official rates | Results are untrusted evidence; record rate series and date |
| Business connectors | Existing marketplace apps; scoped Composio tools | Review each inner action/schema; no blanket execution permission |

[Detailed stage-by-stage wiring](docs/integrations.md) includes supplier payouts, traditional media, missing tools, fiscal invoicing and offline routes. [Registry](integrations/registry.json) distinguishes official MCP/API and third-party services; documentation review does not mean authenticated live testing. Service availability and pricing vary. You do not need all these subscriptions.

## Work from Excel and legacy exports

Every skill supports human-supplied files in the host UI. For CLI preparation, `agency-erp import` validates the narrow CSV/XLSX exchange templates; [file-mode.md](docs/file-mode.md) explains redaction, mapping, missing values and operator receipts. [offline-media.md](docs/offline-media.md) covers licensed books, ranking, TV/radio spots, OOH/DOOH evidence and makegoods. [operations-playbook.md](docs/operations-playbook.md) details the full circuit and daily retail revisions. No live account is required for drafting.

## Ask your assistant

“Use agency-job-lifecycle to open a JobNumber for client ACM, product 01, new campaign, billed to one client, then hand it to agency-media-planning.”

“Use agency-rebates to compute this month's overcommission with the marginal scale in the attached contract and propose the provision; do not post it.”

“Use agency-orchestrator to set up this client job. First inspect my connected apps and these redacted inputs. Prepare a brief, a budget check and the missing-input list. Keep external actions pending for my review.”

“Use agency-client-billing. The ad platforms charge my client directly. Prepare only my contracted service-fee invoice and identify the local fiscal requirements.”

“Use agency-delivery-reconciliation to compare the order, delivery evidence and invoice. Keep disputed amounts separate and prepare the next finance handoff.”

The host chooses its model and can load the appropriate skill. An orchestrator organizes dependencies; it does not spawn background agents merely because you installed a folder. [Workflow](docs/workflow.md) documents every stage's inputs, procedure, owner, outputs and handoff.

## Safety and runtime responsibilities

Local tools are read-only arithmetic with strict bundled input/output validation. External accounts are accessed only through the user's configured tools. Skills require approval before money, commitments, emails/messages or deletion, but **prompts cannot enforce** sandboxing, secrets removal, atomic reservations, budgets or authenticated approvals. Your host must enforce [control-contract.md](docs/control-contract.md). If it cannot, stay in draft/read-only mode. [Architecture](docs/architecture.md) maps each requested control to the included component or host requirement.

## Validate and contribute

```sh
npm run check
npm test
npm run eval
npm pack --dry-run
```

Deterministic checks verify tools, packaging and synthetic fixtures; they are not LLM success rates. [Evaluation guide](evals/README.md) separates deterministic results from trajectory and held-out model tests. Run behavioral cases independently in your intended host before live writes. CI blocks broken package/tool regressions; production hosts must additionally gate model releases on their reviewed trajectory suite. Contribute reviewed integrations, anonymized failure cases and clearer procedures through [CONTRIBUTING.md](CONTRIBUTING.md). Never contribute secrets, client records or fabricated provider receipts.

Discovery sources: [awesome-agentic-advertising](https://github.com/afelipeg/awesome-agentic-advertising), independently checked against provider documentation. Skill formats: [Agent Skills](https://agentskills.io/specification), [Codex skills](https://learn.chatgpt.com/docs/build-skills), [Claude skills](https://code.claude.com/docs/en/skills).

See [release validation](docs/release-validation.md) for checks actually run and the remaining host/publication boundaries.
