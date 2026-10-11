---
name: agency-rebates
description: "Calculate supplier overcommissions, volume rebates, incentives and finder fees under documented contracts with the five scale engines, monthly provision vs bill flags, retroactivity and client rebate shares. Use for rebate pendings and settlement proposals. Do not approximate tiers with a flat rate, post provisions or issue rebate documents."
---

# Rebates

This stage sits after media orders and production estimates are executed and supplier invoices are registered (`agency-media-buying`, `agency-production-estimating`, `agency-payables`). It owns rebate contract interpretation, monthly pending generation (`Generar Pendientes de Overcomisión`), provision vs bill decisions and client rebate shares. Downstream, `agency-accruals-revaluation` provisions them, the billing and tax stages issue invoices to suppliers and credit notes to clients, and `agency-payables` registers supplier credit notes. It never posts provisions, issues invoices or credit notes, or marks pendings as billed without approval.

Read [control-contract.md](references/control-contract.md) first and apply it. Circuit map: [e2e-circuit.md](references/erp/e2e-circuit.md). Domain rules: [media-buying.md](references/erp/media-buying.md) (P-OC-01 to P-OC-05, BR-OC-00 to BR-OC-11, §4.6, §10.3–10.4, gaps 3–7); [production.md](references/erp/production.md) (P30, rules 50–60); [receivables.md](references/erp/receivables.md) (P-09 to P-13, rules 6–8, 31–32, §4.4); [supplier-invoicing.md](references/erp/supplier-invoicing.md) (P-22 to P-25, R-15 to R-19).

## Use when
- "Generate October overcommission pendings for supplier X", "overcomisiones", "rappel", "bonificación por volumen", "incentivos a proveedores".
- Computing a tiered rebate (value scale, slab, marginal, stepped) or a flat one, with cap, % reduction and contract sequencing (`Orden Generación Pendiente`).
- Deciding which months provision and which bill under the cut-off calendar (`Período de Corte`), including retroactive contracts.
- Computing the client share of a rebate (`Devolución al cliente`: total, partial %, fixed) or a volume credit passed to the client (`% Traslado`).
- Finder-fee (`finder fee`) base and amount; centralized group contracts across subsidiaries.

## Do not use when
- Billing the client for media or production → `agency-client-billing`.
- Registering the supplier's credit note or invoice as a document → `agency-payables`.
- Posting the monthly overcommission provision (PO/PD accounts) → `agency-accruals-revaluation`.
- Negotiating buy contracts and confidential discounts on rate cards → `agency-rate-cards-contracts`.
- Supplier invoice vs order differences → `agency-delivery-reconciliation`.
- Margin reporting including rebate income → `agency-profitability`.

## Required inputs
- **Blocking:** tenant, contract holder (supplier, which must exist as a billing client), contract id, type (origin media or production, income and client-rebate GL accounts), validity, base gross or net, currency and fixed-rate option, % reduction, calculation type, scale rows, cap, deduct-vendor-commission flag, generation order, cut-off calendar, billing type (agency invoice or supplier credit note), client rebate terms, scope (clients/products, publication types, media, production types).
- **Blocking:** qualifying orders or estimate lines within validity and scope with amounts in minor units and currency; registered supplier invoices for incentive scales and volume parts; earlier pendings, provisions and billed amounts by month and version.
- FX rates from the host for converting order currency to contract currency; supplier settlement amounts per client when the supplier sends them.
- Ask only for missing material inputs; never ask for credentials in chat.

## Procedure
1. Read the contract from the trusted master, not from a supplier email. Confirm the holder is linked to a billing client (production rule 60; receivables rule 32), the contract type maps income to observation code U4, 23 or 20 and client rebates to U7, 23 or 20 (P-OC-01), and validity is at most one year for production contracts (production rule 56).
2. Build the base per contract and month (BR-OC-00): qualifying order or estimate amounts within validity and scope (clients/products include/exclude, publication types, media, eligible production types), gross or net per contract, converted to contract currency at the fixed or generation-time rate, times (1 − % reduction), minus plan vendor commission when flagged, minus overcommission already computed by contracts with an earlier generation order. Exclusions of clients absent in a subsidiary are ignored there.
3. Select the engine: `flat` (fixed % without scales, BR-OC-01), `value_scale` (fixed amount per bracket, BR-OC-02), `slab` (absolute %, BR-OC-03), `marginal` (BR-OC-04), `stepped` (BR-OC-05). Use `tiered_commission` for all five; use `flat_rebate` only for a documented flat rate with a client share. Never approximate a tiered contract with a flat rate.
4. Evaluate cumulative scales on the cumulative-to-date base: month commission = C(cumulative to month) − C(cumulative to previous month), by passing `prior_adjusted_base_minor` (BR-OC-07; inferred, confirm locally). Apply the cap with `cap_minor` (BR-OC-06; whether per contract or per month is unstated, confirm locally).
5. When the supplier supplies its own settlement per client (`Importe Liquidación del Proveedor`), do not calculate; spread the supplier figure across that client's orders pro rata to base with `allocate` (receivables rule 8).
6. Distribute the month commission across orders pro rata to base with `allocate`. Pending per order = commission − billed (or − provisioned in provision months). With `Netea` on, net negatives against positives; otherwise propose a credit note for negatives.
7. Apply the cut-off calendar: provision months accrue only (PO account for income, PD for client rebate); bill months allow invoicing or a supplier credit note. The last contract month must be Bill (BR-OC-07). For centralized contracts, a provision month blocks billing in every subsidiary and each subsidiary bills only its own pending (P-OC-03).
8. Handle retroactivity (BR-OC-08): a contract signed mid-period regenerates pendings for past months. Never alter billed months; propose differences as new pending or credit. `Recalcular` bumps the version even after partial billing; `Eliminar` only when nothing is billed or provisioned.
9. Compute client rebates per client (BR-OC-09): Total = commission, Partial % = commission × r (base ambiguous between computed and billed commission; confirm locally), Partial fixed. With `Solo cobradas`, refund only overcommission already collected; with `Calcular Devolución Sobre Monto Over Cobrado`, base the refund on the collected amount (P-11d).
10. For supplier volume credit notes (P-22/P-23): expected credit = Σ order amount × Σ up to four percentages (R-15, additive); client share = credit × `% Traslado` (R-16); amount-origin credits spread pro rata (R-17). Overriding the received amount resets to one effective percentage.
11. For incentive scales (P-10, P-OC-04): base = registered supplier-invoice investment in the selected windows; mode `Sin Retroactivos`, `Solo Retroactivos` (top-up delta, inferred) or `Incluye Retroactivos`; slab reading is the likely default (confirm locally).
12. For supplier commissions billed to the supplier (P-09): base `Sobre Bruto`, `Sobre Neto` or `Solo 1° Descuento`; local currency only; media and production apart; volume part requires registered supplier invoices.
13. For finder fees (P-12, BR-OC-11): fee = % × client net investment or % × client profitability; output is an expense request per order to `agency-payables`, never an AR document.
14. Return the pending register by contract × month × generation order × version with state (`Pendiente`, `Provisionado`, `Facturado Parcial`, `Facturado`), compute `payload_digest`, and mark `pending_approval`. Mark-as-billed (`FACTURADO (M)`) needs a manual invoice reference.

## Rules and locks
- Holder must be a billing client of type Media or Production; contract types map only to the allowed observation codes.
- Contracts, contract types and pendings can be deleted or annulled only if nothing is invoiced (P-OC-02, BR-C-12).
- Orders already overcommission-billed are locked as selected; orders of an earlier-sequenced contract without pending are locked as unselected (P-11a).
- The last contract month must be Bill; provision months never bill (BR-OC-07).
- Centralized contracts are created and changed only in the consolidated database; subsidiaries view only; the consolidated entity neither bills nor provisions.
- Overcommission billing is irreversible; mark-as-billed can be undone only by a supervisor (P-11c).
- Supplier commission on foreign-currency plans or estimates is not allowed (receivables P-09).
- Scale boundaries below the first bracket yield zero; the reference examples start marginal brackets from 0 (gap 3, confirm locally).

## Calculations
- `tiered_commission`: the five engines with `reduction_bps`, `deductions_minor` (vendor commission and earlier contracts), brackets, `cap_minor`, `prior_adjusted_base_minor` for monthly increments and `client_share_mode` none, total, percent or fixed.
- `flat_rebate`: documented flat rate with client share and agency retained amount.
- `allocate`: commission across orders pro rata to base, supplier settlement across a client's orders, amount-origin volume credits across orders, with exact conservation.

```bash
python3 scripts/agency_tools.py tiered_commission < input.json
```
```json
{"currency": "USD", "method": "marginal", "base_minor": 800000, "reduction_bps": 0, "deductions_minor": 0, "flat_bps": 0, "brackets": [{"from_minor": 0, "bps": 500, "amount_minor": 0}, {"from_minor": 200000, "bps": 300, "amount_minor": 0}, {"from_minor": 500000, "bps": 200, "amount_minor": 0}, {"from_minor": 700000, "bps": 100, "amount_minor": 0}], "cap_minor": null, "prior_adjusted_base_minor": 550000, "client_share_mode": "percent", "client_share_bps": 2500, "client_share_fixed_minor": 0}
```
Not calculated by tools: FX conversion to contract currency, scope filtering, revenue recognition and provision accounting, incentive retroactive top-up policy and tax on rebate documents. Take them from the host rate source, contract master and controller policy.

## Approvals and segregation of duties
- Media director or producer confirms contract terms and scope; the controller approves pendings, provision vs bill and client rebates; billing issues documents through the billing and tax stages.
- Generating final pendings, recalculation of billed months, overcommission billing, client rebate NCs, mark/unmark as billed and contract annulment require an authenticated human approval bound to the `payload_digest`, contract, month, version, currency and total.

## Exceptions to escalate
- Contract terms ambiguous (marginal vs stepped, cap scope, partial % base) → controller with the contract owner.
- Holder not linked to a billing client or contract type mapped to a wrong account → data steward.
- Retroactive contract touching billed months → controller; differences only.
- Recalculation turns a month negative without `Netea` → controller; credit note proposal.
- Cap reached or near → media director.
- Supplier settlement differs from agency calculation beyond policy tolerance → media director.
- Rebate base includes foreign-currency estimates for supplier commission → billing lead; exclude.
- Client rebate owed but overcommission uncollected with `Solo cobradas` → hold; collections lead.
- Centralized contract edit attempted in a subsidiary → controller.

## Return and handoff
Return `eligible_base`, `rebate_calculation`, `pending_register`, `provision_proposal`, `client_rebates`, `rebate_exceptions`. Include tenant, contract and holder ids, month, generation order, version, client and order ids, currency, amounts in minor units, status (`draft`/`blocked`/`pending_approval`/`completed` only when verified), evidence references, blockers, approvals required and next stage.
**Owner:** Controller and media director. **Next:** agency-accruals-revaluation, agency-client-billing, agency-payables, agency-profitability.

## Connectors and files
- `xero` or `quickbooks` for posted supplier invoices and credit notes as base evidence; `supermetrics` or `google-ads`/`meta-ads` spend exports only as unverified volume evidence, never as the contractual base. Discover live tools first; registry entries are documentation, not tested access.
- File mode: [file-mode.md](references/file-mode.md); templates in `assets/`; `python3 scripts/normalize_files.py --kind broadcast-order ...` or `--kind invoice ...` for order and supplier-invoice extracts.
