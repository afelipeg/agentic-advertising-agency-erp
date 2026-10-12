---
name: agency-access-governance
description: "Reviews roles, approval powers, cost visibility and segregation of duties; controls config changes and offboarding. Use when granting or auditing access. Never grants access itself."
---

# Govern Access and Configuration

Access governance is a foundation stage under the whole circuit: every stage, from JobNumber creation to payment-list finalization and period close, depends on who may see costs, who may create or approve, and which parameters switch gates on. This stage owns the access matrix, the SoD conflict report, configuration change requests, audit evidence packs and offboarding plans. It never grants itself or the agent a capability, never edits a parameter directly, and never deletes a user with history.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [management-security.md](references/erp/management-security.md) (P-SY-01, P-SY-06, P-SY-10, P-SY-11; P-US-01 to P-US-10; P-AU-01 to P-AU-08; §3 user, profile, role, specific activity; §4 user and profile lifecycles; §5 R-SEC 39–51, R-AP 52–58, R-AUD 67–69; §10.3; §11 items 3, 5, 18).

Agency policy: apply `roles`, `approvals`, `connectors` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Route approvers with `approval_route`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- New joiner, role change, leaver ("alta / baja de usuario", "cambio de perfil", "reasignar responsabilidades").
- Reviewing profiles (`Perfiles`), functional roles (`Roles Funcionales`) and specific activities (`Actividades Específicas`) such as approve for billing or finalize payment lists.
- Quarterly SoD or access review for auditors; producing access-by-user evidence.
- A parameter change (`Configuraciones Especiales`): media approval circuit, mandatory PO, timesheet approval, security policy.
- Mapping the agent's service user to screens, levels and visibility.

## Do not use when
- Attention-group design for a new client's products → `agency-onboarding` (this skill reviews the approval functions it assigns).
- Connector OAuth scopes and tool allowlists → `agency-integrations`.
- Master records, bulk master deactivation → `agency-master-data`.
- Reassigning a JobNumber responsible as part of job work → `agency-job-lifecycle`; task reassignment → `agency-tasks-timesheets`.
- Period reopen authority → `agency-period-close`; multi-stage routing → `agency-orchestrator`.

## Required inputs
- **Blocking:** `tenant_id`; users with department, type (pure, collaborator, client), status and dates; profiles with per-option S/N, access level and visibility; roles; specific activities; expense control/approve map with caps.
- **Blocking for parameter changes:** current value, proposed value, parameter group, requester and business reason.
- **Blocking for offboarding:** leaver, end date, successor, open tasks, open JobNumbers and pending approvals they own.
- The agency's SoD conflict matrix (the reference leaves it to the implementer); security policy parameters.
- Ask only for missing material inputs. Never ask for credentials or passwords in chat.

## Procedure
1. **Build the access matrix.** For each user: department, profile or role, per screen S/N, action level 1–6 (1 full plus special actions; 2 create/delete/modify/query; 3 create/modify/query; 4 create/query; 5 query with special actions; 6 query only), visibility A (unrestricted), B (profitability and costs), C (costs), D (no costs) (R-SEC 41). Adopt six levels; the reference is inconsistent (confirm locally).
2. **List approval powers as capabilities:** approve others' hours; control/approve expenses with cap; approve for billing; approve on behalf of client; approve non-billable estimates; approve production and expense POs; post supplier invoices after pre-close; finalize payment lists; close insertions and estimates; view supplier commissions; administer USGAAP entries; approve withholdings (CR/PA) (R-SEC 44). Add attention-group functions (approve for client, approve for billing, sector approval).
3. **Check structural rules:** every operator is a registered user and every user is a contact (R-SEC 39); unique email among active users (R-SEC 40); expense approvers hold level 1 or 2 on the expense screen (R-SEC 43); a user without department cannot create campaigns or incur costs (R-SEC 51); JobNumber creators are Accounts collaborators at level ≥3 with visibility C.
4. **Run the SoD review** against the agency matrix. Minimum pairs from the reference: creates and approves the same expense; enters and approves a supplier invoice; enters supplier invoices and finalizes payment lists; requester and approver of provisional masters; withholding calculator and approver; collaborator and approver of their own hours; Accounts close and definitive job close; client approval and approval for billing on the same document (§10.3 item 5). Use `payload_digest` to fingerprint the reviewed matrix.
5. **Check visibility controls.** Planners and buyers at D unless policy says otherwise; hiding costs is an anti-collusion control (R-SEC 42). The agent's service user inherits the requesting user's visibility; C/D fields never enter model context.
6. **Prepare grants and changes** as change requests, preferably on the shared role so all holders update (P-US-02, P-US-10). Show which users a role change propagates to.
7. **Control configuration changes** (P-SY-01): record current and proposed value, downstream impact (for example switching media circuit to Strict blocks orders lacking approvals; turning on mandatory PO approval blocks supplier invoices without approved PO), affected open documents, and rollback. Hash the change request with `payload_digest`.
8. **Plan offboarding** (P-US-04, P-US-05, P-US-08): reassign open tasks and open JobNumbers to a successor with sufficient permissions, release pending approvals the leaver owns, unlock the departed user record if items are stuck, then set the end date. Never delete a user with history.
9. **Assemble audit evidence** (P-AU-01, P-AU-07): movement trail filtered by user, entity and key; access-by-user report; options by role. Bulk changes and purges include planned vs executed export (R-AUD 68).
10. **Return** the matrix, conflicts, change requests and evidence with approval routing.

### Tool-to-access mapping for agent actions (§10.3 items 2–3)
| Agent action | Minimum action level | Visibility needed | Commit capability (human) |
|---|---|---|---|
| Read a listing or report | 5–6 | D strips costs; C costs without margin; B both; A all | none |
| Create a draft document | 4 | per document | none |
| Modify a draft | 3 | per document | none |
| Delete an unused draft | 2 | per document | none |
| Special action (post to control accounts, close insertions or estimates) | 1 | per document | named specific activity |
| Approve by client, for billing, POs, expenses, hours, payment lists | screen level 1–2 where required | per document | named specific activity or group function |

## Rules and locks
- Deny by default: a missing S/N grant means no access, whatever the level.
- An agent prepares; a human holding the capability commits, unless the deployment explicitly delegates in writing (§10.3 item 4).
- Self-approval of expenses is blocked when the no-self-approval flag is on; treat it as on unless the controller documents otherwise (configurable).
- Profiles assigned to any user cannot be deleted; users with activity cannot be deleted, only end-dated (P-US-09, R-SEC 48).
- Role edits propagate to all holders; review the blast radius before approving.
- Parameter changes need confirmation, a before/after record and impact notes; tools read parameters at runtime and never hard-code circuits (§10.3 items 6, 8).
- Every write emits an audit row: date, time, user, action, entity type, entity id, notes, agent run id (§10.3 item 7).
- Security policy: password length and history, max age, inactivity lockout, failed-attempt limit, idle logout. The legacy 8-character limit is not a target; exceed it (§11 item 18).
- Mandatory timesheet and FX-rate login gates block a user's other work; an agent acting for that user surfaces the blocker first (§10.3 item 9).

## Calculations
- `payload_digest`: fingerprint each access change request, configuration change request and reviewed SoD matrix so the approval binds to that exact content. The digest does not authorize anything.

```sh
echo '{"payload":{"tenant_id":"t-01","change":"grant","user":"u-118","capability":"finalize_payment_lists","revision":3}}' \
  | python3 scripts/agency_tools.py payload_digest
# returns sha256 and authorizes_execution false
```
- SoD conflicts are evaluated by rule against the agency matrix; no bundled tool decides them.
- Not calculated here: expense caps, credit limits, or any amounts. They come from the configured approval map.

## Approvals and segregation of duties
- The system administrator prepares user, profile and role changes; the controller approves capabilities that touch money, postings, approvals or cost visibility; a department head confirms business need.
- Parameter changes: requester ≠ approver; the controller approves, and high-impact circuit changes add the CFO (agency policy).
- Every grant, role edit, parameter change, purge and offboarding step needs an authenticated human approval bound to the `payload_digest`, revision and expiry, verified by the host. The agent never approves a change it prepared.

## Exceptions to escalate
- SoD conflict found → controller; propose role split or compensating review.
- Departed user still owns approvals, tasks or jobs → successor plus controller; run offboarding.
- Agent service user holds a commit capability without written delegation → remove; system administrator.
- Planner or buyer with visibility A/B without documented reason → controller.
- Profile change requested for one user that differs from their role → prefer role update; system administrator.
- Parameter change with open documents affected (for example pending orders under a stricter circuit) → controller with impact list.
- Request to delete a user with history or an assigned profile → refuse; end-date instead.
- Audit trail gap or missing agent run id on writes → host engineering.

## Return and handoff
Return `access_matrix`, `capability_register`, `sod_conflicts`, `access_change_requests`, `config_change_requests`, `offboarding_plan`, `audit_evidence_pack`. Include tenant IDs, user, profile and role ids, revision, payload digests, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Controller and system administrator. **Next:** `agency-integrations`, `agency-orchestrator`, or the stage that requested the access.

## Connectors and files
- Identity and audit exports from the ERP via host marketplace warehouse or documents; `xero` or `quickbooks` user and role listings where the ledger is the system of record; `notion` or `hubspot` for access request tickets; `composio` or `zapier` reviewed read tools. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating. Access reviews normally use a redacted access-by-user export reviewed by a human.
