---
name: agency-master-data
description: "Maintains agency ERP masters: clients, products, billing-client links, suppliers, media masters (type, outlet, programme, dayparts, duration factors, publication types), observation-coded GL links, cost centers and divisions. Use when creating, validating, mapping or deactivating masters. Do not delete used records or merge on name alone."
---

# Maintain Agency Master Data

Master data is the reference backbone under every document in the circuit: intake → **masters** → JobNumber → plans, estimates and orders → supplier invoices, client billing and automatic postings. This stage owns the canonical records for clients, products, billing-client links, suppliers, media masters, ledger-account links and analytic dimensions, plus their external codes. It never deletes a record that a transaction has used, never merges identities on a matching name, and never edits ledger accounts on a media type without Administration.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-masters-ooh.md](references/erp/media-masters-ooh.md) (§2.0 generic pattern; P01–P04, P06, P09, P12–P14, P16–P20, P25; §3.1–3.3; §5 rules 1–5, 9–17, 20–22, 34–41; §6; §10.2); [accounts-jobs.md](references/erp/accounts-jobs.md) (P-01 to P-05; §3.1–3.4; §5 rules 1–8; §6 observation code 22); [management-security.md](references/erp/management-security.md) (P-SY-09, P-SY-10, P-SY-12; §3 division and cost center; §4 provisional master change; §10.4).

## Use when
- Creating or validating masters: client, product, billing-client link, supplier, outlet (`Medio`), programme, daypart set (`Franja Horaria`), duration coefficients, publication type, material, target, zone.
- Linking ledger accounts to media types, publication types or production types by observation code ("cuentas contables por tipo de medio").
- Defining cost centers (`Centro de Costos`), divisions, sub-companies, or reassigning an account's management subcategory.
- Mapping external provider codes (ratings, monitoring, ad server, client codes) to masters.
- Bulk deactivation (`Modificación Masiva de Datos`) or duplicate resolution.

## Do not use when
- New client or brand intake and the provisional request itself → `agency-onboarding`.
- Opening or closing JobNumbers → `agency-job-lifecycle`.
- Rate cards and media buy contracts → `agency-rate-cards-contracts`; seller-side billboard faces → `agency-ooh-inventory`.
- Chart of accounts structure, voucher types, manual entries → `agency-general-ledger`.
- User profiles, roles and approval powers → `agency-access-governance`; connectors → `agency-integrations`.
- Multi-stage routing → `agency-orchestrator`.

## Required inputs
- **Blocking:** `tenant_id`; the master type and the record payload; current records with ids and usage status from the system of record.
- **Blocking for identity merges:** legal identity evidence (tax id, registry) held under restricted access outside model context.
- **Blocking for ledger links:** the chart of accounts with observation codes and whether bridge accounts are used.
- Configuration: provisional masters, product hierarchy, bridge-account mode, taxed/untaxed income split, different accounts for additional costs, divisions/sub-companies, currency exponents.
- Ask only for missing material inputs. Never ask for credentials in chat.

## Procedure
1. **Scope and read.** Load the current record, its active flag, validity dates and usage (any transaction). Usage decides delete vs deactivate for every master (§2.0, rule 5).
2. **Check identity and duplicates.** Match on stable ids and legal evidence, never on name alone. Keep aliases and provenance. Propose merges for steward review; never delete the original.
3. **Client side.** Owner client 3-character code; product 2-character code unique per client (accounts-jobs §5.1, §5.3); billing-client links from the CxC master; rate-card mode `Propio` or `Negociado` (§5.8). A product with hierarchy on needs macro group and group (§5.5).
4. **Supplier side.** Supplier with tax condition, payment term, withholding profile and media-enabled flag from trusted records. Basic suppliers (name, tax id, address) are allowed only when configured and are converted later (P30).
5. **Media classification.** Build top-down: generic media type with calculation basis (cm/column, seconds, elements; Internet uses elements) → media type (cut-off hour, ad-control flag, free programme entry, unit-of-measure use, manual-rate lock, base duration and pricing mode) → at least one publication type per media type (rule 3).
6. **Outlets and programming.** One outlet per zone × media type (rule 1); at least one supplier link and exactly one default supplier (rule 4); currency, VAT condition (100%, 50%, untaxed), tax jurisdiction and due-date rule (rules 34–41). Programmes carry outlet, type, weekdays, times, genre and rate basis. Sort broadcast grids by cut-off hour: times before the cut-off sort after 23:59 (rule 21).
7. **Validate dayparts and duration factors.** A daypart set covers 7 days × 24 h without overlap (rule 20). Duration coefficients hold factors for seconds 1–200, with factor 1 at the base duration; seconds without a factor fall back to proportional (rules 13–17). Supplier-criterion tables are off by default (configurable).
8. **Link ledger accounts.** Administration fills media-type accounts after Media creates the type (§6). Bridge mode: sales obs. 01, cost obs. 02, rebates and differences obs. 23, own-advertising cost obs. 36. Result mode: sales obs. 21 (fees 22), cost obs. 39. Fee contracts need media and production fee accounts with obs. 22 (accounts-jobs §6). Accounts must exist with the right observation code before the type is used for postings (§10.2).
9. **Analytic dimensions.** Cost centers, cost-center groups, divisions and sub-companies. Sub-company divisions cannot change once more than one fiscal year exists (P-SY-12). Account subcategory reassignment (Gross Income / Compensation / Other expenses) changes management P&L presentation; flag the impact (P-SY-09).
10. **External codes.** Map provider codes per entity and client (P12, P13). Record provider, entity, code and source file hash. Leave unmapped codes as gaps; never guess.
11. **Route the change.** Provisional masters on: submit as pending create, modify or delete (operator → manager → accounting registration). Bulk changes: list candidates, flag rows with a pending provisional change and skip them, and export planned vs executed actions (P-SY-10, R-AUD 68).
12. **Return** the change set with before/after values, validation results and approval routing.

## Rules and locks
- Never physically delete a master used in any transaction; set it inactive (universal rule; accounts-jobs §5.6).
- One outlet ↔ one media type and one zone; a plan has exactly one media type (rules 1–2).
- Exactly one default supplier per outlet, chosen among media-enabled suppliers (rule 4).
- With `pauta_libre` off, plans use registered programmes only (rule 9). With manual-rate lock on, only top-level (1A) users edit rates, discounts and surcharges (rule 10).
- Ad-control default cascades: outlet Yes/No overrides; "per media type" inherits (rule 11).
- VAT condition changes on an outlet reach existing plans only through the retroactive process from an effective date (rule 41).
- Ledger tabs on media and production types are edited only from the accounting side (configurable).
- Dynamic categories on an item lock once it is client-invoiced, its order is closed or rejected, or it is in a general plan close (rule 6).
- Material with no products is valid for all the client's products (rule 7).
- Balance-sheet accounts used as sales accounts are excluded from the gross-income provision (§6); flag any such link.

## Calculations
- `job_number`: after creating or recoding a client or product, check that the codes still compose a valid JobNumber (`client_code` 3 chars, `product_code` 2 chars) and report typology or billing restrictions. It does not open jobs.

```sh
echo '{"client_code":"ACM","product_code":"B1","year":2027,"job_type":"C","billing_code":"F","sequence":1}' \
  | python3 scripts/agency_tools.py job_number
# expect ACMB17CF0001 with media_allowed false (typology C)
```
- Daypart coverage, cut-off sorting and duration-factor fallback are validated by inspection against the rules above (no bundled tool).
- Not calculated here: VAT rates, withholding tables, FX rates, rate-card prices. These come from tax configuration, `agency-tax-compliance` and `agency-rate-cards-contracts`.

## Approvals and segregation of duties
- The data steward prepares; the media administrator owns media masters; Administration owns ledger links; the controller approves observation-code, subcategory and cost-center changes.
- Provisional masters: operator proposes, manager validates, accounting registers; the proposer never approves.
- Merges, bulk deactivations and ledger-link changes need an authenticated human approval bound to the exact change set and revision, verified by the host.

## Exceptions to escalate
- Possible duplicate client, supplier or outlet with conflicting legal evidence → data steward; no merge.
- Media type without accounts, or account lacking its observation code → Administration via `agency-general-ledger`.
- Outlet without a default supplier or with a non-media supplier → media administrator.
- Daypart gaps or overlaps; duplicate programme names on import (merge vs variant) → media administrator decides.
- VAT condition change requiring the retroactive run → media administrator and `agency-tax-compliance`.
- Bulk change touching rows with pending provisional changes → skip and report.
- Request to delete a used record → refuse; propose deactivation.
- Unmapped external codes blocking monitoring or reporting → `agency-integrations` or the owner stage.

## Return and handoff
Return `master_change_set`, `validation_report`, `duplicate_candidates`, `ledger_link_map`, `external_code_map`, `deactivation_plan`, `provisional_approval_requests`. Include tenant/client IDs, master ids and revision, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Data steward and controller. **Next:** `agency-job-lifecycle`, `agency-rate-cards-contracts`, `agency-media-planning`, `agency-general-ledger`.

## Connectors and files
- `hubspot` for client and contact records; `xero` or `quickbooks` for contacts, chart of accounts and tracking categories; host marketplace warehouse or documents for ERP master exports; `composio` or `zapier` reviewed read tools; `monid` or `supermetrics` only for discovering external platform account ids. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind KIND ...` for plan|broadcast-order|emission|ooh|invoice|rating. Master exports outside these kinds need a reviewed manifest and steward sign-off.
