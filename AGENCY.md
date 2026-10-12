# AGENCY.md — agency policy overlay

This file holds **your agency's parameters**: who approves what and up to which amount, currencies, tax rates, chart of accounts, job typologies, commercial defaults and the connectors you enabled. Every skill reads it before acting. Change a value once and every skill, in every agent (Claude Code, Codex, Gemini CLI or a Claude, ChatGPT or Gemini app), applies it.

> **Example values.** Everything below is a synthetic example for a Mexico-based agency. Replace it with your own and have finance and tax review it before use.

## How it works

- **Only the `json agency-policy` block is policy.** Text outside it is commentary for people; agents give it no authority.
- **Parameters, not permissions.** This file decides *which* human role approves, never *whether* a human approves. Money, commitments, postings, sends and deletions always need an authenticated human approval under the control contract. An approval role must be a person's job role, and segregation of duties stays on.
- **Every role in a tier approves.** A tier with two roles needs two different people, neither of them the maker. A higher tier keeps the approvers of the tier below and can only add more.
- **No secrets.** Credentials live in your host's secret store. The validator rejects keys, tokens, passwords and long account or card numbers.
- **Amounts** are integer minor units of the rule's currency (MXN 500,000.00 is `50000000`). Rates are basis points (16% is `1600`).
- **Missing is not zero.** If a section or action is missing, skills mark it *confirm locally* and ask.

Where agents look, in order: a file the user attaches or names, `AGENCY.md` at the project root, then `~/.agency-erp/AGENCY.md`. Validate after every edit:

```sh
agency-erp policy check            # or: python3 tools/agency_policy.py AGENCY.md
```

## Policy

```json agency-policy
{
  "policy_version": "2026-10-12.1",
  "agency": {
    "name": "Example Agency S.A. de C.V.",
    "base_currency": "MXN",
    "countries": ["MX"],
    "timezone": "America/Mexico_City",
    "fiscal_year_start_month": 1
  },
  "currencies": [
    {"code": "MXN", "exponent": 2},
    {"code": "USD", "exponent": 2}
  ],
  "roles": ["account_director", "media_director", "production_director", "finance_manager", "controller", "tax_manager", "cfo", "ceo", "it_admin"],
  "segregation_of_duties": true,
  "approvals": [
    {"action": "client_estimate", "currency": "MXN", "tiers": [
      {"up_to_minor": 50000000, "roles": ["account_director"]},
      {"up_to_minor": null, "roles": ["account_director", "cfo"]}]},
    {"action": "media_order", "currency": "MXN", "tiers": [
      {"up_to_minor": 100000000, "roles": ["media_director"]},
      {"up_to_minor": null, "roles": ["media_director", "cfo"]}]},
    {"action": "production_order", "currency": "MXN", "tiers": [
      {"up_to_minor": 30000000, "roles": ["production_director"]},
      {"up_to_minor": null, "roles": ["production_director", "cfo"]}]},
    {"action": "plan_change", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["media_director"]}]},
    {"action": "campaign_launch", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["media_director"]}]},
    {"action": "supplier_invoice", "currency": "MXN", "tiers": [
      {"up_to_minor": 50000000, "roles": ["finance_manager"]},
      {"up_to_minor": null, "roles": ["finance_manager", "controller"]}]},
    {"action": "client_invoice", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["finance_manager"]}]},
    {"action": "credit_note", "currency": "MXN", "tiers": [
      {"up_to_minor": 5000000, "roles": ["finance_manager"]},
      {"up_to_minor": null, "roles": ["finance_manager", "cfo"]}]},
    {"action": "payment_run", "currency": "MXN", "tiers": [
      {"up_to_minor": 200000000, "roles": ["finance_manager", "controller"]},
      {"up_to_minor": null, "roles": ["finance_manager", "controller", "cfo"]}]},
    {"action": "payment_run", "currency": "USD", "tiers": [
      {"up_to_minor": 10000000, "roles": ["finance_manager", "controller"]},
      {"up_to_minor": null, "roles": ["finance_manager", "controller", "cfo"]}]},
    {"action": "cash_settlement", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["finance_manager"]}]},
    {"action": "journal_entry", "currency": "MXN", "tiers": [
      {"up_to_minor": 10000000, "roles": ["controller"]},
      {"up_to_minor": null, "roles": ["controller", "cfo"]}]},
    {"action": "budget_change", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["account_director", "cfo"]}]},
    {"action": "credit_override", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["cfo"]}]},
    {"action": "write_off", "currency": "MXN", "tiers": [
      {"up_to_minor": 1000000, "roles": ["controller"]},
      {"up_to_minor": null, "roles": ["controller", "cfo"]}]},
    {"action": "period_reopen", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["controller", "cfo"]}]},
    {"action": "master_data_change", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["controller"]}]},
    {"action": "access_change", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["it_admin", "controller"]}]},
    {"action": "message_send", "currency": "MXN", "tiers": [
      {"up_to_minor": null, "roles": ["account_director"]}]}
  ],
  "taxes": {
    "reviewed_by_role": "tax_manager",
    "reviewed_on": "2026-10-12",
    "rates": [
      {"code": "IVA16", "country": "MX", "kind": "vat", "rate_bps": 1600, "applies_to": "Example: general VAT rate on services; confirm with your tax advisor"}
    ]
  },
  "fx": {"source": "Example: central bank daily reference rate", "revaluation": "monthly"},
  "jobs": {
    "typologies": [
      {"code": "A", "label": "Advertising campaign", "sales_allowed": true},
      {"code": "P", "label": "Production only", "sales_allowed": true},
      {"code": "I", "label": "Internal or new business", "sales_allowed": false}
    ]
  },
  "commercial": {
    "default_payment_terms_days": 30,
    "default_agency_fee_bps": 1000,
    "overcommission_engine": "marginal",
    "plan_change_tolerance_bps": 200
  },
  "collections": {"dunning_days": [7, 15, 30, 60], "credit_limit_review": "quarterly"},
  "accounting": {
    "close_day": 5,
    "accounts": [
      {"purpose": "media_payable", "code": "2105-01"},
      {"purpose": "production_payable", "code": "2105-02"},
      {"purpose": "client_receivable", "code": "1105-01"},
      {"purpose": "agency_commission_revenue", "code": "4101-01"},
      {"purpose": "fee_revenue", "code": "4102-01"},
      {"purpose": "unbilled_revenue_accrual", "code": "1180-01"},
      {"purpose": "uninvoiced_cost_accrual", "code": "2180-01"},
      {"purpose": "fx_gain", "code": "7101-01"},
      {"purpose": "fx_loss", "code": "7201-01"}
    ]
  },
  "connectors": {"profile": "agency", "enabled": ["google-ads", "meta-ads", "supermetrics", "quickbooks", "banxico-sie"]}
}
```

## Notes for your team

- Bump `policy_version` on every change. Skills pass it to `approval_route` and put it in every approval request, so a change invalidates pending approvals granted under the previous version.
- Keep this file in a private fork or a private repository. Review changes by pull request; CI runs the validator.
