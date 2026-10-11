# Agentic Advertising Agency ERP

Open-source operational skills for a small advertising agency, creative studio or solopreneur. Run your existing AI assistant through intake, scope, budgets, planning, production, media, reconciliation, billing, collections, expenses, margin and close. Connect the tools you already use; start with redacted files when you do not have a connector.

**28 self-contained Agent Skills, an npm/npx installer, six read-only calculation tools, an optional local stdio MCP, connector wiring and evaluation cases.** MIT licensed. The package adds expertise and handoffs to your host; it is not a hosted ERP, autonomous payment service or production swarm runtime. No account credentials, LLM keys or provider subscriptions are bundled. [Guía en español](README.es.md).

## Start locally

Requires Node 22+. Python 3 is needed only for calculations, local MCP, bundle creation and offline evaluations. The runtime tools have no third-party dependencies.

```sh
node bin/agency-erp.mjs list
node bin/agency-erp.mjs install --agent codex --dry-run
node bin/agency-erp.mjs install --agent codex
# Or choose Claude Code instead:
node bin/agency-erp.mjs install --agent claude-code
node bin/agency-erp.mjs connect-plan --profile solo
node bin/agency-erp.mjs demo
```

Run installation from your agency project directory, or pass `--cwd /your/project`. Codex uses `.agents/skills`; Claude Code uses `.claude/skills`. Add `--global` for user-level installation, or `--skill agency-production` for one skill. Existing skill folders are never overwritten. Inspect and archive old copies yourself before upgrading. `doctor` reports dependencies; it does not claim connector access.

## npx distribution

After the GitHub repository is published and accessible:

```sh
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent codex
# Same package, other host:
npx --package github:afelipeg/agentic-advertising-agency-erp agency-erp install --agent claude-code
```

Or use the independent [skills CLI](https://github.com/vercel-labs/skills):

```sh
npx skills add afelipeg/agentic-advertising-agency-erp --agent codex claude-code
```

After a maintainer publishes version 0.1.0 to npm, `npx --package agentic-advertising-agency-erp@0.1.0 agency-erp install --agent codex` becomes available. These are release instructions, not a claim that npm publication has happened. Pin a reviewed tag/commit/version for reproducible installation.

## Claude.ai and ChatGPT/GPT

Claude supports custom skill uploads: generate one self-contained bundle with `node bin/agency-erp.mjs bundle --skill agency-production --out agency-production.zip`, then upload and enable it using Claude's current skill UI. Upload more stages as needed. Skills and connectors are configured separately; inspect plan/workspace eligibility.

For ChatGPT, prefer available marketplace plugins/apps and their own setup flows. This package is not automatically listed in either marketplace. `node bin/agency-erp.mjs export --host gpt --out agency-reference.md` produces an instruction reference to adapt in a Project/GPT or compatible skill/plugin builder. A document upload alone does not create native tool access or install executable skills. Follow [web-assistant.md](docs/web-assistant.md) for the actual compatibility boundary.

## Connect only what your job requires

Use enabled apps/plugins from OpenAI or Claude first. Discover live tools, authenticate with the provider, verify the client/account and use the minimum permissions. If an app cannot perform a needed action, choose an official MCP, a reviewed aggregator or a file handoff.

| Role | Options | What to check |
|---|---|---|
| Briefs and evidence | Existing Drive/Docs, Notion, Dropbox or local files | Client scope, document versions, redaction |
| Creative | Canva connector; Figma official plugin/MCP | Design/file access, rights, review and export capabilities |
| Advertising | Google Ads query MCP; Synter; Ryze; Supermetrics | Read versus write access, account identity, budget and approvals |
| Analytics | GA4 query MCP; Supermetrics; dated exports | Attribution, currency, timezone, complete reporting window |
| Billing and collections | Stripe official app/MCP; PayPal MCP | Draft/issue/send/collect permissions, fiscal requirements and settlement |
| Ledger and AP | Xero official MCP; reviewed QuickBooks connector/API; accountant exports | Company scope, duplicates, posting approval; payment records versus bank movement |
| Business connectors | Existing marketplace apps; scoped Composio tools | Review each inner action/schema; no blanket execution permission |

[Detailed stage-by-stage wiring](docs/integrations.md) includes supplier payouts, traditional media, missing tools, fiscal invoicing and offline routes. [Registry](integrations/registry.json) distinguishes official MCP/API and third-party services; documentation review does not mean authenticated live testing. Service availability and pricing vary. You do not need all these subscriptions.

## Work from Excel and legacy exports

Every skill supports human-supplied files in the host UI. For CLI preparation, `agency-erp import` validates the narrow CSV/XLSX exchange templates; [file-mode.md](docs/file-mode.md) explains redaction, mapping, missing values and operator receipts. [offline-media.md](docs/offline-media.md) covers licensed books, ranking, TV/radio spots, OOH/DOOH evidence and makegoods. [operations-playbook.md](docs/operations-playbook.md) details the full circuit and daily retail revisions. No live account is required for drafting.

## Ask your assistant

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
