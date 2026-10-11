# Observable trajectory format

The evaluator accepts one JSON file per scenario. It evaluates exported evidence and an independent review, not hidden reasoning or the authenticity of a provider receipt. The host must authenticate approvals and preserve source receipts separately. Never export raw prompts, secrets or PII as trace evidence.

Run `python3 scripts/evaluate_trajectory.py trace.json`, or use `--directory DIRECTORY` for a batch. Add `--require-traces` to fail if a directory contains no traces. The default package CI reports missing host traces explicitly; it cannot enforce a model-quality regression threshold without actual host runs and a versioned baseline.

## Envelope

All listed fields are required; extra fields are rejected.

| Field | Meaning |
| --- | --- |
| `case_id` | An exact scenario ID from scenarios.json. |
| `origin` | `synthetic` or `deidentified-authorized-production`. |
| `limits` | Positive integer caps: `tokens`, `elapsed_ms`, `cost_microusd`. One microUSD is 0.000001 USD; provider tool fees/retries count toward task cost. |
| `events` | Nonempty ordered array of observable events, described below. |
| `review` | Independent rubric adjudication and evidence references. |

## Every event

| Field | Required representation |
| --- | --- |
| `seq` | Contiguous positive integer, starting at 1. |
| `kind` | `decision`, `model`, `tool-read`, `approval`, `tool-write`, `write-uncertain`, `outcome-query`, `checkpoint`, or `resume`. |
| `tenant_id`, `client_id`, `job_id` | Nonempty pseudonymous strings; immutable throughout the task. |
| `revision` | Positive integer business revision. |
| `action_key` | Stable host-assigned idempotency identifier; a retry must retain it. Empty string for an event unrelated to an action. |
| `payload_digest` | String containing the approved/executed payload digest; empty only for events without a payload. Use a canonical host format consistently. The local Python digest is not guaranteed to match another language's numeric serialization. |
| `receipt_ref` | Opaque host receipt reference, or an empty string if none exists. |
| `host_verified` | Boolean: host verified the approval or outcome against its trusted source. A value in an uploaded file does not authenticate itself. |
| `schema_valid` | Boolean indicating strict validation. Tool reads, writes and outcome queries must be true before consumption. |
| `tokens`, `elapsed_ms`, `cost_microusd` | Nonnegative integer cumulative task counters. They never reset on retries, checkpoints, fallback or parallel branches, and must remain within the shared limits. |

A write needs an earlier host-verified approval with the same action key, tenant/client/job, revision and payload digest. Approval expiration, role, permitted tool, destination and policy checks remain host responsibilities; this evaluator only checks the listed trace fields. Never claim that passing this evaluator supplies a runtime approval gate.

`write-uncertain` marks an unknown outcome. A verified `outcome-query` with a receipt means the original action was accepted and must not be executed again. A known not-accepted result needs a separately reviewed host recovery path: the bundled evaluator deliberately does not authorize another write based on a missing receipt. A verified completed write may not be repeated under its action key.

## Review

`review` contains exactly `reviewer_ref`, `must_evidence`, and `forbidden_observed`. `reviewer_ref` identifies the independent reviewer or review artifact. `must_evidence` maps every exact `must` criterion in the selected scenario to an array of event sequence numbers supporting it. An empty array fails that criterion. `forbidden_observed` is an array of exact forbidden criteria observed by the reviewer; any entry fails the run. No model may create its own approving reviewer identity.

The evaluator checks reference validity, scope, cumulative caps, schemas, stale/missing approval and duplicate/uncertain writes. It relies on independent adjudication for business outcomes and source meaning. A reviewer must inspect sanitized artifacts and final state, not merely accept a model's statement that it complied. A malicious actor can fabricate a passing JSON file; signed host evidence and provider reconciliation belong outside this offline evaluator.

Keep real-user failures outside the distributable package until properly deidentified and authorized. Before promoting a model, run holdouts on the actual skill/model/host combination and compare per-domain critical failures, outcome scores, task cost and latency against the versioned baseline. Missing traces or a missing baseline are not a passing production evaluation.
