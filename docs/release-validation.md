# 0.3.0 release candidate validation

Validation date: 2026-10-11. Portable skill package, ERP functional reference and local read-only tooling. It does not certify a production ERP or autonomous execution.

## Verified locally

| Check | Result |
| --- | --- |
| Package consistency (`npm run check`) | Passed: 42 skills, 25 local tools, 118 synthetic behaviour scenarios (at least two per skill), catalogue = frontmatter descriptions, per-skill ERP references, no resource/asset/generated-doc drift, portable links. Injected drift in `docs/workflow.md` was detected. |
| Python tests (`npm test`) | 57 passed: calculators (including regression tests from an independent review), importer, trajectory checker and stdio MCP (tool inventory, structured output, error isolation for out-of-range inputs). |
| Node installer/export/bundle tests | 4 passed. |
| Deterministic business fixtures (`npm run eval`) | 18 of 18 passed, including the five overcommission engines reproduced from the reference's worked examples. Zero model runs. |
| SKILL.md example tool inputs | All 37 runnable examples executed against the canonical calculator without error. |
| npm package | 979 files, no bytecode/cache; includes `.claude-plugin/`, `.mcp.json` and `docs/erp-reference/`. |
| Install from packed tarball | All 42 skills installed for Codex (`.agents/skills`) and Claude Code (`.claude/skills`) in a fresh project; calculator executed from an installed skill folder. |
| Claude.ai bundle | `bundle --skill agency-tax-compliance` produced a self-contained zip (23 files). |
| Claude Code plugin | `claude plugin validate .` passed with one expected warning (root `CLAUDE.md` is maintainer guidance, not plugin context). |
| App bundles (0.3.0) | `scripts/build_release.py` produced 42 skill zips plus the ChatGPT/Gem pack; all 42 extracted bundles passed the official `skills-ref validate`; descriptions are 200 characters or fewer; build is deterministic (identical checksums on rebuild). |
| Gemini | `agency-erp install --agent gemini` installs into `.gemini/skills`; `gemini-extension.json` declares the calculator MCP with `${extensionPath}`. Not run inside Gemini CLI or the Gemini app in this environment. |
| Verbatim-overlap scan | 10-word overlaps with the source manual are limited to guide/menu titles and state names used as citations; no copied prose. |

An independent reviewer, working without the authoring context, audited the calculators, the sync and check scripts, six skills against their cited rules, the packaging and the registry. It found these issues:

- date overflow crashing the MCP
- direct production lines without agency service
- order-dependent spot matching
- fortnight payment terms
- the first bracket of marginal tiers
- additive rounding
- the depreciation remainder
- credit balances in aging
- the error-list cap
- stale wording about Supermetrics and Meta
- a wrong rule citation
- missing drift checks

All were fixed and covered by tests.

## Coverage and boundaries

The ERP reference was built from ~1,330 public help pages of a reference agency ERP and paraphrased into 11 domain chapters plus a circuit map. Training pages that contain only video titles, stub screens and items the source leaves ambiguous are listed as gaps; skills label them *confirm locally*. Country depth is highest for Argentina and Colombia; Mexico appears mainly through CFDI stamping and counter-receipts. Tax tables, e-invoicing providers, FX sources and statutory layouts must come from the host.

Connector documentation was reviewed (Meta Ads MCP, Intuit QuickBooks MCP, Notion, HubSpot, Zernio, Monid, Banxico SIE and others) but no provider authentication, advertising write, fiscal emission, email, bank transfer or settlement was tested. Runtime controls (authenticated approvals, atomic reservations, redaction, sandboxing, durable checkpoints, telemetry) remain host responsibilities described in `control-contract.md` and `architecture.md`.

There are no instrumented host trajectories or model baseline in this release; the behaviour scenarios are synthetic acceptance cases for forward-testing in your host.

## Publication status

Source changes are proposed on branch `feat/erp-reverse-engineering`. The npm registry package is not published and no hosted service is claimed. Check the repository's Actions tab for remote CI results.
