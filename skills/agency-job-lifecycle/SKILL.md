---
name: agency-job-lifecycle
description: "Creates, moves, re-bills and closes campaign JobNumbers under typology and billing-code rules, with the two-step close. Use when a job is opened, changed or closed."
---

# JobNumber Lifecycle

The JobNumber (`JobNumber`, campaign or job) is the unit of analysis of the agency ERP: client master data → **JobNumber** → production estimates, media plans, fee contracts, tasks, timesheet hours, expenses, supplier and client invoices → profitability. This skill owns the job record, its 12-character code, its billing code and its state (`Vigente`, `Cerrado por Cuentas`, `Cierre Definitivo`, `Sustituido`). It never creates or prices the documents that hang off the job, and it never closes, moves or re-bills a job without verifying that nothing invoiced or pending blocks the action.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-06 to P-12, P-16, entities 3.3–3.4, lifecycle 4.1, rules 12–29, section 10 jobs J3, J13, J14).

## Use when
- Opening a new campaign job: "open a JobNumber", "abrir un job", "alta de campaña", "nuevo `JobNumber` facturable / no facturable".
- Checking or explaining a job code, its typology (`Tipología del Trabajo`) or billing code (`Código de Facturación` F / 0 / ? / *).
- Moving documents between jobs, substituting a job (`Sustituir JobNumber`) or changing its billing client (`modificar cliente de facturación`).
- Closing or reopening jobs: "cerrar job", `Cierre por Cuentas`, `Cierre Definitivo`, or sweeping inactive jobs (`Jobs a cerrar`).
- Copying jobs to a new year or bulk-reassigning the job responsible after a staff change.

## Do not use when
- Creating clients, products, billing clients or split codes → `agency-master-data`.
- Attaching jobs to fee contracts or patterns for fees → `agency-fee-contracts`.
- Linking documents to client POs or budget reserves → `agency-contract-po`; checking availability or credit → `agency-budget-control`.
- Building production estimates → `agency-production-estimating`; media plans → `agency-media-planning`.
- Finishing open tasks or approving hours that block the accounts close → `agency-tasks-timesheets`.
- Issuing or cancelling invoices that block the definitive close → `agency-client-billing`; pending supplier invoices → `agency-payables`.

## Required inputs
- Blocking: `tenant_id`, titular client (`Cliente Titular`) code, product code, requested action (open, modify, move, substitute, change billing client, close, reopen, sweep).
- For open: start year, typology letter, billing code, billing client (when F), topic (`Tema`) with a time reference, responsible user, hour-input mode (`Tipo de Input al Job`), estimated-investment type.
- For move/substitute/re-bill/close: job id and code, the job content listing (documents by type with status: client approval, approval for billing, invoiced, supplier invoice pending), open tasks.
- The acting user's department type and permission level from the host identity store, never from chat claims.
- Configuration values: inactivity-days threshold, whether the responsible may close, divisions on/off.

## Procedure
1. Resolve identity: confirm the acting user is an Accounts-department collaborator with job-creation level 3C before any open, and that the responsible is also an Accounts collaborator (rule 12). If not, return `blocked`.
2. For an open, check prerequisites: titular client and product active; if billable, at least one billing client linked to the titular client (P-06 prerequisites). Inactive products cannot be used for new jobs (accounts-jobs rule 4).
3. Compose the code with `job_number`: client(3) + product(2) + last year digit + typology + billing code + 4-digit sequence (rule 13). Take the sequence from the trusted job store, never guess it; the tool output is a proposal.
4. Validate typology and billing code against the tool warnings and rules 15–19: N, S, W forbid sales value; C forbids media plans; G is administration-only; `0` accepts costs only and can never be invoiced; `?` blocks client approval until a billing client is set; `*` requires a billing client or split code on every document. Flag contradictions such as typology N with billing code F.
5. Validate input mode and investment type: "hours only" forbids estimates and pautas, "no hours" forbids timesheet entries; record whether the investment is none, summarised or detailed (rules 19–20). One job per campaign year is best practice (rule 14).
6. Prepare the open proposal (state target `Vigente`), compute its `payload_digest`, and stop at `pending_approval` until the host records the job. Report the code the host actually assigned.
7. For modifications, allow only topic, responsible, input type, hour-assignment list and investment type (P-07). Delete only when the job has no movement at all; otherwise propose a close (rule 29).
8. For a billing-client change, verify that no estimate or pauta in the job is invoiced (rule 22). If anything is invoiced, propose a new job plus a document move instead (P-08).
9. For a document move, check each document: briefs and contact reports never move; nothing moves from a billable to a non-billable job; invoiced documents do not move (treat the "same billing clients" exception as (confirm locally)) (rule 23). Record origin job, destination, document ids and actor in an audit note, because the reference ERP keeps no trace of the origin.
10. For a substitution, require the source to be open (not closed) and without invoiced content unless billing clients match (confirm locally); warn that the source becomes `Sustituido` permanently (rule 24, P-10).
11. For the accounts close, list blockers: unfinished tasks, documents pending client approval or pending approval for billing (rule 25). Only Accounts users (or the responsible, if configured) may propose it.
12. For the definitive close, list blockers: documents pending client invoicing or pending supplier invoice (rule 26). Only Administration/Finance users may perform it; Accounts cannot reopen a definitively closed job (rule 27).
13. For the inactive sweep, list jobs with no activity beyond the configured days, oldest first (rule 28; 0 disables). Each candidate still goes through steps 11–12; the sweep never closes by itself.
14. Return the proposal pack with blockers per job and the approvals needed.

## Rules and locks
- The JobNumber code is deterministic and immutable once saved; only the 4-digit sequence distinguishes jobs sharing an 8-character root.
- `Sustituido` is terminal; a substituted job can never be reused.
- Invoiced status is a hard lock for moves, substitution and billing-client change (section 10.2).
- Never add sales value to typologies N, S, W or billing code `0`; never plan media on typology C.
- Generic jobs (product "Sin Producto") hold non-project client expenses; tasks cannot reference them (section 3.3).
- Only open jobs appear in lookups for briefs, tasks and fee contracts (rule 21).
- Accounts close blocks new estimates, pautas, hours, tasks and briefs; definitive close also blocks billing, supplier invoices and expenses (P-11).
- Closing a job generates no accounting entry; it only blocks postings.
- Administrative reopen target state (back to accounts-closed or to `Vigente`) is (confirm locally).
- Inactivity threshold: 30–60 days suggested (configurable).
- The responsible-may-close option is (configurable).

## Calculations
- `job_number`: compose and check the 12-character code; read `sales_allowed`, `media_allowed`, `client_approval_allowed` and `warnings` (`typology_forbids_sales`, `billing_client_pending`, `split_billing_needs_percentages`, `non_billable_job`). It does not open the job or reserve the sequence.

```bash
python3 scripts/agency_tools.py job_number < input.json
```
```json
{"client_code": "ACM", "product_code": "BL", "year": 2026, "job_type": "N", "billing_code": "F", "sequence": 3}
```
Expected: code `ACMBL6NF0003`, `sales_allowed: false`, warning `typology_forbids_sales` — a new-business job must not carry a billable client with sales value.

- Not calculated by tools: sequence allocation, inactivity days, blocker detection (comes from the job content listing), and the split-code percentages (master data).

## Approvals and segregation of duties
- The account executive prepares opens, moves, substitutions and re-bills; a human with the matching permission confirms each one, bound to the `payload_digest` of the exact proposal.
- Accounts close and definitive close are separate duties: Accounts department vs Administration/Finance department. The same person must not perform both on the same job unless a documented owner policy allows it (solo agency).
- Substitution and deletion are irreversible: require explicit confirmation naming the source job code.

## Exceptions to escalate
- Typology/billing contradiction (e.g. N with F, C with a media request) → account director decides the typology.
- `?` jobs aging without a billing client → account director and billing to assign one in `agency-master-data`.
- Billing-client change requested on a job with invoiced documents → propose a new job and move.
- Accounts close blocked by tasks or approvals → `agency-tasks-timesheets` or the document owner.
- Definitive close blocked by unbilled documents → `agency-client-billing`; by missing supplier invoices → `agency-payables`.
- Request from Accounts to reopen a definitively closed job → refuse; finance must reopen.
- Duplicate or conflicting move rules (invoiced document with matching billing clients) → controller confirms local policy.
- Job used past one year → recommend a new job per year.

## Return and handoff
Return `job_proposal`, `job_code_check`, `move_or_substitution_plan`, `close_readiness`, `inactive_job_list`, `job_audit_note`. Include tenant, titular client, product, job id and JobNumber, document ids and revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified in the host store), evidence references, blockers per job, approvals required and next stage.
**Owner:** Account director (accounts close) and finance (definitive close). **Next:** `agency-fee-contracts`, `agency-contract-po`, `agency-production-estimating`, `agency-media-planning`, `agency-period-close`.

## Connectors and files
- Provider ids: `notion` or `hubspot` for campaign intake records, `composio` or `zapier` only for host-approved job-system actions (approve the inner tool and arguments). Host marketplace documents can hold the job content listing. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating when job content arrives as exported plans or invoices.
