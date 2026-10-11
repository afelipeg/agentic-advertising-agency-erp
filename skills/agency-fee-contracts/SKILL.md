---
name: agency-fee-contracts
description: "Draft fixed and hourly client fee contracts: instalments, media/production split, JobNumber attachment by list or pattern, monthly hourly settlement and two-step approval. Use when agency remuneration is a fee instead of commission. Do not add agency commission to fee-linked documents or recognize advances as revenue automatically."
---

# Fee Contracts

Fee contracts replace or complement commission: client agreement → **fixed-fee (`Contrato de Fee Fijo`) or hourly-fee (`Contrato de Fee por Horas`) contract** → per instalment a fee `pauta` (media share) and/or a fee production estimate (production share) → client approval → approval for billing → `Cuotas de Fee` billing. This stage owns the contract header, its jobs or pattern, the instalment table, the monthly hours import for hourly contracts and the approval state per instalment. It never issues invoices, never edits the read-only fee documents by hand and never charges commission on fee-linked estimates.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [accounts-jobs.md](references/erp/accounts-jobs.md) (P-13 fixed fee, P-14 hourly fee and P-14a–e, P-15 staff-hour estimate, P-16 patterns, entity 3.5, lifecycle 4.2, rules 30–49, section 6 observation code 22, job J4–J7) and [expenses.md](references/erp/expenses.md) (P20 fee-contract cross-reference: contract types, separate media and production instalments, no commission on fee-linked estimates).

## Use when
- "Armar contrato de fee", "fee mensual", "retainer", "fee por horas", "honorarios fijos" for a titular client.
- Attaching JobNumbers to a contract by list, by percentage or by `Patrón de JobNumber`, including self-assignment prompts.
- Running the monthly hours import of an hourly contract (`Importar horas`) and computing overage at client rates.
- Approving instalments by client or for billing, or explaining why an instalment cannot be approved.
- Building a staff-hour estimate (`Estimación de Dedicación Horaria`) to price or monitor a fee.

## Do not use when
- Opening, moving or closing the jobs themselves → `agency-job-lifecycle`.
- Capturing, approving or valuing timesheet hours → `agency-tasks-timesheets`.
- Client POs or reserves that cap the fee → `agency-contract-po`.
- Issuing the fee instalment invoices → `agency-client-billing`; accrual of fee revenue at month end → `agency-accruals-revaluation`.
- Supplier rebates or overcommissions → `agency-rebates`; job profitability → `agency-profitability`.

## Required inputs
- Blocking: `tenant_id`, titular client, signed agreement, contract kind (fixed or hourly), contract type (fixed distribution, dynamic, dynamic with self-assignment), validity, instalment months and amounts, single currency and exchange rate if foreign.
- Blocking: billing criterion (defined billing client or split code), media/production distribution percentages, fee production type and fee media configured against fee revenue accounts flagged with observation code 22 (P-13 prerequisites).
- Fixed distribution: JobNumbers with a percentage each. Dynamic: the JobNumber pattern and allocation table.
- Hourly: covered hours per instalment, approved timesheet hours by collaborator on the contract's jobs, client rates by salary category, manual resource lines, adjustment coefficients, overage policy from the agreement.
- Accounting calendar showing which fiscal periods are open.

## Procedure
1. Verify the prerequisites: fee GL accounts with observation code 22, fee media type and media, fee production type declared in configuration (P-13). Missing setup → `blocked`.
2. Check currency: one currency per contract; a foreign currency needs an exchange rate; different currencies need separate contracts (rule 30).
3. Build the instalment table with `installment_schedule` when amounts are even, or from the agreement when months differ (not every month needs an amount). Contract total = Σ instalments (rule 31).
4. Split each instalment between media and production with `allocate` using the distribution percentages (default 50/50, may be 100/0). When both shares are non-zero, two billable items per month are generated and invoiced separately (rule 32).
5. Attach jobs: only open jobs (rule 21). Fixed distribution: give each job a percentage summing to 100; use `allocate` to spread each share across jobs. Dynamic: jobs matching the pattern are included without percentage and fees distribute proportionally; the basis is (confirm locally) (rule 33, gap 4). Self-assignment: on job creation the user is asked whether to include a matching job.
6. Enforce attachment locks: a job belongs to one contract unless multi-contract configuration is on (rule 36); fixed-distribution contracts accept no new jobs after the first instalment is invoiced (rule 35); jobs created later may be added manually otherwise (rule 34).
7. Mark every estimate linked to the contract's jobs as commission-free; flag any agency commission (`Servicio de Agencia`) on a fee-linked estimate as a blocker (rule 37).
8. For hourly contracts each month: take only supervisor-approved hours when timesheet approval is on (rule 47); apply adjustment coefficients and manual resource lines (rule 45); late hours fall into the next import (rule 46).
9. Run `hourly_fee_settlement`: implied rate = instalment / covered hours (rule 42); within quota the agreed instalment is billed (rule 43); excess hours are valued at each collaborator's client rate and billed on top (rule 44). The tool allocates the excess pro rata to hours — which person's hours count as excess is (confirm locally) (gap 3). Save the instalment as pending client approval (lifecycle 4.2).
10. Check the period gate: no approval for an instalment whose fiscal year is not open in accounting (rule 40).
11. Prepare the approval proposal per instalment or for all: client approval first, then approval for billing (rule 41). Compute its `payload_digest`.
12. On approval for billing, the system generates the fee `pauta` and fee estimate per instalment; they are read-only and owned by the contract (rule 38). Report their numbers only when returned by the host.
13. Deletion is possible only while no instalment is invoiced (rule 39); otherwise propose deactivation or a contract amendment.

## Rules and locks
- No agency commission on any estimate linked to a fixed or hourly fee contract (rule 37).
- Fee-generated pautas and estimates are read-only (rule 38).
- Media and production fee items are invoiced separately; plans, estimates and fees never share an invoice (receivables rule 1).
- Client approval precedes approval for billing; each needs its user flag (`Aprueba por Cliente`, `Aprueba para Facturar`) (rule 41).
- Instalment hours import is repeatable and reversible until approval (rule 48).
- A JobNumber in more than one contract is (configurable) (rule 36).
- Contract state follows `Sin Aprobar por Cliente` → `Aprobado por Cliente` → `Aprobado para Facturar` → `Facturado Parcialmente` → `Facturado Total`; header state derivation from mixed instalments is (confirm locally).
- Advances, invoice dates, service delivery and revenue recognition are separate; ask the controller for recognition policy (agency policy).
- Timesheet by JobNumber is mandatory for hourly contracts (P-14 prerequisites).

## Calculations
- `installment_schedule`: `gross_minor`, `advance_bps`, `installments`, `start_month` → exact monthly amounts.
- `allocate`: split an instalment into media/production or across jobs by integer weights with exact conservation.
- `hourly_fee_settlement`: `instalment_minor`, `covered_hours_hundredths`, `hours` (person, approved hours, client rate), `overage_policy` → implied rate, overage hours and amount, total billable, per-person overage.

```bash
python3 scripts/agency_tools.py hourly_fee_settlement < input.json
```
```json
{"currency": "MXN", "instalment_minor": 5000000, "covered_hours_hundredths": 10000, "hours": [{"person_id": "C-01", "approved_hours_hundredths": 7000, "client_rate_minor": 60000}, {"person_id": "C-02", "approved_hours_hundredths": 4200, "client_rate_minor": 45000}], "overage_policy": "bill_at_client_rate"}
```
Expected: `implied_rate_minor` 50000, `overage_hours_hundredths` 1200, `overage_minor` 652500, `total_billable_minor` 5652500.

- Not calculated by tools: client rates by salary category, exchange rates, VAT, revenue recognition and the dynamic-distribution basis; take them from the rate table, the host FX source and the controller.

## Approvals and segregation of duties
- The account director prepares the contract and monthly imports; the account lead validates hours before import (P-14 prerequisites).
- A user with `Aprueba por Cliente` approves by client; a different step by a user with `Aprueba para Facturar` approves for billing. The agent cannot approve its own proposal; each approval is bound to the `payload_digest`, instalment, amount and revision.
- Unapproving by client or for billing is allowed only before invoicing and needs the same flags.

## Exceptions to escalate
- Fiscal year not open for the instalment month → finance to open the period (`agency-period-close`).
- Foreign currency without exchange rate → finance.
- Job percentages not summing to 100, or job already in another contract → account director.
- New job requested on an invoiced fixed-distribution contract → refuse; propose a new contract.
- Commission found on a fee-linked estimate → `agency-production-estimating` to remove it.
- Overage hours above the agreed tolerance, unapproved hours or missing client rate → account lead and `agency-tasks-timesheets`.
- Agreement silent on overage policy → account director before billing.
- Deletion requested with an invoiced instalment → refuse.

## Return and handoff
Return `fee_contract_draft`, `instalment_schedule`, `job_allocation`, `hourly_settlement`, `approval_proposal`, `fee_exceptions`. Include tenant, titular and billing client, contract number, job ids and JobNumbers, instalment months, currency, revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Account director and billing. **Next:** `agency-client-billing`, `agency-accruals-revaluation`, `agency-profitability`.

## Connectors and files
- Provider ids: `xero` or `quickbooks` for fee revenue accounts and invoice references, `stripe` for recurring billing evidence (never enable automatic charging), `hubspot` or `notion` for the signed agreement. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating; timesheet exports arrive as host marketplace spreadsheets.
