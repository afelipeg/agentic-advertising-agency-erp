---
name: agency-tasks-timesheets
description: "Dispatch and track internal job tasks through their state machine and validate, approve and value timesheet hours at cost and sale with chargeability. Use when work requests, task follow-up or hour capture on JobNumbers need control. Do not approve your own hours or tasks, or book hours to closed jobs or closed timesheet periods."
---

# Tasks and Timesheets

Tasks and hours are the labour layer of each JobNumber: brief or contact report → **task (`Tarea`) dispatched to one recipient → work → timesheet hours (`Time Sheet`) → hour approval** → hourly fee settlement, job P&L and profitability. This stage owns task state transitions, task date checks, daily timesheet validation, the approval queue and the valuation of approved hours at internal cost and client sale rate. It never approves on behalf of the requester or the hour approver, and it never edits hours inside a closed timesheet period.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-21 tasks, P-22 JPM, P-23 timesheet closing and control, lifecycle 4.3 and 4.7, rules 50–56 and 66–68, rule 80 hour valuation, jobs J11, J12, J18) and [management-security.md](references/erp/management-security.md) (P-GN-06 to P-GN-08 entry, approval and past-hour edits, timesheet lifecycle in section 4, rules R-TS 21–38, R-SEC 44 approve-hours power, R-AP 58 task options, section 10.3 segregation).

## Use when
- "Enviar tarea", "pedido interno", "tarea pendiente", "reasignar tarea", "devolver tarea" for a JobNumber, or a task-delay report.
- Checking task dates: requested by Accounts, internal consensus, promised to client.
- "Cargar horas", "validar timesheet", "aprobar horas", "horas pendientes de aprobación", or the last-entry control (`Control de Horas TimeSheet`).
- Closing a timesheet period (`Cierre de TimeSheet`) or listing staff who stopped loading hours.
- Valuing approved hours at cost and sale, weighted hours, or chargeability against target.
- Bulk-finishing tasks so Accounts can close a job.

## Do not use when
- Closing or reopening the JobNumber after tasks finish → `agency-job-lifecycle`.
- Settling an hourly fee instalment with approved hours → `agency-fee-contracts`.
- Creating the production estimate attached to a task → `agency-production-estimating`.
- Collaborator rates, salary categories and departments → `agency-master-data`; user powers → `agency-access-governance`.
- Job or client profitability from valued hours → `agency-profitability`.

## Required inputs
- Blocking for tasks: `tenant_id`, JobNumber (open, non-generic), requester, single recipient, topic, description, the three dates, current task state and actor role.
- Blocking for timesheets: collaborator, date, lines (titular client, JobNumber, concept or task, hours in hundredths), the collaborator's configured daily total, allocation mode (`Time Sheet por Cliente`: client, JobNumber or task), timesheet closing date.
- Blocking for valuation: approved hours, internal hourly cost and client hourly rate per collaborator, currency.
- Configuration: approval on/off, business-days-only, hour cap, previous-day edit, self-reactivation window, concepts on/off, chargeability target and tolerance.

## Procedure
1. Task creation: require an open, non-generic JobNumber (rules 21, 53), exactly one system-user recipient plus any CC (rule 50), and date order requested-by-Accounts ≤ internal consensus ≤ promised-to-client (rule 51). Save leaves the task in `Standby`; send moves it to `Pendiente`.
2. If the task carries a production estimate, allow at most one and only for an open management month (rule 52); hand the estimate to `agency-production-estimating`.
3. Apply transitions only from the allowed states (rule 54): reassign when `Pendiente` or `Rechazada` (requester, coordinator or department reassigner); reject when `Pendiente` (recipient or coordinator, with reason); cancel only sent and pending tasks.
4. Apply progress conventions (rule 55): recipient finishes → 80% with actual hours; requester sends back → 50% and `Pendiente` with reason; requester approves → 100%, delivered-to-client date, immutable. Treat the 80% state as finished-by-recipient, not approved (gap 12).
5. Report delay as today − consensus date, and list overdue, rejected and standby tasks that will block the accounts close (job J12, rule 25).
6. For a job about to close, propose the bulk progress-100% action filtered by JobNumber for an Accounts user to confirm (P-21 bulk closing).
7. Timesheet day validation: every line in quarter-hour steps (0.25 h, i.e. hundredths divisible by 25) (R-TS 22); day total equal to the configured daily total (R-TS 23); weekend and holiday days filled with 0 when business-days-only is off (R-TS 26); hour cap respected when on (R-TS 27).
8. Route non-client time to the internal `AGC` generic jobs (vacation, sickness, new business, not assignable) (R-TS 24). Reject lines on closed jobs, closed timesheet periods (rule 67) or generic jobs when restricted (R-TS 32).
9. To split a block of hours across jobs, run `allocate` on quarter-hour units so lines stay in 0.25 steps and sum exactly to the day total.
10. Approval queue: when approval is on, only approved hours count in reports and fee imports (R-TS 29, accounts-jobs rule 47). Prepare approve/reject decisions per entry for the collaborator's assigned approver; rejected hours return to the collaborator.
11. Valuation: approved hours × internal hourly cost = labour cost; × client hourly rate = sale value (rule 80, R-TS 37). Weighted hours cap each day at 8 h for the weighted view (rule 68).
12. Chargeability: hours charged to clients ÷ total hours for last week and last 4 weeks, against the management target with tolerance (amber deviating, red excessive) (R-TS 35). Target values are (confirm locally) (management-security gap 11).
13. When approved hours sit on hourly-fee jobs, run `hourly_fee_settlement` as a burn preview against covered hours and hand the result to `agency-fee-contracts`.
14. Timesheet closing: propose a cut-off date and a default JobNumber for empty days; the close locks entry and edit up to that date and can be reopened per user (P-23).

## Rules and locks
- One recipient per task; recipients must be system users (rule 50).
- An approved task (100%) is immutable (rule 55).
- Tasks cannot reference generic jobs (rule 53).
- Hours only in quarter-hour increments; a day saves only when it equals the daily total (R-TS 22–23).
- Closed timesheet periods block entry and edit; reopening is per user and audited (rule 67).
- Previous-day edits need the `Permite Modif. Horas Día Anterior` flag; self-reactivation within N days (configurable) (R-TS 28).
- Unapproved hours are invisible to profitability and fee imports.
- Hours of now-inactive clients are hidden by the "active clients only" filter; always include them in completeness checks (R-TS 38).
- Auto-copies to group heads, e-mails to creatives and edit rights for CC users are (configurable) (rule 56).

## Calculations
- `allocate`: split quarter-hour units (or a valued amount) across jobs by integer weights with exact conservation. For hours, pass the number of quarter hours as `amount_minor` and the ISO no-currency code `XXX`.
- `hourly_fee_settlement`: preview approved hours against an hourly contract's covered hours; read `overage_hours_hundredths`, `unused_hours_hundredths` and `per_person`.

```bash
python3 scripts/agency_tools.py allocate < input.json
```
```json
{"currency": "XXX", "amount_minor": 32, "weights": [{"target_id": "ACMBL6AF0012", "weight": 5}, {"target_id": "ACMBL6CF0004", "weight": 3}]}
```
Expected: 20 and 12 quarter hours (5.00 h and 3.00 h), total 32 (8.00 h).

- Not calculated by tools: day-total and quarter-step validation, chargeability ratios and traffic lights, and cost or sale valuation; compute them explicitly in integer hundredths and minor units and show the formula. Rates come from the collaborator master, not from chat.

## Approvals and segregation of duties
- The requester approves a task; the recipient cannot approve their own delivery.
- Hours are approved only by the collaborator's assigned approver holding the approve-hours power (R-SEC 44); a collaborator never approves their own hours (section 10.3 item 5).
- Timesheet period close and reopen are performed by an authorized administrator; the agent prepares the list and cut-off proposal bound to a `payload_digest`.
- Sending tasks or reminders to people is a message action and needs human confirmation; external addresses need explicit confirmation (R-COM 63).

## Exceptions to escalate
- Task dates out of order → requester to fix before sending.
- Task on a generic or closed job → account executive to pick an open job.
- Rejected or overdue tasks blocking a job close → traffic manager.
- Day total mismatch or non-quarter steps → collaborator to correct.
- Hours pending approval at month end → approver; hourly fee import waits.
- Collaborator without rates or approver → `agency-master-data`.
- Departed user still owning tasks or approvals → `agency-access-governance` for reassignment.
- Chargeability red for a team → team lead review.

## Return and handoff
Return `task_actions`, `task_delay_report`, `timesheet_validation`, `hour_approval_queue`, `hour_valuation`, `chargeability_report`, `timesheet_close_proposal`. Include tenant, client, job ids and JobNumbers, task numbers, collaborator ids, period, revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Traffic manager and team leads. **Next:** `agency-fee-contracts`, `agency-job-lifecycle`, `agency-profitability`.

## Connectors and files
- Provider ids: `notion` or `hubspot` for task intake, `composio` or `zapier` only for host-approved task-tool actions (approve the inner tool and arguments). Host marketplace calendars, email and spreadsheets may hold timesheet exports. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` covers plan|broadcast-order|emission|ooh|invoice|rating only, so treat timesheet spreadsheets as unverified evidence and validate line by line.
