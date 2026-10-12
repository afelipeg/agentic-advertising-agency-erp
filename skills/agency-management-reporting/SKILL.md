---
name: agency-management-reporting
description: "Prepares the monthly management pack and HQ reporting exports, checks account mapping coverage and computes KPIs (gross income, DSO, chargeability, WIP aging). Use after month close."
---

# Management Reporting

This stage sits after period close (agency-period-close) and reads the ledger, subledgers, timesheets and profitability results. It owns the monthly management pack, the parent-company reporting mapping (`Código de interfaz`) review and the per-tab export files for systems such as Hyperion/HFM, Magnitude or Cartesis. It never posts, never edits account mappings in the ERP without approval, and never submits files to headquarters itself.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [management-security.md](references/erp/management-security.md) (P-RP-01 to P-RP-03, rules R-RP 18–20, timesheet rules 29, 35 and 37, §6, §9 KPIs, §10.1 `reporting.validate_mapping` and `reporting.export_period`, gaps 1 and 11) and [accounting.md](references/erp/accounting.md) (§3.1 rubros with Hyperion code, §3.3 observation codes, BR-50 to BR-53 close and post-close controls, P09 WIP aging, 8A/8B reporting entries, §9 reports and KPIs).

Agency policy: apply `agency`, `currencies`, `accounting` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Monthly pack", "reporting a casa matriz", "HFM export", "Hyperion mapping", "cierre de reporting", "management accounts".
- Checking which accounts, cost centers or clients lack an interface code before export (unmapped means unreported).
- Producing the per-tab export files for a fiscal period, with cost-center and sub-company scope.
- Computing KPIs: gross income by client/job/division/month, DSO, chargeability vs target, WIP balance and aging, days to close, integration differences.
- Explaining month-over-month or budget-vs-actual movements in the pack.

## Do not use when
- The month is not closed or post-close controls are failing → agency-period-close.
- Job or client profitability detail and overhead allocation → agency-profitability.
- Cash projection → agency-cash-forecast; receivable follow-up → agency-collections.
- Creating or changing GL accounts, rubros or observation codes → agency-general-ledger; master records → agency-master-data.
- Revenue budget versions → agency-revenue-budget; timesheet approval → agency-tasks-timesheets.
- Changing reporting-system parameters or user access → agency-access-governance.

## Required inputs
- **Blocking:** tenant, fiscal period from/to, target system (HFM, Magnitude, Cartesis, or a "Global Client Profitability" variant), reporting currency and exponent, sub-company scope, cost centers or groups to exclude.
- **Blocking:** period state per subledger (closed, or pre-closed with explicit acceptance of a provisional pack); trial balance with integrator breakdown.
- **Blocking for export:** vendor-supplied interface code table and the account-to-code mapping; client codes for the client-profitability variant.
- Chart of accounts with subcategories (Gross Income, Compensation, Other expenses, Other income) and Hyperion codes; 8A/8B reporting entries and the policy on including them.
- KPI inputs: AR open items and period billing; approved hours with client vs total split and the chargeability target and tolerance; WIP account balance and items (obs 86 or WP); revenue budget version for comparison.
- Ask only for missing material inputs. Never ask for credentials or reporting-system logins in chat.

## Procedure
1. Check the period gate: all subledgers closed (accounting §4.2) and post-close controls passed (BR-52): no integration differences on AR 48, AP 30 and 82–85; unpaid listings equal control accounts; posted gross income equals the P&L Gross Income heading; bridge, cheque and deferred-cheque controls tie. If not, return `blocked` and route to agency-period-close.
2. Validate mapping coverage (P-RP-01, `reporting.validate_mapping`): list every account with movements or balance, entity and, for the client variant, client without an interface code. Unmapped items are not reported (R-RP 18). Report coverage as mapped amount ÷ total amount per currency and as counts.
3. Propose mappings for unmapped items with evidence (account name, subcategory, prior-period code). New interface accounts or codes are master changes: prepare them for the controller's approval; do not apply them.
4. Apply scope: exclude cost centers or cost-center groups and filter by sub-company as instructed (R-RP 20). State the 8A/8B policy: 8A-only adds USGAAP adjustments for headquarters, excluding both keeps local view.
5. Assemble the export data split into the tabs the target expects, one file per tab named after the tab (R-RP 19; P-RP-02). Record source trial-balance extraction time, period, currency and hash for each file.
6. Compute gross income by client, job, division and month from posted results and check the total against the P&L Gross Income heading.
7. Compute DSO. The reference does not compute it by name; use the agency formula (for example AR balance ÷ period billing × days in period) and state it (agency policy). Use `aging` for the AR profile by currency.
8. Compute chargeability from approved hours only: client hours ÷ total hours vs management target with tolerance; amber when deviating, red when excessive (timesheet rules 29, 35). Target and tolerance are not specified in the reference (gap 11) (confirm locally). Weighted hours cap at 8 per day (rule 37).
9. Compute WIP balance and aging from the WIP account items (supplier invoiced, client not billed) with `aging`; note the obs-86 vs WP ambiguity (accounting gap 4) (confirm locally).
10. Use `margin` for agency-level and client-level margin with managed spend separate, and `allocate` when the pack must distribute a shared amount (for example a regional fee or central cost) across divisions or clients with exact conservation.
11. Write variance commentary: month vs prior month, vs budget version, vs forecast. Forecast pages are stubs in the reference (gap 1); use the revenue budget projection instead and say so.
12. Compute the payload digest of the final pack and export files and return `pending_approval` for controller and CFO sign-off. Submission to headquarters is a human action.

## Rules and locks
- Unmapped accounts or entities are silently dropped from the export; a pack with uncovered amounts cannot be `completed` (R-RP 18).
- One export file per tab, named after the tab (R-RP 19).
- Exports produce no postings; corrections happen in the ledger by reversal in an open period, then re-export (accounting BR-07).
- Reopening a closed month changes reported figures; a re-export after reopen supersedes the earlier files and must be versioned (accounting §4.2).
- 8A entries post on the last day with an automatic 8B reversal; including or excluding them is a stated policy, never a silent choice (accounting §4.1).
- Only approved hours count for chargeability and valuation (management-security rule 29).
- Subcategory reassignment changes the management P&L presentation; it is a configuration change that needs approval (P-SY-09, §6).
- Aging scales must be well ordered; the tool requires ascending limits (the ERP report uses descending scales).
- Cost and profitability figures go only to users with visibility A/B; strip them for others before model access.

## Calculations
- `margin`: agency revenue and agency cost per client, division or total with `managed_spend_minor` separate; `margin_bps` null when revenue is zero.
- `aging`: AR (for DSO context) or WIP items by days past due with `as_of`, ascending `bucket_limits_days` and items per currency; returns buckets and weighted days overdue.
- `allocate`: distribute a shared amount across targets by integer weights with exact largest-remainder conservation.

```sh
python3 scripts/agency_tools.py aging < input.json
```
```json
{"as_of": "2026-10-31", "bucket_limits_days": [30, 60, 90], "items": [
 {"doc_id": "INV-1", "currency": "MXN", "due_date": "2026-10-15", "open_minor": 40000000},
 {"doc_id": "INV-2", "currency": "MXN", "due_date": "2026-08-20", "open_minor": 12000000},
 {"doc_id": "INV-3", "currency": "MXN", "due_date": "2026-11-20", "open_minor": 30000000}]}
```
- Not calculated by tools: interface code assignment, FX translation to reporting currency and reporting rates, DSO formula choice, consolidation eliminations (undocumented in the reference), chargeability targets.

## Approvals and segregation of duties
- The controller prepares the pack and mapping review; the CFO approves the pack and any headquarters submission.
- New or changed interface codes, subcategory reassignments and reporting-parameter changes need an authenticated human approval bound to the payload digest of the exact change; the preparer does not approve.
- Sending files or emails to headquarters is a send action and needs approval; never claim a submission receipt unless a trusted connector returns one.

## Exceptions to escalate
- Unmapped accounts, entities or clients with amounts → controller (mapping approval) before export.
- Posted gross income not equal to the P&L Gross Income heading → agency-general-ledger.
- Integration differences or failed post-close controls → agency-period-close.
- Month reopened after an export → controller; re-export as a new version.
- Hours pending approval or rejected for the period → agency-tasks-timesheets.
- WIP items ageing beyond policy → agency-accruals-revaluation and agency-client-billing.
- DSO deterioration or concentration in overdue buckets → agency-collections.
- Missing reporting rate or FX translation policy → CFO.

## Return and handoff
Return `management_pack`, `mapping_coverage`, `export_files`, `kpi_summary`, `variance_commentary`. Include tenant ID, period, sub-company and cost-center scope, target system, currency, source extraction times and hashes, mapping coverage, 8A/8B policy, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Controller and CFO. **Next:** agency-period-close, agency-revenue-budget, agency-orchestrator.

## Connectors and files
- Ledger and trial balance: `xero`, `quickbooks`. Media spend context: `supermetrics`, `google-analytics` (use read tools only). Host marketplace warehouse for extracts and host marketplace documents for the pack. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind invoice ...` for invoice extracts; other kinds plan|broadcast-order|emission|ooh|rating. Trial balances, mapping tables and hours extracts arrive as values-only CSV and stay unverified evidence.
