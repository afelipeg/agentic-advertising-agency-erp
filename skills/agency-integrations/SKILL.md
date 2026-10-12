---
name: agency-integrations
description: "Plans which connectors each ERP stage needs (ad platforms, ledgers, e-invoicing, docs), verifies live access and falls back to files. Use when connecting tools. Never asks for secrets."
---

# Wire Connectors per ERP Stage

Integrations is a foundation stage: it runs before any stage that reads or writes outside the host and again whenever a stage reports missing access. It sits beside the whole circuit (intake → planning and buying → activation → delivery → supplier invoices → billing and e-invoicing → payments → close and reporting) and owns the capability inventory, the per-stage wiring plan, the access matrix and the schema review. It never holds credentials, never grants itself permissions and never reports a connector as working without a verified read.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [management-security.md](references/erp/management-security.md) (P-SY-05 e-invoicing web service, P-SY-07 email, P-SY-12 consolidation connections, P-SY-14 supplier portal, P-RP-01 reporting interface, P-US-11 external credentials, P-AU-04 access report; §5 R-SEC 46–47, R-COM 63; §10.3 control model 1–3, 6–10). Stage wiring table: [wiring-guide.md](references/wiring-guide.md); providers: [provider-registry.json](references/provider-registry.json).

Agency policy: apply `roles`, `connectors` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Connect Meta / Google Ads / Xero / the PAC", "conectar el `facturador electrónico`", "¿qué conectores necesito para esta etapa?".
- A sibling skill returned `blocked` for missing tool, scope, account or schema.
- Choosing between a marketplace app, first-party MCP, aggregator, official API adapter or files for a stage.
- Reviewing an aggregator (Composio, Zapier, Supermetrics) before enabling inner tools.
- Planning e-invoicing (`mx-cfdi-pac`, `arca-afip`), FX rates (`banxico-sie`), ad-server or DOOH proof feeds.

## Do not use when
- Granting users roles or approval powers → `agency-access-governance`.
- Mapping external codes onto masters → `agency-master-data`.
- Running a stage once tools are wired: activation → `agency-campaign-activation`; e-invoice issuance → `agency-tax-compliance`; ledger postings → `agency-general-ledger`.
- Multi-stage routing → `agency-orchestrator`.

## Required inputs
- **Blocking:** host type (Claude, Codex, web assistant, CLI); the stages in scope; `tenant_id` and, per stage, `client_id` and the platform account ids from trusted records.
- **Blocking for writes:** the host's approval store, sandbox and idempotency support; without them the stage stays read-only or draft.
- Existing marketplace apps and MCP servers already enabled; the agency's approved tool policy.
- Country and fiscal context for e-invoicing and FX sources.
- Ask only for missing material inputs. Never ask for credentials in chat.

## Procedure
1. **Inventory what exists.** List enabled marketplace apps/plugins and MCP servers with their actual tool names and schemas. Follow the registry's selection order: enabled marketplace app → official MCP → reviewed aggregator → reviewed official API adapter → files and human handoff. When `AGENCY.md` lists `connectors.enabled`, only those registry ids are candidates; adding one is a policy change made in AGENCY.md by its owners, not by this skill.
2. **Map needs per stage.** For each in-scope stage, list required reads and writes from the wiring table: intake and masters (documents, CRM), planning and ranking (platform reports, licensed ratings), buying and activation (ad-platform writes), delivery (platform reports, monitoring, proof of play), supplier invoices and ledger, client invoice and e-invoice authorization, collections, supplier payment, close and parent-company reporting (P-RP-01).
3. **Select candidates** from the registry by role, not brand. A query MCP never implies mutation; `google-ads` documented tools are read-only. Mark aggregator capabilities "discover first".
4. **Request authentication through the host** (OAuth or backend credential store). External-system credentials belong in the host vault (P-US-11); consolidation and e-invoicing certificates stay server-side (P-SY-05, P-SY-12).
5. **Verify identity with one permitted read:** account or company id, owner relationship, currency, timezone, a small date window and full pagination. Record the response schema version.
6. **Review schemas.** Validate output against a reviewed strict schema. Quarantine extra fields, invalid types, truncated pages and account, currency or period mismatches. No schema → evidence for drafts only.
7. **Apply least privilege.** Allowlist only the inner tools the stage needs. For `composio` and `zapier`, approve inner tool and arguments, never the meta-tool; deny workbench and bash. Map each tool to a screen and access level and field visibility (create ≥4, modify ≥3, delete ≥2, special 1) so cost fields are stripped for C/D users (§10.3 items 2–3).
8. **Gate writes.** Writes need host approval bound to payload digest, idempotency keys, sandbox testing first (`paypal` sandbox, `xero` demo company, `stripe` test account), and readback. Configuration changes to circuits or e-invoicing endpoints are high-risk (§10.3 item 6).
9. **Wire communications safely.** Email and messaging only to registered contacts; external sends need confirmation of external addresses (R-COM 63).
10. **Plan file mode** for every stage without a sufficient connector: templates, normalizer kind and the human who executes in the legacy system and uploads its receipt.
11. **Report statuses separately:** documented, configured, authenticated, read-tested, write-approved. Never collapse them.

### Stage wiring map (candidates only; discover before use)
| ERP stage (sibling skill) | Reads | Writes (gated) | Candidate provider ids | File-mode kind |
|---|---|---|---|---|
| Intake, masters (`agency-onboarding`, `agency-master-data`) | CRM, contacts, documents | record creation in authorized scope | `hubspot`, `notion`, `composio`, `zapier` | reviewed CSV manifest |
| Ranking, planning (`agency-media-ranking`, `agency-media-planning`, `agency-digital-planning`) | platform reports, licensed ratings | none | `google-ads`, `google-analytics`, `meta-ads`, `supermetrics`, `synter`, `meridian` | rating, plan |
| Buying, activation (`agency-media-buying`, `agency-campaign-activation`) | account state, readback | orders, paused campaigns | `meta-ads`, `amazon-ads`, `synter`, `ryze`, `zernio` | broadcast-order |
| Delivery (`agency-transmission-control`, `agency-delivery-reconciliation`) | airings, proof of play, ad-server logs | none | `broadsign`, `vastlint`, `supermetrics`, `monid` | emission, ooh |
| Supplier invoices, ledger (`agency-payables`, `agency-general-ledger`) | bills, chart of accounts | bill drafts, entries | `xero`, `quickbooks` | invoice |
| Client billing, fiscal (`agency-client-billing`, `agency-tax-compliance`) | invoices, authorization status | invoice drafts, stamping requests | `stripe`, `paypal`, `xero`, `mx-cfdi-pac`, `arca-afip` | invoice |
| Cash, FX, close (`agency-collections`, `agency-payment-run`, `agency-accruals-revaluation`) | settlements, statements, rates | payment proposals only | `stripe`, `paypal`, `xero`, `banxico-sie` | statement CSV |
| Production assets (`agency-production`) | designs, exports | edits in authorized workspace | `canva`, `figma` | asset manifest |

## Rules and locks
- Installing skills or apps connects no account; registry entries are documentation, not tested access.
- Credentials, tokens, certificates and bank details never enter prompts, skills, artifacts or traces.
- Deny unknown capabilities by default. Pin connector versions; re-review on version change.
- One connector account maps to one tenant and client scope; no cross-client cache or credential reuse.
- Every agent action runs as a named user or a service user, never anonymously (§10.3 item 1); service users get only their stage's allowlist.
- Retry reads at most three times with backoff; never retry auth, schema or policy errors unchanged; a timed-out write is `uncertain` and is looked up, not recreated.
- E-invoicing, FX-rate and bank-file connectors feed fiscal or money documents: test in sandbox, verify country eligibility, and keep the legacy route available until reconciled (agency policy).
- Supplier-portal behaviour flags (mandatory PDF, partial PO invoicing, rate differences, other currency) are configuration of the portal, not of the connector; route changes to the controller (P-SY-14).

## Calculations
- No deterministic calculation tool applies to this stage. Use the tool contracts reference only to confirm which local calculations other stages can run offline.
- Not calculated here: FX rates, tax rates, fees or amounts. Connectors such as `banxico-sie` supply rates as evidence; the consuming stage validates them.

## Approvals and segregation of duties
- The operations lead prepares the wiring plan; the workspace owner or system administrator approves OAuth scopes and allowlists; finance or the controller approves any write capability on ledgers, invoicing, e-invoicing or payments.
- Write enablement, scope expansion and endpoint changes need an authenticated human approval bound to the exact allowlist, account and revision, verified by the host.
- The person who wires a write capability does not also approve its first production write (agency policy).

## Exceptions to escalate
- Discovered tool lacks an output schema → host engineering to review one; stage stays draft.
- Account owner, currency or timezone mismatch on the identity read → stop; account manager and `agency-master-data`.
- Aggregator exposes broad execution or bash → deny; security administrator.
- Registry endpoint unverified (for example `ryze`) → mark gap; obtain endpoint through authorized onboarding.
- E-invoicing certificate or PAC credentials requested in chat → refuse; route to host vault and tax lead.
- Connector returns extra or truncated data → quarantine; provider review.
- Stage needs writes but host lacks approval store or sandbox → keep read-only; operations lead.
- Payment or payout tool proposed as default rail → treasury lead; bank execution stays human until approved.

## Return and handoff
Return `capability_inventory`, `stage_wiring_plan`, `access_matrix`, `schema_review`, `connection_requests`, `file_mode_plan`, `gaps`. Include tenant/client IDs, stage, provider ids, account ids, connector versions, status per capability (documented/configured/authenticated/read-tested/write-approved), evidence references, blockers, approvals required and next stage.
**Owner:** Operations lead. **Next:** `agency-access-governance`, then the requesting stage or `agency-orchestrator`.

## Connectors and files
- Ad platforms and analytics: `google-ads`, `google-analytics`, `meta-ads`, `amazon-ads`, `synter`, `ryze`, `supermetrics`, `zernio`, `monid`, `vastlint`, `meridian`. Creative: `canva`, `figma`. Work and CRM: `notion`, `hubspot`, `composio`, `zapier`. Finance: `xero`, `quickbooks`, `stripe`, `paypal`. Fiscal and rates: `mx-cfdi-pac`, `arca-afip`, `banxico-sie`. DOOH proof: `broadsign`. Host marketplace documents/email/warehouse are generic options. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating.
