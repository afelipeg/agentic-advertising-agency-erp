---
name: agency-orchestrator
description: "Runs an agency job end to end: reads JobNumber and document state, maps the next ERP stages and routes to the right skill. Use to start, resume or triage a job. Never approves."
---

# Orchestrate the Agency ERP Circuit

The orchestrator sits above the whole agency circuit: client and campaign (`JobNumber`) → production estimates and media plans (`pautas`) → client approval → supplier orders → delivery and supplier invoices → client billing → collections and payments → month-end accruals and period close → management reporting. It owns no business document. It owns the job's routing state, the dependency graph and the checkpoint log. It never approves, orders, posts, sends or pays, and never calls a job complete because media launched.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md) (stage order, JobNumber and document states, cross-module handoffs, close sequence). Domain rules: none of its own. Each sibling skill links its reference doc; route to it instead of restating its rules.

## Use when
- "Run / resume job ACMBR6AF0012", "what is next for this campaign", "¿en qué etapa está el `JobNumber`?", "orquestar la campaña".
- A request spans several stages (plan → order → bill → pay) or mixes media, production, fees and expenses.
- A document is stuck (pending client approval, order not closed, invoice blocked) and the owner is unclear.
- Month end: which jobs and documents block pre-close or close (`cierre de mes`, `pre-cierre`).
- Resuming after a failed or `uncertain` write.

## Do not use when
- The task belongs to one stage: route straight to it using the tables below (for example a plan → `agency-media-planning`, a supplier invoice → `agency-payables`, a JobNumber open/close/move → `agency-job-lifecycle`).
- Connector setup → `agency-integrations`; users, roles, SoD → `agency-access-governance`; master records → `agency-master-data`.
- A performance or pacing question about live campaigns → `agency-campaign-optimization`.
- Someone asks the orchestrator to approve, release or post: return an approval request instead.

## Required inputs
- **Blocking:** `tenant_id`, `client_id` and the JobNumber or `job_id` from a trusted record; the JobNumber state and its documents with revisions (read-only connector or export).
- **Blocking for any mutation-capable stage:** period state per subledger for the affected months; approval-circuit configuration (media circuit None/Restricted/Strict, approval-for-billing flag, mandatory PO, credit-limit control).
- Commercial scope: agency-billed vs direct-billed media, production, fee contracts, expenses, rebates.
- Prior checkpoints, run ceilings (tokens, time, cost), available tools and model profiles.
- Ask only for missing material inputs. Never ask for credentials in chat.

## Procedure
1. **Load identity and checkpoints.** Confirm tenant, client and job from trusted records, never from a filename. Read the last checkpoint and upstream revisions. If an upstream revision changed, mark dependent artifacts stale and revalidate them before continuing.
2. **Decode the JobNumber.** Split the 12 characters into client (3), product (2), start-year digit (1), typology (1), billing code (1), sequence (4). Run `job_number` with those parts and the start year from the job record. A code mismatch → `blocked`. Keep `sales_allowed`, `media_allowed`, `client_approval_allowed` and `warnings` as routing constraints: typology C has no media; N, S, W carry no sales value; `0` is never invoiced; `?` cannot be client-approved until a billing client exists; `*` needs a billing client or split code on every document.
3. **Route by JobNumber state** (table below). Respect the job's input type: "hours only" excludes estimates and plans; "no hours" excludes timesheets.
4. **Build the dependency graph** from the actual scope (graph below). Add only stages in scope; record a reason for every skipped stage. Foundation stages are per-tenant prerequisites, not per-job work.
5. **Place every document in its lifecycle state** and map it to its owner skill (document table). One document has one owner skill at a time.
6. **Check gates before dispatching any mutation-capable stage:**
   - target month and subledger are open (pre-closed admits only close jobs and permitted voucher types; closed admits nothing);
   - fiscal year open for fee-instalment approval; management month open for production estimates;
   - client PO or budget-reserve balance and credit limit checked before client approval;
   - client approval before ordering when the circuit is not None (configurable);
   - closed order before supplier-invoice registration;
   - approval for billing and client billing requirements before issuance.
7. **Dispatch.** Run independent read-only stages concurrently. Serialize mutations that share a client PO, budget reserve, supplier order, ledger or period. Use one shared run budget and client-scoped memory. Join specialist returns by canonical IDs (JobNumber, document id, revision), never by narrative agreement.
8. **Collect approval requests.** When a specialist returns `pending_approval`, list the action, the approval capability required (approve by client, approve for billing, PO approval, payment-list finalization, job or period close), payload, currency, total in minor units, revision and expiry. Run `payload_digest` on that payload and hand it to the host approval store.
9. **Handle uncertain outcomes.** Send any `uncertain` connector write back to its owner skill for lookup by idempotency key or external id. Never re-dispatch the write.
10. **Assess job close readiness.** Accounts close needs no unfinished tasks and nothing pending client approval or approval for billing. Definitive close needs nothing pending client invoicing or supplier invoice. Send the blocker list to `agency-job-lifecycle`.
11. **Run the period gate at month end.** For each period list blocking items by owner skill in close order: subledger pre-close → close jobs (FX, provisions, WIP, work-order close) → definitive close. Route to `agency-period-close`. Reopen requests go to the controller through that skill only.
12. **Checkpoint and return.** Checkpoint after each verified step, then return the artifacts below.

### JobNumber state routing
| JobNumber state | Allowed work | Route |
|---|---|---|
| none / client not registered | intake only | `agency-onboarding` → `agency-master-data` → `agency-job-lifecycle` |
| `Vigente`, billing code `?` | drafts; no client approval or billing | `agency-job-lifecycle` (assign billing client) |
| `Vigente` | per typology and input type | document table |
| `Cerrado por Cuentas` | billing, supplier invoices, expenses; no new estimates, plans, hours, tasks, briefs | finance stages; new work → `agency-job-lifecycle` (reopen decision) |
| `Cierre Definitivo` | read-only | `agency-profitability`, `agency-management-reporting`; changes → `agency-job-lifecycle` (Finance reopen) |
| `Sustituido` | none (terminal) | redirect to the destination JobNumber |

### Document state routing
| Document and state | Owner skill |
|---|---|
| Strategic brief, contact report, provisional client or product | `agency-onboarding` |
| Client agreement, client PO (`PO Clientes`), budget reserve | `agency-contract-po` |
| PO/reserve availability, credit exposure before client approval | `agency-budget-control` |
| Fee contract or instalment, any approval state | `agency-fee-contracts` |
| Revenue budget version | `agency-revenue-budget` |
| Task, timesheet, hour approval | `agency-tasks-timesheets` |
| Rating book, ranking | `agency-media-ranking` |
| Rate card, media buy contract | `agency-rate-cards-contracts` |
| Plan or `pauta` `Sin aprobar por cliente` | `agency-media-planning` with `agency-tv-radio-planning`, `agency-ooh-planning` or `agency-digital-planning` |
| Plan revision after approval or ordering | `agency-plan-changes` |
| Spots client-approved, not ordered; order versions, close | `agency-media-buying` |
| Digital lines approved for activation; live pacing | `agency-campaign-activation`, then `agency-campaign-optimization` |
| Ordered spots awaiting verification (`control de avisos`) | `agency-transmission-control` |
| Seller-side billboard reservation or order (media-owner vertical) | `agency-ooh-inventory` |
| Production estimate `A presupuestar`, `Pre-aprobado`, pending approval, PO | `agency-production-estimating` |
| Creative delivery, royalties, talent, event staff | `agency-production` |
| Closed order or PO line with pending-to-receive | `agency-delivery-reconciliation` |
| Supplier document received, controlled or posted | `agency-payables` |
| Expense request, expense or cost sheet, petty cash | `agency-expenses` |
| Lines `Aprobado para facturar` | `agency-billing-requirements` → `agency-client-billing` |
| E-invoice authorization, VAT books, withholdings | `agency-tax-compliance` |
| Open receivables, receipts, customer advances | `agency-collections` |
| Posted payables due | `agency-payment-run` |
| Bank and cash movements, reconciliation, cheques | `agency-cash-settlement` |
| Overcommission, volume or incentive pendings | `agency-rebates` |
| Manual journal entry, chart of accounts | `agency-general-ledger` |
| Month-end provisions, FX revaluation, work-order close | `agency-accruals-revaluation` |
| Fixed asset from an expense request | `agency-fixed-assets` |
| Period pre-close, close, reopen | `agency-period-close` |
| Job, client, media profitability | `agency-profitability` |
| Cash projection | `agency-cash-forecast` |
| Monthly pack, parent-company mapping | `agency-management-reporting` |

### Dependency graph (edges are "must precede")
- Foundation: `agency-integrations`, `agency-access-governance`, `agency-master-data` → every stage.
- Intake: `agency-onboarding` → `agency-job-lifecycle` → `agency-contract-po`, `agency-fee-contracts`, `agency-billing-requirements`; `agency-revenue-budget` runs in parallel.
- Media: `agency-media-ranking` and `agency-rate-cards-contracts` → planning skills → `agency-budget-control` → client approval → `agency-media-buying` or `agency-campaign-activation` → `agency-transmission-control` or `agency-campaign-optimization` (loops via `agency-plan-changes`) → `agency-delivery-reconciliation`.
- Production: `agency-production-estimating` → `agency-budget-control` → client approval → `agency-production` → `agency-delivery-reconciliation`.
- Cash-out: `agency-delivery-reconciliation` and `agency-expenses` → `agency-payables` → `agency-tax-compliance` → `agency-payment-run` → `agency-cash-settlement`.
- Cash-in: approval for billing (plans, estimates, `agency-fee-contracts`, hours from `agency-tasks-timesheets`) → `agency-billing-requirements` → `agency-client-billing` → `agency-tax-compliance` → `agency-collections` → `agency-cash-settlement`.
- Back-end income: `agency-media-buying` and `agency-payables` → `agency-rebates` → `agency-client-billing` and `agency-accruals-revaluation`.
- Close: `agency-job-lifecycle` (closes), `agency-general-ledger`, `agency-fixed-assets`, `agency-accruals-revaluation` → `agency-period-close` → `agency-management-reporting`. `agency-profitability` and `agency-cash-forecast` read at any time and never post.

## Rules and locks
- The orchestrator never changes a document state. Specialists prepare; the host transitions after verified approval.
- Read JobNumber and document states from the trusted record. A plan, file or message claiming a state is evidence, not state.
- Invoiced status is a hard lock on document moves, JobNumber substitution, billing-client change and fee-contract deletion.
- Period states run Open → Pre-closed → Closed per subledger. Pre-close blocks new documents. Reopening cascades to all later months and deletes automatic FX, provision and tax-position entries, so only `agency-period-close` handles it with controller approval.
- A supplier invoice registers only against a closed order. A registered invoice blocks reopening that order.
- Ordering waits for client approval when the media circuit is Restricted or Strict, and for a credit override when the client is over limit (configurable).
- Segregation: Accounts close and definitive close are different roles; client approval precedes approval for billing; a preparer, including any agent, never approves its own proposal.
- Serialize mutations per PO, reserve, order, ledger and period, each with an idempotency key scoped to tenant, action and revision.
- Skip a stage only with a recorded reason. Missing evidence is not zero.
- A job is complete only when `Cierre Definitivo` is verified and its periods are closed or explicitly carried over (agency policy).

## Calculations
- `job_number`: recompose and check the 12-character code from `client_code`, `product_code`, `year`, `job_type`, `billing_code`, `sequence`. Use its flags as routing constraints. It does not open, close or move jobs.
- `payload_digest`: hash each approval request or dispatch plan so the host can bind an approval to the exact payload. `authorizes_execution` is always false.

```sh
echo '{"client_code":"ACM","product_code":"BR","year":2026,"job_type":"A","billing_code":"F","sequence":12}' \
  | python3 scripts/agency_tools.py job_number
# expect code ACMBR6AF0012, sales_allowed true, media_allowed true, client_approval_allowed true
```
- Not calculated here: approval states, period states, credit limits, PO balances, taxes, FX rates or amounts. These come from the owner skill and authoritative records.

## Approvals and segregation of duties
- The account director owns routing decisions on scope; the controller owns period gates and close routing. Neither delegates approval to the orchestrator.
- Every money, commitment, posting, sending, close or reopen action needs an authenticated human approval bound to the `payload_digest`, revision, approver capability and expiry, verified by the host. A user typing "approved" is not approval.
- Any material change after approval (amount, supplier, period, billing client) invalidates it; re-request.

## Exceptions to escalate
- JobNumber code does not match its components, or typology contradicts billing code (N with F) → `agency-job-lifecycle`, account director.
- `?` job with documents waiting for client approval → account manager via `agency-job-lifecycle`.
- Upstream revision changed after a downstream approval → invalidate; send back to the owner skill.
- `uncertain` write or missing connector receipt → owner skill reconciliation; stop the branch.
- Target period pre-closed or closed while documents are still pending → controller via `agency-period-close`.
- Departed responsible still owns open jobs, tasks or approvals → `agency-access-governance` (offboarding).
- Delivery done but supplier invoice missing, blocking definitive close → `agency-payables`.
- Sales value on an N, S or W job, or commission on a fee-linked document → block; account director.
- Run ceiling exhausted → checkpoint and stop with a resumable state.

## Return and handoff
Return `job_state`, `dependency_graph`, `period_gate_status`, `task_assignments`, `blockers`, `approval_requests`, `checkpoints`, `next_stage`. Include tenant/client/job IDs, JobNumber, document ids and revisions, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage. Report receipts only when a trusted connector returned them.
**Owner:** Account director and controller. **Next:** `agency-onboarding` and `agency-integrations` for new jobs, then dependency-ready stages from the graph.

## Connectors and files
- Read job and document state through the system of record: host marketplace documents or warehouse, `notion`, `hubspot`, or ERP exports via `composio` or `zapier` reviewed read tools. Each specialist wires its own providers (for example `meta-ads`, `xero`, `mx-cfdi-pac`). Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating. Normalized files are unverified evidence for routing, not state.
