# ERP functional reference

Functional reverse engineering of a reference agency ERP, built from its publicly accessible help documentation (about 1,330 pages, reviewed 2026-10-11). The content is paraphrased and restructured in English to give agents the business rules of a complete agency back office: processes, entities, document lifecycles, numbered rules, accounting impacts, cross-module handoffs, country behaviour and known gaps.

Start with [e2e-circuit.md](e2e-circuit.md). Each skill mirrors the circuit map plus only the domain documents it needs under `references/erp/`.

| Document | Reference ERP module | Main skills |
|---|---|---|
| [accounts-jobs.md](accounts-jobs.md) | Cuentas, Presupuesto de Ingresos, Workflow | job-lifecycle, onboarding, contract-po, budget-control, fee-contracts, tasks-timesheets, revenue-budget, profitability |
| [production.md](production.md) | Producción | production-estimating, production, rebates, accruals-revaluation |
| [media-planning.md](media-planning.md) | Medios: planificación, import/export de planes | media-ranking, media-planning, tv-radio-planning, digital-planning, plan-changes, campaign-activation, campaign-optimization |
| [media-buying.md](media-buying.md) | Medios: compra, contratos, tarifarios, control de avisos, overcomisiones | rate-cards-contracts, media-buying, transmission-control, rebates |
| [media-masters-ooh.md](media-masters-ooh.md) | Medios: maestros; Carteles Vía Pública | master-data, ooh-planning, ooh-inventory |
| [expenses.md](expenses.md) | Gastos | expenses, fixed-assets, fee-contracts |
| [receivables.md](receivables.md) | Cuentas por Cobrar | client-billing, billing-requirements, collections, tax-compliance |
| [supplier-invoicing.md](supplier-invoicing.md) | Cuentas por Pagar: facturación proveedores | payables, delivery-reconciliation, tax-compliance |
| [payables-treasury.md](payables-treasury.md) | Cuentas por Pagar: recepción, pagos; Tesorería | payment-run, cash-settlement, cash-forecast |
| [accounting.md](accounting.md) | Contabilidad | general-ledger, accruals-revaluation, fixed-assets, period-close, tax-compliance |
| [management-security.md](management-security.md) | Management, Sistemas, General | access-governance, cash-forecast, management-reporting, tasks-timesheets |

## How to use and extend

- Treat each rule as the reference behaviour of a mature Latin American agency ERP, not as law or as your agency's policy. Configure differences in your host and record them in the skill's returned assumptions.
- Bracketed ids such as `[mp301010]` name the help page used as evidence so maintainers can re-check a rule.
- Corrections: open an issue with the rule id, the evidence and the agency/country context. Do not paste proprietary manuals, client data or credentials.
- Not legal, tax or accounting advice.
