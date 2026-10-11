# Contribute

Open an issue or PR with the operational need, reproducible deidentified example, expected handoff and validation. Keep this project independent and write original descriptions. Do not copy proprietary prompts, private product screens or client documents.

For a connector, supply primary provider docs, current transport/authentication, account scopes, actual tool/schema discovery, country/product restrictions, read/write boundaries, sandbox procedure and unavailable-capability fallback. Marketplace presence does not prove all API operations are exposed. Credentials and live data never belong in fixtures. Mark documentation-only integrations honestly; write-tested claims require a permitted sandbox trace.

For skills, use name/description frontmatter, clear activation conditions, required inputs, operational procedure, blockers, human gate and return/handoff. Keep each folder independently installable. Copy shared contracts with scripts/sync_resources.py and run checks. Do not put behavioral evaluation gold answers in installed skill resources.

For failures, include synthetic or consented/deidentified provenance, tool/model versions and observable steps. Add a regression scenario before changing prompts, and an executable regression when a deterministic tool is affected. Separate expected outcomes from the skill context. Run check, test and eval. Model changes need held-out trajectory evaluations and a host-controlled shadow/A-B rollout; do not relabel static lint scores as model quality.

Release only after required checks pass and supported host forward tests are reviewed. Publish a pinned npm version under authorized maintainer credentials; never put an npm token in this repository. Record known gaps and host limits. Marketplace publication is separate from npm/GitHub publication and must follow each marketplace's review process.
