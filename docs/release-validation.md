# 0.1.0 release candidate validation

Validation date: 2026-10-11. This is a portable skill package and local read-only tooling release candidate. It does not certify a production ERP or autonomous execution.

## Verified locally

| Check | Result |
| --- | --- |
| Skill creator frontmatter/resource validation | 28 of 28 passed. |
| Package consistency and self-contained references | Passed; 28 skills and 34 synthetic behavior scenarios. |
| Python tool/import/trajectory tests | 21 passed. |
| Node installer/export/bundle tests | 4 passed. |
| Deterministic business evaluation fixtures | 7 of 7 passed; zero instrumented model runs in this suite. |
| Actual npm package | Built without bytecode/cache files; includes tests and contributor instructions. |
| Offline npx install from local npm tarball | Installed all 28 Codex skills into a fresh project. |
| Installed CLI TV CSV import | Passed; source remains unverified. |
| Calculator run from installed skill | Passed; delivery shortfall returned a hold. |
| Local MCP | stdio initialization, tool inventory, schema output and refusal of an unknown write tested. |

The separate skill-creator forward test reviewed the instructions with synthetic raw cases, without evaluation gold or external accounts: a daily retail revision removing committed TV inventory; missing ratings in XLSX; an authenticated solopreneur reviewing an AI-prepared payment; overlapping PO requests; partial delivery; payment recording versus real settlement; read-only ad tooling; and direct supplier billing. Findings led to clearer shortfall holds, owner approval policy, handoff schema, provenance and cancellation sequencing. This was a qualitative independent review, not a measured production-model benchmark.

## Coverage and boundaries

The operations playbook describes onboarding → masters → commercial terms/PO → budget → media ranking/planning → production estimates/selection → orders/materials/activation → daily changes → transmission/delivery reconciliation → AP/client billing → cash/rebates/expenses → margin/close. Offline guidance covers TV/radio books, programs, timebands, rate units, material acceptance, emission matching and compensation; OOH separates site/flight, fabrication/installation and digital play evidence. Instructions are an original functional reconstruction using public behavior and documented agency controls, not access to another product's source or undisclosed internals.

Every stage accepts redacted human-supplied evidence. The bundled importer supports only its six exact CSV/XLSX exchange templates; it is not a universal legacy import, PDF OCR or a PII detector. UI file handling depends on the assistant's actual capabilities. A normalized workbook is not approval, a supplier booking, a bank transfer or a posted ledger document.

Connector documentation was reviewed, but no provider authentication, advertising write, fiscal emission, email, bank transfer or real-account settlement was tested. Availability depends on host, permissions, provider plan, country and actual discovered tools. Dynamic model routing, shared budgets, caching, authenticated HITL, transactional reservation, redaction, sandboxing, durable checkpoints and telemetry require a host implementation. Their configuration examples are not active enforcement.

There are no instrumented host trajectories or model baseline in this release. CI verifies package/tests/deterministic fixtures and supplied reviewed traces; it cannot yet block a production model regression against a nonexistent baseline. `--require-traces` prevents an empty trajectory directory from passing when a maintainer configures a production release gate. Fine-tuning, traffic A/B and provider failover are deployment procedures, not delivered services. No live hosted demo or speedup SLA is claimed.

## Publication status

The public repository `afelipeg/agentic-advertising-agency-erp` was verified with write access after its initial creation. Source publication preserves the owner's original MIT license. GitHub-based npx installation is available after this source commit reaches main; the README also documents local installation. The npm registry package has not been published, and no hosted production service is claimed. Inspect the repository's Actions tab for remote CI results rather than treating local tests as a completed GitHub workflow run.
