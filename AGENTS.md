# AGENTS.md

Guidance for coding agents (Codex, Claude Code, others) working **on** this repository. To *use* the skills, see README.md.

## What this repo is

- `skills/<name>/` — 42 self-contained Agent Skills that run an advertising agency's ERP circuit. Each has `SKILL.md`, `agents/openai.yaml` (Codex UI metadata) and mirrored `references/`, `scripts/`, `assets/`.
- `docs/erp-reference/` — functional reverse engineering of a reference agency ERP (paraphrased English). `e2e-circuit.md` is the map every skill links.
- `tools/agency_tools.py` — read-only deterministic calculators (stdlib only, integer minor units, strict input/output schemas). `tools/mcp_server.py` exposes them over stdio MCP.
- `contracts/workflows.json` — the skill catalogue (descriptions, outputs, ERP references, tools). It drives `docs/workflow.md` and per-skill reference mirroring.
- `integrations/registry.json` — documented connector options per ERP stage. Documentation review, not tested access.
- `.claude-plugin/` and `.mcp.json` — Claude Code plugin marketplace packaging.

## Rules for changes

1. Never edit mirrored files inside `skills/*/references`, `skills/*/scripts` or `skills/*/assets`. Edit the canonical source (`docs/`, `tools/`, `integrations/`, `contracts/`) and run `npm run sync`.
2. A skill's description lives in two places: `SKILL.md` frontmatter and `contracts/workflows.json`. Keep them identical; `npm run check` fails otherwise.
3. New calculators: add schema, output schema, description and function in `tools/agency_tools.py`; add tests in `tests/test_erp_tools.py` and a fixture in `evals/deterministic.json`. No network, clock, randomness or third-party imports.
4. ERP rules must cite the reference id (e.g. `BR-O-08`) or be labelled agency policy / *confirm locally*. Do not paste vendor manual text; paraphrase.
5. Never add credentials, client data or claims of live connector access. Skills prepare and verify; humans approve money, postings and sends.

## Verify before committing

```sh
npm run sync     # mirror shared resources and per-skill ERP references, regenerate docs/workflow.md
npm run check    # structure, links, drift, catalogue consistency
npm test         # unit tests for calculators, importer, MCP and installer
npm run eval     # deterministic business fixtures
```
