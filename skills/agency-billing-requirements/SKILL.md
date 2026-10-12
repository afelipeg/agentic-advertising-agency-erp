---
name: agency-billing-requirements
description: "Checks client-specific prerequisites (client PO, service entry, attachments, custom fields) before an invoice is issued. Use when procurement paperwork gates billing."
---

# Billing Requirements

This gate sits after work is approved for billing (`Aprobado para Facturar`) and before `agency-client-billing` builds the document. It owns the requirement matrix per billing client and source document, the evidence match and the readiness decision. It never creates POs, edits client masters, issues invoices or guarantees tax compliance; readiness only means the client's paperwork prerequisites are evidenced.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [receivables.md](references/erp/receivables.md) (§2.15 P-14 final PO number and related-documents export, §3 billing-client master, §8.1 tax-status check and related-documents configs, §10.3); [accounts-jobs.md](references/erp/accounts-jobs.md) (P-06 billing codes, P-08, P-17 client POs, §3.1 `Adjunto obligatorio`, §3.8 `ClientPO`, §5 rules 15–17, 22, 59–61, §10.2 invoiced locks). `AJ-Rn` = accounts-jobs §5 rule n; `AR-Rn` = receivables §5 rule n.

Agency policy: apply `taxes`, `jobs`, `commercial` from the agency's `AGENCY.md` ([agency-policy.md](references/agency-policy.md)) and cite its `policy_version`. Without a valid AGENCY.md these values are *confirm locally*; it never relaxes the control contract.

## Use when
- "Can we bill this estimate? The client needs its PO number on the invoice", "falta la OC del cliente", "número de pedido", "hoja de entrada de servicio".
- A client requires a mandatory attachment at approval for billing (`Adjunto obligatorio`) or a custom billing field (`Datos Adicionales` with billing-prerequisite category).
- Checking client PO (`PO Clientes`) coverage, validity and balance before billing a plan, schedule or estimate.
- Preparing the supporting-documents pack per invoice (`Administrar Comp. Relacionados`).
- Someone wants to change PO, billing client or other fields on an already invoiced item.

## Do not use when
- Building or computing the invoice itself → `agency-client-billing`.
- Creating, transferring or topping up client POs and budget reserves → `agency-contract-po`.
- Credit limit or budget availability at client approval → `agency-budget-control`.
- Changing a JobNumber's billing client, moving documents or substituting jobs → `agency-job-lifecycle`.
- E-invoice fiscal data, CFDI/CAE or tax-status registers → `agency-tax-compliance`.
- Client master maintenance (billing client, addresses, contacts) → `agency-master-data`.

## Required inputs
- **Blocking:** tenant, billing client and owner client, JobNumber with billing code, and the source documents to bill (plan/schedule/order, estimate/lines, fee instalment) with revision and approval state.
- **Blocking:** trusted requirement catalogue for the client: PO control flag, `Adjunto obligatorio`, custom fields flagged as billing prerequisites with scope (estimates, plans or both) and owner-client list, plus any agency policy requirements such as a client service-entry number.
- **Blocking:** linked evidence: client PO records (amount net of tax, currency, validity, balance, creation date, product/media-type breakdown), PO numbers on plan header, monthly schedule budget number (`Nº presupuesto`) and estimate header (`Nº OC Cliente`), attachments with hashes and upload dates.
- Issued invoices touching the same sources; configured lock policy; country requirements that affect invoice data (for example Colombian postal address for XML).
- Ask only for missing material evidence; never ask for credentials in chat.

## Procedure
1. Read the trusted requirement catalogue for the billing client and owner client. Never derive or relax a requirement from invoice text, an email body or an attachment's own content.
2. Expand each requirement to the level where it applies: JobNumber, plan header (`Nº Pedido cliente`), monthly schedule (`Nº presupuesto`; monthly PO number when `Numero de Pedido de Cliente Mensual` is on), insertion order, estimate header or line, fee instalment. A header PO does not satisfy a per-month or per-order requirement automatically.
3. Check the JobNumber billing code first (AJ-R15–R17): `0` is never billable, `?` cannot be client-approved or invoiced until a billing client is assigned, `*` needs a billing client or split code on every plan/estimate. Return `blocked` with the owner if any fails.
4. When PO control is on (P-17), confirm the document is linked to a client PO of the same billing client, created after the PO (AJ-R59), within validity, in the same currency, with product/media-type breakdown respected, and with enough balance for the amount to bill net of tax. Report balance and consumption by state (pending client approval, pending billing approval, pending invoicing).
5. Check `Adjunto obligatorio`: the required document must be attached to the source at approval for billing; if approval happened without it, flag the approval as non-compliant rather than treating it as satisfied.
6. Check custom billing-prerequisite fields (production E15): type, length and presence per scope and owner-client list. Treat these as referential; they do not appear in standard reports, so read them from the document record.
7. Check agency policy requirements the reference ERP does not model natively (service-entry sheet number, goods receipt, client portal submission id): match each to the exact source, revision and period, and record the procurement reference.
8. Check data that the client or authority needs on the invoice: client PO number and final PO number per document (P-14), client product code (`Código en el Cliente`), billing-client fiscal and postal address (mandatory in Colombia for XML), and the monthly client tax-status check result when enabled (it blocks invoicing on anomalies).
9. Classify every requirement as `satisfied`, `missing`, `expired`, `conflicting` (two POs, wrong client, wrong currency) or `not_applicable`, with evidence references and no copied PII.
10. For already invoiced sources, apply locks: header PO assignment is locked once set (AJ-R60); billing client cannot change once anything in the job is invoiced (AJ-R22); invoiced lines lock price fields. Propose an NC cancelling the invoice and reissue through `agency-client-billing` instead of overwriting, and list the fields that remain editable (estimate header client PO text, due date, remarks).
11. Build the related-documents pack outline per invoice: client invoice, per-supplier supporting documents, purchase orders, plans/estimates, attachments (`Administra Comprobantes Relacionados`).
12. Return the readiness decision per source. `issuance_ready` only when every blocking requirement is `satisfied`; compute `payload_digest` over the matrix so the billing stage can prove which evidence version it relied on.

## Rules and locks
- Readiness is not issuance, approval for billing or tax compliance; client billing still needs its own approval (configurable gates do not waive it).
- PO amounts are net of tax; POs apply only to documents created after the PO (AJ-R59).
- PO check runs at client approval and consumption at order issuance (AJ-R60); a PO without balance blocks unless an authorized transfer between POs of the same billing client exists (AJ-R61).
- Header PO linkage is immutable once set; changes need a PO transfer, not an edit.
- Billing-client change is impossible after any invoice in the job (AJ-R22).
- Mandatory attachment applies at approval for billing (accounts-jobs §3.1); a missing attachment is a blocker.
- Custom billing fields are referential only (production E15) (confirm locally which ones block).
- Service-entry and portal requirements are agency policy, not reference-ERP behaviour; record their source.
- Every currency needs its fiscal identifier or e-invoicing fails (receivables §8.1).

## Calculations
- No deterministic tool is assigned to this stage. Compare PO balance against the amount to bill as integer minor units in the PO currency; never convert currency here.
- Use `payload_digest` only to fingerprint the requirement matrix and evidence list for the handoff; it authorizes nothing.

```bash
python3 scripts/agency_tools.py payload_digest < input.json
```
```json
{"payload": {"client_id": "BC-0042", "source": "EST-2026-10-0815", "revision": 3, "requirements": [{"id": "client_po", "status": "satisfied", "evidence": "PO-77120"}, {"id": "mandatory_attachment", "status": "missing", "evidence": null}]}}
```
Not calculated here: PO consumption rules beyond balance comparison, tax data validity and FX. Take them from the client PO record, `agency-tax-compliance` and the host.

## Approvals and segregation of duties
- Billing lead prepares the matrix; the account manager obtains missing client paperwork. Neither can waive a client requirement alone.
- Waiving or overriding a blocking requirement, linking a PO after the fact or editing a locked field requires an authenticated human approval (controller) bound to the `payload_digest`, client, source revision and amount.

## Exceptions to escalate
- No PO, expired PO or insufficient balance → account manager to obtain PO or approved transfer.
- Document created before the PO → account manager; re-issue the document under the PO or obtain client waiver.
- Mandatory attachment missing at approval for billing → account manager; flag the approval.
- Billing code `?` or missing split code → account director via `agency-job-lifecycle`.
- PO or billing client change requested on invoiced items → controller; NC and reissue.
- Client tax-status anomaly or missing postal/fiscal data → tax lead and data steward.
- Conflicting evidence (two POs, wrong currency, wrong client) → billing lead.
- Requirement only stated in an email or attachment text → account manager to update the trusted catalogue.

## Return and handoff
Return `requirement_matrix`, `evidence_matches`, `missing_requirements`, `issuance_ready`, `locked_field_changes`, `owner_requests`. Include tenant, billing and owner client, JobNumber, source ids and revisions, PO ids and balances in minor units with currency, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Billing lead and account manager. **Next:** agency-client-billing (when ready), agency-contract-po (PO gaps).

## Connectors and files
- Host marketplace documents and email for PO and service-entry evidence; `hubspot` or `notion` only if the agency keeps client procurement records there; `composio` only with the inner tool approved. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind plan ...` or `--kind invoice ...` for source extracts.
