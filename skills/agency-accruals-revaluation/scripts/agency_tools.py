#!/usr/bin/env python3
"""Read-only agency ERP calculations. Python standard library; no network, clock or ledger writes."""
import hashlib
import json
import sys

MAX_AMOUNT = 9_007_199_254_740_991

def integer(minimum=0, maximum=MAX_AMOUNT):
    return {"type": "integer", "minimum": minimum, "maximum": maximum}

def obj(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}

CURRENCY = {"type": "string", "pattern": "^[A-Z]{3}$"}
SIGNED = integer(-MAX_AMOUNT)
ID = {"type":"string", "pattern":"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$"}
DATE = {"type":"string", "pattern":"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
LINE = obj({"line_id":ID,"account_id":ID,"supplier_id":ID,"channel":ID,"currency":CURRENCY,"amount_minor":integer(),"committed_minor":integer(),"start_date":DATE,"end_date":DATE})
LINES = {"type":"array","items":LINE,"maxItems":1000}
SCHEMAS = {
    "plan_diff": obj({"before":LINES,"after":LINES}),
    "budget_check": obj({"currency": CURRENCY, "authorized_minor": integer(), "spent_minor": integer(), "open_commitments_minor": integer(), "reservations_minor": integer(), "requested_minor": integer()}),
    "reconcile": obj({"currency": CURRENCY, "ordered_minor": integer(), "delivered_minor": integer(), "invoiced_minor": integer(), "tolerance_minor": integer()}),
    "flat_rebate": obj({"currency": CURRENCY, "eligible_minor": integer(), "rate_bps": integer(0, 10000), "client_share_bps": integer(0, 10000)}),
    "margin": obj({"currency": CURRENCY, "agency_revenue_minor": integer(), "agency_cost_minor": integer(), "managed_spend_minor": integer()}),
    "payload_digest": obj({"payload": {"type": "object"}}),
}
OUTPUT_SCHEMAS = {
    "plan_diff": obj({"added":{"type":"array","items":ID},"removed":{"type":"array","items":ID},"changed":{"type":"array","items":ID},"unchanged":{"type":"array","items":ID},"currency_deltas":{"type":"array","items":obj({"currency":CURRENCY,"before_minor":integer(),"after_minor":integer(),"delta_minor":SIGNED})},"blockers":{"type":"array","items":obj({"line_id":ID,"reason":{"type":"string","enum":["commitment_removed","below_commitment","commitment_rewritten","committed_dimensions_changed"]}})},"status":{"type":"string","enum":["draft","blocked"]},"requires_host_approval":{"type":"boolean"}}),
    "budget_check": obj({"currency": CURRENCY, "available_minor": SIGNED, "after_request_minor": SIGNED, "within_budget": {"type":"boolean"}, "atomic_reservation_required":{"type":"boolean"}}),
    "reconcile": obj({"currency": CURRENCY, "discrepancy_minor": SIGNED, "payable_candidate_minor": integer(), "status":{"type":"string","enum":["hold","matched"]}, "reasons":{"type":"array","items":{"type":"string","enum":["invoice_delivery_mismatch","delivery_exceeds_order","short_delivery","invoice_exceeds_order"]}}}),
    "flat_rebate": obj({"currency": CURRENCY, "rebate_minor": integer(), "client_return_minor": integer(), "agency_retained_minor": integer()}),
    "margin": obj({"currency": CURRENCY, "margin_minor": SIGNED, "margin_bps":{"anyOf":[SIGNED,{"type":"null"}]}, "managed_spend_minor": integer()}),
    "payload_digest": obj({"sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"}, "canonicalization":{"type":"string","enum":["python-json-sorted-v1"]}, "authorizes_execution":{"type":"boolean"}}),
}

def validate(value, schema, path="$ "):
    """Strict validator for the small schema vocabulary used here, not general JSON Schema."""
    import re
    if "anyOf" in schema:
        for alternative in schema["anyOf"]:
            try:
                validate(value, alternative, path)
                return
            except ValueError:
                pass
        raise ValueError(f"{path}: no matching type")
    kind = schema["type"]
    checks = {"object": lambda: type(value) is dict, "integer": lambda: type(value) is int, "string": lambda: type(value) is str, "boolean": lambda: type(value) is bool, "array": lambda: type(value) is list, "null": lambda: value is None}
    if kind not in checks or not checks[kind]():
        raise ValueError(f"{path}: expected {kind}")
    if kind == "object" and "properties" in schema:
        required = set(schema["required"])
        if set(value) != required:
            missing = sorted(required-set(value))
            unknown = sorted(set(value)-required)
            raise ValueError(f"{path}: missing fields {missing}; unexpected field count {len(unknown)}")
        for key, spec in schema["properties"].items():
            validate(value[key], spec, path + "." + key)
    if kind == "integer" and not schema["minimum"] <= value <= schema["maximum"]:
        raise ValueError(f"{path}: outside allowed integer range")
    if kind == "string" and "pattern" in schema and not re.fullmatch(schema["pattern"], value):
        raise ValueError(f"{path}: invalid string")
    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path}: unsupported value")
    if kind == "array":
        if len(value) > schema.get("maxItems", 10000):
            raise ValueError(f"{path}: too many items")
        for i, item in enumerate(value):
            validate(item, schema["items"], f"{path}[{i}]")

def round_half_up(numerator, denominator):
    return (numerator + denominator // 2) // denominator

def run(name, arguments):
    if name not in SCHEMAS:
        raise ValueError("Unknown tool")
    validate(arguments, SCHEMAS[name])
    a = arguments
    if name in ERP_TOOLS:
        try:
            result = ERP_TOOLS[name](a)
        except (OverflowError, ArithmeticError):
            raise ValueError("date or amount outside the supported range") from None
        validate(result, OUTPUT_SCHEMAS[name])
        return result
    if name == "plan_diff":
        from datetime import date
        for label in ("before", "after"):
            seen = set()
            for line in a[label]:
                if line["line_id"] in seen:
                    raise ValueError(f"{label}: duplicate line_id")
                seen.add(line["line_id"])
                if date.fromisoformat(line["end_date"]) < date.fromisoformat(line["start_date"]):
                    raise ValueError("end_date precedes start_date")
                if label == "before" and line["amount_minor"] < line["committed_minor"]:
                    raise ValueError("before amount is below authoritative commitment")
        before, after = ({x["line_id"]: x for x in a[k]} for k in ("before", "after"))
        added, removed = sorted(after.keys()-before.keys()), sorted(before.keys()-after.keys())
        changed = sorted(k for k in before.keys() & after.keys() if before[k] != after[k])
        unchanged = sorted(k for k in before.keys() & after.keys() if before[k] == after[k])
        blockers = []
        for k in removed:
            if before[k]["committed_minor"]:
                blockers.append({"line_id":k,"reason":"commitment_removed"})
        for k in after:
            old, new = before.get(k), after[k]
            if new["amount_minor"] < new["committed_minor"]:
                blockers.append({"line_id":k,"reason":"below_commitment"})
            if (not old and new["committed_minor"] != 0) or (old and new["committed_minor"] != old["committed_minor"]):
                blockers.append({"line_id":k,"reason":"commitment_rewritten"})
            if old and old["committed_minor"] and any(old[f] != new[f] for f in ("account_id","supplier_id","channel","currency","start_date","end_date")):
                blockers.append({"line_id":k,"reason":"committed_dimensions_changed"})
        currencies = sorted({x["currency"] for x in a["before"]+a["after"]})
        deltas = []
        for currency in currencies:
            totals = [sum(x["amount_minor"] for x in a[k] if x["currency"] == currency) for k in ("before","after")]
            deltas.append({"currency":currency,"before_minor":totals[0],"after_minor":totals[1],"delta_minor":totals[1]-totals[0]})
        result = {"added":added,"removed":removed,"changed":changed,"unchanged":unchanged,"currency_deltas":deltas,"blockers":blockers,"status":"blocked" if blockers else "draft","requires_host_approval":bool(added or removed or changed)}
        validate(result, OUTPUT_SCHEMAS[name])
        return result
    if name == "payload_digest":
        # Finite JSON only. The digest binds content; it does NOT authenticate an approver.
        data = json.dumps(a["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        result = {"sha256": hashlib.sha256(data.encode()).hexdigest(), "canonicalization": "python-json-sorted-v1", "authorizes_execution": False}
        validate(result, OUTPUT_SCHEMAS[name])
        return result
    result = {"currency": a["currency"]}
    if name == "budget_check":
        remaining = a["authorized_minor"] - a["spent_minor"] - a["open_commitments_minor"] - a["reservations_minor"]
        result.update(available_minor=remaining, after_request_minor=remaining-a["requested_minor"], within_budget=a["requested_minor"] <= remaining, atomic_reservation_required=True)
    elif name == "reconcile":
        discrepancy = a["invoiced_minor"] - a["delivered_minor"]
        reasons = []
        if abs(discrepancy) > a["tolerance_minor"]:
            reasons.append("invoice_delivery_mismatch")
        if a["delivered_minor"] > a["ordered_minor"] + a["tolerance_minor"]:
            reasons.append("delivery_exceeds_order")
        if a["ordered_minor"] - a["delivered_minor"] > a["tolerance_minor"]:
            reasons.append("short_delivery")
        if a["invoiced_minor"] > a["ordered_minor"] + a["tolerance_minor"]:
            reasons.append("invoice_exceeds_order")
        result.update(discrepancy_minor=discrepancy, payable_candidate_minor=min(a["ordered_minor"], a["delivered_minor"], a["invoiced_minor"]), status="hold" if reasons else "matched", reasons=reasons)
    elif name == "flat_rebate":
        rebate = round_half_up(a["eligible_minor"] * a["rate_bps"], 10000)
        client = round_half_up(rebate * a["client_share_bps"], 10000)
        result.update(rebate_minor=rebate, client_return_minor=client, agency_retained_minor=rebate-client)
    elif name == "margin":
        margin = a["agency_revenue_minor"] - a["agency_cost_minor"]
        result.update(margin_minor=margin, margin_bps=None if a["agency_revenue_minor"] == 0 else margin*10000//a["agency_revenue_minor"], managed_spend_minor=a["managed_spend_minor"])
    validate(result, OUTPUT_SCHEMAS[name])
    return result

# ---------------------------------------------------------------------------
# ERP circuit calculators (v0.2). Derived from the functional reverse-engineering
# reference in docs/erp-reference/. Every function is pure arithmetic over
# validated inputs: no network, no clock, no ledger or provider writes.
# Defaults reproduce the reference ERP's documented behaviour; hosts must still
# confirm agency policy (rounding, tax tables, tier semantics) before relying on them.
# ---------------------------------------------------------------------------
from datetime import date as _date, timedelta as _timedelta

BPS = integer(0, 10000)
SIGNED_BPS = integer(-10000, 10000)
MONTH = {"type": "string", "pattern": "^[0-9]{4}-(0[1-9]|1[0-2])$"}
HHMM = {"type": "string", "pattern": "^([01][0-9]|2[0-3]):[0-5][0-9]$"}
def arr(items, max_items=1000):
    return {"type": "array", "items": items, "maxItems": max_items}
def enum(*values):
    return {"type": "string", "enum": list(values)}
def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}
CODE3 = {"type": "string", "pattern": "^[A-Z0-9]{3}$"}
CODE2 = {"type": "string", "pattern": "^[A-Z0-9]{2}$"}
LETTER = {"type": "string", "pattern": "^[A-Z]$"}
HOLIDAYS = arr(DATE, 400)

def rdiv(numerator, denominator):
    """Round half away from zero for signed integer division."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    return sign * ((abs(numerator) + denominator // 2) // denominator)

def _d(text):
    try:
        return _date.fromisoformat(text)
    except ValueError:
        raise ValueError("invalid calendar date") from None

def _business_roll(day, holidays, weekend_roll=True):
    blocked = {_d(h) for h in holidays}
    rolled = 0
    while (weekend_roll and day.weekday() >= 5) or day in blocked:
        day += _timedelta(days=1)
        rolled += 1
        if rolled > 31:
            raise ValueError("holiday calendar blocks more than 31 consecutive days")
    return day, rolled

def _month_end(day):
    nxt = (day.replace(day=28) + _timedelta(days=4))
    return nxt - _timedelta(days=nxt.day)

def _add_months(month_text, offset):
    year, month = map(int, month_text.split("-"))
    index = year * 12 + (month - 1) + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"

ERP_SCHEMAS = {
    "job_number": obj({"client_code": CODE3, "product_code": CODE2, "year": integer(2000, 2099), "job_type": LETTER,
                       "billing_code": enum("F", "0", "?", "*"), "sequence": integer(1, 9999)}),
    "media_line_cost": obj({"currency": CURRENCY, "calc_type": enum("per_second", "per_unit", "per_thousand", "per_action", "package"),
                            "rate_minor": integer(), "measure": integer(0, 1_000_000), "spots": integer(0, 1_000_000),
                            "volume": integer(0, MAX_AMOUNT), "package_minor": integer()}),
    "discount_cascade": obj({"currency": CURRENCY, "gross_minor": integer(), "mode": enum("compound", "additive"),
                             "discounts_bps": arr(BPS, 8),
                             "surcharges": arr(obj({"kind": enum("percent", "amount"), "value": integer(), "accumulative": {"type": "boolean"}}), 8),
                             "fee_base": enum("none", "net", "gross", "gross_after_first_discount"), "fee_bps": BPS, "fee_discount_bps": BPS}),
    "audience_metrics": obj({"currency": CURRENCY, "net_cost_minor": integer(), "universe": integer(1, 10_000_000_000),
                             "spots": arr(obj({"spot_id": ID, "rating_hundredths": integer(0, 10000)}), 5000),
                             "reach_hundredths": nullable(integer(1, 10000))}),
    "tiered_commission": obj({"currency": CURRENCY, "method": enum("flat", "value_scale", "slab", "marginal", "stepped"),
                              "base_minor": integer(), "reduction_bps": BPS, "deductions_minor": integer(), "flat_bps": BPS,
                              "brackets": arr(obj({"from_minor": integer(), "bps": BPS, "amount_minor": integer()}), 20),
                              "cap_minor": nullable(integer()), "prior_adjusted_base_minor": nullable(integer()),
                              "client_share_mode": enum("none", "total", "percent", "fixed"), "client_share_bps": BPS, "client_share_fixed_minor": integer()}),
    "estimate_totals": obj({"agency_service_bps": BPS, "agency_service_discount_bps": BPS,
                            "lines": arr(obj({"line_id": ID, "kind": enum("indirect", "direct", "internal", "cost_rendering"), "currency": CURRENCY,
                                              "unit_price_minor": integer(), "unit_cost_minor": integer(), "quantity": integer(0, 1_000_000), "days": integer(1, 3660),
                                              "discount_bps": BPS, "service_eligible": {"type": "boolean"},
                                              "supplier_commission_mode": enum("none", "fixed", "percent"), "supplier_commission_value": integer()}), 500)}),
    "hourly_fee_settlement": obj({"currency": CURRENCY, "instalment_minor": integer(), "covered_hours_hundredths": integer(1, 100_000_000),
                                  "hours": arr(obj({"person_id": ID, "approved_hours_hundredths": integer(0, 100_000_000), "client_rate_minor": integer()}), 500),
                                  "overage_policy": enum("bill_at_client_rate", "absorb")}),
    "payment_terms": obj({"base_date": DATE, "term_days": integer(0, 3650), "rule": enum("net_days", "end_of_month_then_days", "next_fortnight"),
                          "delay_days": integer(0, 365), "holidays": HOLIDAYS, "weekend_roll": {"type": "boolean"}}),
    "withholding": obj({"currency": CURRENCY, "method": enum("per_payment", "cumulative_period"), "payment_base_minor": integer(),
                        "accumulated_base_minor": integer(), "accumulated_withheld_minor": integer(), "non_taxable_minimum_minor": integer(),
                        "rate_bps": BPS, "minimum_withholding_minor": integer()}),
    "fx_revaluation": obj({"local_currency": CURRENCY, "local_exponent": integer(0, 6),
                           "closing_rates": arr(obj({"currency": CURRENCY, "rate_micro": integer(1, MAX_AMOUNT)}), 100),
                           "items": arr(obj({"doc_id": ID, "side": enum("asset", "liability"), "currency": CURRENCY, "exponent": integer(0, 6),
                                             "open_minor": integer(), "book_rate_micro": integer(1, MAX_AMOUNT)}), 5000)}),
    "aging": obj({"as_of": DATE, "bucket_limits_days": arr(integer(1, 3650), 10),
                  "items": arr(obj({"doc_id": ID, "currency": CURRENCY, "due_date": DATE, "open_minor": SIGNED}), 20000)}),
    "allocate": obj({"currency": CURRENCY, "amount_minor": SIGNED, "weights": arr(obj({"target_id": ID, "weight": integer(0, 1_000_000_000)}), 1000)}),
    "installment_schedule": obj({"currency": CURRENCY, "gross_minor": integer(), "advance_bps": BPS, "installments": integer(1, 120), "start_month": MONTH}),
    "depreciation_schedule": obj({"currency": CURRENCY, "cost_minor": integer(), "residual_minor": integer(), "life_months": integer(1, 600),
                                  "acquisition_date": DATE, "first_month_rule": enum("acquisition_month", "following_month")}),
    "journal_check": obj({"entry_id": ID, "posting_date": DATE, "locked_periods": arr(MONTH, 240),
                          "lines": arr(obj({"line_id": ID, "account_id": ID, "currency": CURRENCY, "debit_minor": integer(), "credit_minor": integer(),
                                            "required_dimensions_present": {"type": "boolean"}}), 500)}),
    "cash_projection": obj({"as_of": DATE, "granularity": enum("week", "month"), "periods": integer(1, 26), "holidays": HOLIDAYS,
                            "opening_balances": arr(obj({"currency": CURRENCY, "amount_minor": SIGNED}), 50),
                            "items": arr(obj({"item_id": ID, "currency": CURRENCY, "direction": enum("in", "out"), "amount_minor": integer(),
                                              "base_date": DATE, "term_days": integer(0, 3650), "delay_days": integer(0, 365),
                                              "status": enum("confirmed", "expected"), "probability_bps": BPS}), 20000)}),
    "spot_match": obj({"tolerance_minutes": integer(0, 120), "match_material": {"type": "boolean"},
                       "ordered": arr(obj({"spot_id": ID, "station_id": ID, "air_date": DATE, "window_start": HHMM, "window_end": HHMM, "material_id": ID}), 5000),
                       "aired": arr(obj({"event_id": ID, "station_id": ID, "air_date": DATE, "air_time": HHMM, "material_id": ID}), 20000)}),
    "credit_exposure": obj({"currency": CURRENCY, "credit_limit_minor": integer(), "ar_open_minor": integer(), "approved_unbilled_minor": integer(), "requested_minor": integer()}),
    "invoice_check": obj({"currency": CURRENCY, "lines": arr(obj({"line_id": ID, "net_minor": integer(), "vat_bps": BPS}), 500),
                          "perceptions_minor": integer(), "other_charges_minor": integer(), "withholdings_netted_minor": integer(),
                          "declared_total_minor": integer(), "rounding_tolerance_minor": integer(0, 10000)}),
}

# Approval routing from the agency policy overlay (AGENCY.md). Routing names who approves;
# it never removes the human approval required by the control contract.
APPROVAL_ACTIONS = ("client_estimate", "media_order", "production_order", "plan_change", "campaign_launch", "supplier_invoice",
                    "client_invoice", "credit_note", "payment_run", "cash_settlement", "journal_entry", "budget_change",
                    "credit_override", "write_off", "period_reopen", "master_data_change", "access_change", "message_send")
ROLE = {"type": "string", "pattern": "^[a-z][a-z0-9_]{1,47}$"}
NON_HUMAN_ROLES = frozenset({"ai", "agent", "assistant", "bot", "system", "auto", "automatic", "automation", "llm", "model",
                             "none", "nobody", "anyone", "any", "all", "self", "maker", "skip"})
# Best-effort guard: a role containing any of these tokens names software, not an accountable person.
NON_HUMAN_TOKENS = frozenset({"ai", "bot", "bots", "agent", "agents", "agentic", "auto", "automatic", "automated", "automation",
                              "llm", "gpt", "chatgpt", "claude", "gemini", "codex", "copilot", "model", "system", "svc",
                              "engine", "script", "robot", "rpa", "api", "mcp", "webhook", "cron", "nobody", "anyone", "skip"})
VERSION_ID = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$"}

def non_human(role):
    return role in NON_HUMAN_ROLES or bool(NON_HUMAN_TOKENS & set(role.split("_")))
APPROVAL_RULE = obj({"action": enum(*APPROVAL_ACTIONS), "currency": CURRENCY,
                     "tiers": arr(obj({"up_to_minor": nullable(integer()), "roles": arr(ROLE, 10)}), 10)})
ERP_SCHEMAS["approval_route"] = obj({"policy_version": VERSION_ID, "action": enum(*APPROVAL_ACTIONS), "currency": CURRENCY,
                                     "amount_minor": integer(), "rules": arr(APPROVAL_RULE, 200)})

CURRENCY_TOTAL = obj({"currency": CURRENCY, "sale_minor": integer(), "cost_minor": integer(), "service_minor": integer(),
                      "supplier_commission_minor": integer(), "gross_income_minor": SIGNED})
ERP_OUTPUT_SCHEMAS = {
    "job_number": obj({"code": {"type": "string", "pattern": "^[A-Z0-9]{5}[0-9][A-Z][F0?*][0-9]{4}$"}, "sales_allowed": {"type": "boolean"},
                       "media_allowed": {"type": "boolean"}, "client_approval_allowed": {"type": "boolean"},
                       "warnings": arr(enum("typology_forbids_sales", "billing_client_pending", "split_billing_needs_percentages", "non_billable_job"), 10)}),
    "media_line_cost": obj({"currency": CURRENCY, "gross_minor": integer(), "formula": {"type": "string"}}),
    "discount_cascade": obj({"currency": CURRENCY, "surcharged_gross_minor": integer(),
                             "steps": arr(obj({"discount_bps": BPS, "amount_minor": integer(), "running_minor": integer()}), 8),
                             "net_minor": integer(), "fee_minor": integer(), "client_total_minor": integer(), "rounding": enum("half_up_each_step")}),
    "audience_metrics": obj({"currency": CURRENCY, "trp_hundredths": integer(), "impressions": integer(), "average_rating_hundredths": nullable(integer()),
                             "cpr_minor": nullable(integer()), "cpm_minor": nullable(integer()), "frequency_hundredths": nullable(integer())}),
    "tiered_commission": obj({"currency": CURRENCY, "adjusted_base_minor": integer(), "commission_minor": integer(), "cap_applied": {"type": "boolean"},
                              "prior_commission_minor": integer(), "period_commission_minor": SIGNED, "client_rebate_minor": SIGNED,
                              "agency_retained_minor": SIGNED, "bracket_index": nullable(integer(0, 19))}),
    "estimate_totals": obj({"lines": arr(obj({"line_id": ID, "currency": CURRENCY, "sale_minor": integer(), "cost_minor": integer(), "service_minor": integer(),
                                              "supplier_commission_minor": integer(), "margin_minor": SIGNED}), 500),
                            "currency_totals": arr(CURRENCY_TOTAL, 50), "invoice_groups": integer(0, 50),
                            "blockers": arr(obj({"line_id": ID, "reason": enum("direct_sale_differs_from_cost", "commission_on_internal_line", "duplicate_line_id")}), 500)}),
    "hourly_fee_settlement": obj({"currency": CURRENCY, "implied_rate_minor": integer(), "total_hours_hundredths": integer(), "overage_hours_hundredths": integer(),
                                  "unused_hours_hundredths": integer(), "overage_minor": integer(), "total_billable_minor": integer(),
                                  "per_person": arr(obj({"person_id": ID, "overage_hours_hundredths": integer(), "overage_minor": integer()}), 500)}),
    "payment_terms": obj({"due_date": DATE, "expected_date": DATE, "due_rolled_days": integer(0, 31), "expected_rolled_days": integer(0, 31)}),
    "withholding": obj({"currency": CURRENCY, "taxable_base_minor": integer(), "withholding_minor": integer(), "below_minimum": {"type": "boolean"}}),
    "fx_revaluation": obj({"local_currency": CURRENCY,
                           "items": arr(obj({"doc_id": ID, "book_local_minor": SIGNED, "closing_local_minor": SIGNED, "gain_loss_minor": SIGNED}), 5000),
                           "gain_minor": integer(), "loss_minor": integer(), "net_minor": SIGNED}),
    "aging": obj({"as_of": DATE, "currencies": arr(obj({"currency": CURRENCY, "not_due_minor": SIGNED, "total_minor": SIGNED,
                                                       "buckets": arr(obj({"from_days": integer(1, 3651), "to_days": nullable(integer(1, 3650)), "amount_minor": SIGNED}), 11),
                                                       "weighted_days_overdue": nullable(integer())}), 100)}),
    "allocate": obj({"currency": CURRENCY, "allocations": arr(obj({"target_id": ID, "amount_minor": SIGNED}), 1000), "total_minor": SIGNED}),
    "installment_schedule": obj({"currency": CURRENCY, "advance_minor": integer(), "installments": arr(obj({"number": integer(1, 120), "month": MONTH, "amount_minor": integer()}), 120), "total_minor": integer()}),
    "depreciation_schedule": obj({"currency": CURRENCY, "depreciable_minor": integer(), "first_month": MONTH, "last_month": MONTH,
                                  "months": arr(obj({"month": MONTH, "charge_minor": integer(), "accumulated_minor": integer(), "net_book_minor": integer()}), 600)}),
    "journal_check": obj({"entry_id": ID, "status": enum("valid", "invalid"),
                          "currencies": arr(obj({"currency": CURRENCY, "debit_minor": integer(), "credit_minor": integer(), "difference_minor": SIGNED}), 50),
                          "errors": arr(obj({"line_id": nullable(ID), "reason": enum("both_sides", "zero_line", "missing_dimension", "unbalanced_currency", "locked_period", "duplicate_line_id", "no_lines")}), 2600)}),
    "cash_projection": obj({"as_of": DATE, "granularity": enum("week", "month"),
                            "currencies": arr(obj({"currency": CURRENCY, "opening_minor": SIGNED, "overdue_in_minor": integer(), "overdue_out_minor": integer(),
                                                   "beyond_horizon_in_minor": integer(), "beyond_horizon_out_minor": integer(),
                                                   "periods": arr(obj({"period_start": DATE, "in_confirmed_minor": integer(), "in_expected_minor": integer(),
                                                                       "out_confirmed_minor": integer(), "out_expected_minor": integer(), "closing_minor": SIGNED}), 26),
                                                   "minimum_closing_minor": SIGNED, "minimum_period_start": DATE}), 50)}),
    "spot_match": obj({"matches": arr(obj({"spot_id": ID, "event_id": ID, "kind": enum("exact", "tolerance")}), 5000),
                       "ambiguous": arr(obj({"spot_id": ID, "candidate_event_ids": arr(ID, 20000)}), 5000),
                       "ordered_not_aired": arr(ID, 5000), "aired_not_ordered": arr(ID, 20000)}),
    "credit_exposure": obj({"currency": CURRENCY, "exposure_after_minor": integer(), "headroom_minor": SIGNED, "within_limit": {"type": "boolean"}, "requires_override_approval": {"type": "boolean"}}),
    "invoice_check": obj({"currency": CURRENCY, "net_minor": integer(), "vat_minor": integer(), "computed_total_minor": SIGNED,
                          "difference_minor": SIGNED, "status": enum("matched", "rounding_adjustment", "mismatch"),
                          "vat_by_rate": arr(obj({"vat_bps": BPS, "net_minor": integer(), "vat_minor": integer()}), 50)}),
}

ERP_OUTPUT_SCHEMAS["approval_route"] = obj({"policy_version": VERSION_ID, "action": enum(*APPROVAL_ACTIONS), "currency": CURRENCY, "amount_minor": integer(),
                                            "status": enum("routed", "no_rule_confirm_locally"), "tier_index": nullable(integer(0, 9)),
                                            "approver_roles": arr(ROLE, 10), "quorum": enum("all_distinct", "confirm_locally"),
                                            "human_approval_required": {"type": "boolean"},
                                            "authorizes_execution": {"type": "boolean"}})

ERP_DESCRIPTIONS = {
    "job_number": "Compose and check a 12-character job code (client+product+year digit+typology+billing code+sequence); reports typology/billing restrictions, does not open jobs.",
    "media_line_cost": "Price one media line by calculation type (per second, per unit, per thousand, per action, package); no rate-card lookup.",
    "discount_cascade": "Apply surcharges, up to eight cascaded or additive discounts and an agency fee to a gross media amount.",
    "audience_metrics": "Sum rating points and derive impressions, cost per rating point, CPM and frequency from supplied licensed ratings.",
    "tiered_commission": "Overcommission/rebate engines (flat, value scale, slab, marginal, stepped) with reduction, cap, monthly increment and client share.",
    "estimate_totals": "Production estimate line and currency totals: sale, cost, agency service, supplier commission, invoice groups and direct-line checks.",
    "hourly_fee_settlement": "Monthly hourly-fee settlement: implied rate, hours over the covered quota and overage at client rates.",
    "payment_terms": "Due date and expected payment date from base date, terms rule, delay and business-day calendar.",
    "withholding": "Generic withholding calculation (per payment or cumulative in period) from host-supplied rates and minimums; no tax tables bundled.",
    "fx_revaluation": "Revalue open foreign-currency items at closing rates and split gains and losses; does not post entries.",
    "aging": "Bucket open receivables or payables by days past due per currency with weighted days overdue.",
    "allocate": "Allocate an amount across targets by integer weights with exact conservation (largest remainder).",
    "installment_schedule": "Split a contract amount into an advance plus monthly installments that sum exactly to the gross.",
    "depreciation_schedule": "Straight-line monthly depreciation schedule with exact totals; no inflation adjustment.",
    "journal_check": "Validate a proposed journal entry: balance per currency, one-sided lines, dimensions and locked periods; does not post.",
    "cash_projection": "Project cash by week or month from dated inflows/outflows with terms, delays, probabilities and opening balances.",
    "spot_match": "Match ordered broadcast spots to monitored airings with a time tolerance; returns exact, tolerance, ambiguous and unmatched sets.",
    "credit_exposure": "Check a client credit limit against open receivables, approved unbilled work and a new request.",
    "approval_route": "Route an action and amount to the approver roles of the matching AGENCY.md tier; every listed role approves, each a different person who is not the maker. Never authorizes execution.",
    "invoice_check": "Recompute invoice VAT by rate and total against the declared amount with an explicit rounding tolerance.",
}

def _job_number(a):
    code = f"{a['client_code']}{a['product_code']}{a['year'] % 10}{a['job_type']}{a['billing_code']}{a['sequence']:04d}"
    warnings = []
    sales_allowed = a["job_type"] not in ("N", "S", "W") and a["billing_code"] != "0"
    if a["job_type"] in ("N", "S", "W") and a["billing_code"] in ("F", "*", "?"):
        warnings.append("typology_forbids_sales")
    if a["billing_code"] == "0":
        warnings.append("non_billable_job")
    if a["billing_code"] == "?":
        warnings.append("billing_client_pending")
    if a["billing_code"] == "*":
        warnings.append("split_billing_needs_percentages")
    return {"code": code, "sales_allowed": sales_allowed, "media_allowed": a["job_type"] != "C",
            "client_approval_allowed": a["billing_code"] != "?", "warnings": warnings}

def _media_line_cost(a):
    t = a["calc_type"]
    if t == "package":
        return {"currency": a["currency"], "gross_minor": a["package_minor"], "formula": "package_amount"}
    if a["package_minor"]:
        raise ValueError("package_minor must be 0 unless calc_type is package")
    if t == "per_second":
        gross, formula = a["rate_minor"] * a["measure"] * a["spots"], "rate_per_second * duration_seconds * spots"
    elif t == "per_unit":
        gross, formula = a["rate_minor"] * a["measure"] * a["spots"], "rate_per_unit * measure_units * spots"
    elif t == "per_thousand":
        gross, formula = rdiv(a["rate_minor"] * a["volume"], 1000), "rate * volume / 1000"
    else:
        gross, formula = a["rate_minor"] * a["volume"], "rate * actions"
    if gross > MAX_AMOUNT:
        raise ValueError("amount overflow")
    return {"currency": a["currency"], "gross_minor": gross, "formula": formula}

def _discount_cascade(a):
    gross = a["gross_minor"]
    running = gross
    for s in a["surcharges"]:
        if s["kind"] == "amount":
            running += s["value"]
        else:
            if s["value"] > 10000:
                raise ValueError("percent surcharge above 10000 bps")
            running += rdiv((running if s["accumulative"] else gross) * s["value"], 10000)
    surcharged = running
    if surcharged > MAX_AMOUNT:
        raise ValueError("amount overflow")
    steps = []
    first_after = None
    if a["mode"] == "additive":
        total_bps = sum(a["discounts_bps"])
        if total_bps > 10000:
            raise ValueError("additive discounts exceed 100%")
        target = rdiv(surcharged * total_bps, 10000)
        taken = 0
        for i, d in enumerate(a["discounts_bps"]):
            amount = target - taken if i == len(a["discounts_bps"]) - 1 else rdiv(surcharged * d, 10000)
            amount = max(min(amount, surcharged - taken), 0)
            taken += amount
            running = surcharged - taken
            steps.append({"discount_bps": d, "amount_minor": amount, "running_minor": running})
            if first_after is None:
                first_after = running
    else:
        for d in a["discounts_bps"]:
            amount = rdiv(running * d, 10000)
            running -= amount
            steps.append({"discount_bps": d, "amount_minor": amount, "running_minor": running})
            if first_after is None:
                first_after = running
    net = max(running, 0)
    base = {"none": 0, "net": net, "gross": surcharged, "gross_after_first_discount": surcharged if first_after is None else first_after}[a["fee_base"]]
    fee = 0 if a["fee_base"] == "none" else rdiv(rdiv(base * a["fee_bps"], 10000) * (10000 - a["fee_discount_bps"]), 10000)
    return {"currency": a["currency"], "surcharged_gross_minor": surcharged, "steps": steps, "net_minor": net,
            "fee_minor": fee, "client_total_minor": net + fee, "rounding": "half_up_each_step"}

def _audience_metrics(a):
    seen = set()
    trp = 0
    impressions = 0
    for s in a["spots"]:
        if s["spot_id"] in seen:
            raise ValueError("duplicate spot_id")
        seen.add(s["spot_id"])
        trp += s["rating_hundredths"]
        impressions += rdiv(a["universe"] * s["rating_hundredths"], 10000)
    n = len(a["spots"])
    return {"currency": a["currency"], "trp_hundredths": trp, "impressions": impressions,
            "average_rating_hundredths": rdiv(trp, n) if n else None,
            "cpr_minor": rdiv(a["net_cost_minor"] * 100, trp) if trp else None,
            "cpm_minor": rdiv(a["net_cost_minor"] * 1000, impressions) if impressions else None,
            "frequency_hundredths": rdiv(trp * 100, a["reach_hundredths"]) if (a["reach_hundredths"] and trp) else None}

def _tier_value(method, base, flat_bps, brackets):
    """Return (commission_minor, bracket_index). Brackets ascend by from_minor."""
    if method == "flat":
        return rdiv(base * flat_bps, 10000), None
    idx = None
    for i, b in enumerate(brackets):
        if base >= b["from_minor"]:
            idx = i
    if method == "value_scale":
        return (0 if idx is None else brackets[idx]["amount_minor"]), idx
    if method == "slab":
        return (0 if idx is None else rdiv(base * brackets[idx]["bps"], 10000)), idx
    if method == "marginal":
        # Reference behaviour: once the first threshold is reached, the first bracket is
        # measured from zero; later brackets apply only to the base inside each band.
        if idx is None:
            return 0, None
        total = 0
        for i, b in enumerate(brackets):
            lower = 0 if i == 0 else b["from_minor"]
            upper = brackets[i + 1]["from_minor"] if i + 1 < len(brackets) else None
            top = base if upper is None else min(base, upper)
            if top > lower:
                total += (top - lower) * b["bps"]
        return rdiv(total, 10000), idx
    # stepped: base * first rate once the first threshold is reached, plus each later
    # threshold's rate increment applied to the base above that threshold.
    if idx is None:
        return 0, None
    total = base * brackets[0]["bps"]
    for i in range(1, len(brackets)):
        if base > brackets[i]["from_minor"]:
            total += (base - brackets[i]["from_minor"]) * (brackets[i]["bps"] - brackets[i - 1]["bps"])
    return rdiv(total, 10000), idx

def _tiered_commission(a):
    method, brackets = a["method"], a["brackets"]
    if method == "flat" and brackets:
        raise ValueError("flat method takes no brackets")
    if method != "flat":
        if not brackets:
            raise ValueError("tier methods require brackets")
        froms = [b["from_minor"] for b in brackets]
        if froms != sorted(froms) or len(set(froms)) != len(froms):
            raise ValueError("brackets must strictly ascend by from_minor")
    def adjusted(base):
        return max(rdiv(base * (10000 - a["reduction_bps"]), 10000) - a["deductions_minor"], 0)
    def capped(value):
        if a["cap_minor"] is not None and value > a["cap_minor"]:
            return a["cap_minor"], True
        return value, False
    current = adjusted(a["base_minor"])
    commission, idx = _tier_value(method, current, a["flat_bps"], brackets)
    commission, cap_applied = capped(commission)
    prior = 0
    if a["prior_adjusted_base_minor"] is not None:
        prior, _ = _tier_value(method, a["prior_adjusted_base_minor"], a["flat_bps"], brackets)
        prior, _ = capped(prior)
    period = commission - prior
    mode = a["client_share_mode"]
    # Client rebates are computed on positive period commission only; a negative period
    # (base fell or was corrected) is an agency-side reversal, and any client clawback is policy.
    if mode == "none" or period <= 0:
        rebate = 0
    elif mode == "total":
        rebate = period
    elif mode == "percent":
        rebate = rdiv(period * a["client_share_bps"], 10000)
    else:
        rebate = min(a["client_share_fixed_minor"], period)
    return {"currency": a["currency"], "adjusted_base_minor": current, "commission_minor": commission, "cap_applied": cap_applied,
            "prior_commission_minor": prior, "period_commission_minor": period, "client_rebate_minor": rebate,
            "agency_retained_minor": period - rebate, "bracket_index": idx}

def _estimate_totals(a):
    lines, totals, blockers, seen = [], {}, [], set()
    for line in a["lines"]:
        if line["line_id"] in seen:
            blockers.append({"line_id": line["line_id"], "reason": "duplicate_line_id"})
            continue
        seen.add(line["line_id"])
        units = line["quantity"] * line["days"]
        sale = rdiv(line["unit_price_minor"] * units * (10000 - line["discount_bps"]), 10000)
        cost = line["unit_cost_minor"] * units
        if line["kind"] == "direct" and sale != cost:
            blockers.append({"line_id": line["line_id"], "reason": "direct_sale_differs_from_cost"})
        service = 0
        if line["service_eligible"]:
            service = rdiv(rdiv(sale * a["agency_service_bps"], 10000) * (10000 - a["agency_service_discount_bps"]), 10000)
        mode, value = line["supplier_commission_mode"], line["supplier_commission_value"]
        if mode != "none" and line["kind"] == "internal":
            blockers.append({"line_id": line["line_id"], "reason": "commission_on_internal_line"})
        commission = value if mode == "fixed" else (rdiv(cost * value, 10000) if mode == "percent" else 0)
        if mode == "percent" and value > 10000:
            raise ValueError("supplier commission percent above 10000 bps")
        # Direct lines are billed by the supplier to the client: agency income is service + commission only.
        margin = service + commission if line["kind"] == "direct" else sale - cost + service + commission
        if max(sale, cost, service, commission) > MAX_AMOUNT:
            raise ValueError("amount overflow")
        lines.append({"line_id": line["line_id"], "currency": line["currency"], "sale_minor": sale, "cost_minor": cost,
                      "service_minor": service, "supplier_commission_minor": commission, "margin_minor": margin})
        t = totals.setdefault(line["currency"], {"currency": line["currency"], "sale_minor": 0, "cost_minor": 0, "service_minor": 0,
                                                 "supplier_commission_minor": 0, "gross_income_minor": 0})
        t["sale_minor"] += sale
        t["cost_minor"] += cost
        t["service_minor"] += service
        t["supplier_commission_minor"] += commission
        t["gross_income_minor"] += margin
    ordered = [totals[c] for c in sorted(totals)]
    groups = sum(1 for t in ordered if t["sale_minor"] or t["service_minor"])
    return {"lines": lines, "currency_totals": ordered, "invoice_groups": groups, "blockers": blockers}

def _hourly_fee_settlement(a):
    ids = [h["person_id"] for h in a["hours"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate person_id")
    covered = a["covered_hours_hundredths"]
    total = sum(h["approved_hours_hundredths"] for h in a["hours"])
    overage = max(total - covered, 0)
    per_person = []
    overage_minor = 0
    if overage and total:
        shares = _largest_remainder(overage, [h["approved_hours_hundredths"] for h in a["hours"]])
        for h, share in zip(a["hours"], shares):
            charge = rdiv(share * h["client_rate_minor"], 100) if a["overage_policy"] == "bill_at_client_rate" else 0
            overage_minor += charge
            per_person.append({"person_id": h["person_id"], "overage_hours_hundredths": share, "overage_minor": charge})
    else:
        per_person = [{"person_id": h["person_id"], "overage_hours_hundredths": 0, "overage_minor": 0} for h in a["hours"]]
    return {"currency": a["currency"], "implied_rate_minor": rdiv(a["instalment_minor"] * 100, covered), "total_hours_hundredths": total,
            "overage_hours_hundredths": overage, "unused_hours_hundredths": max(covered - total, 0), "overage_minor": overage_minor,
            "total_billable_minor": a["instalment_minor"] + overage_minor, "per_person": per_person}

def _payment_terms(a):
    base = _d(a["base_date"])
    if a["rule"] == "net_days":
        due = base + _timedelta(days=a["term_days"])
    elif a["rule"] == "end_of_month_then_days":
        due = _month_end(base) + _timedelta(days=a["term_days"])
    else:
        anchor = base.replace(day=15) if base.day <= 15 else _month_end(base)
        due = anchor + _timedelta(days=a["term_days"])
    due, rolled = _business_roll(due, a["holidays"], a["weekend_roll"])
    expected, rolled2 = _business_roll(due + _timedelta(days=a["delay_days"]), a["holidays"], a["weekend_roll"])
    return {"due_date": due.isoformat(), "expected_date": expected.isoformat(), "due_rolled_days": rolled, "expected_rolled_days": rolled2}

def _withholding(a):
    if a["method"] == "per_payment":
        taxable = max(a["payment_base_minor"] - a["non_taxable_minimum_minor"], 0)
        amount = rdiv(taxable * a["rate_bps"], 10000)
    else:
        taxable = max(a["accumulated_base_minor"] + a["payment_base_minor"] - a["non_taxable_minimum_minor"], 0)
        amount = max(rdiv(taxable * a["rate_bps"], 10000) - a["accumulated_withheld_minor"], 0)
    below = 0 < amount < a["minimum_withholding_minor"]
    return {"currency": a["currency"], "taxable_base_minor": taxable, "withholding_minor": 0 if below else amount, "below_minimum": below}

def _to_local(amount, exponent, rate_micro, local_exponent):
    return rdiv(amount * rate_micro * 10 ** local_exponent, 10 ** exponent * 1_000_000)

def _fx_revaluation(a):
    rates = {}
    for r in a["closing_rates"]:
        if r["currency"] in rates:
            raise ValueError("duplicate closing rate")
        rates[r["currency"]] = r["rate_micro"]
    out, gain, loss, seen = [], 0, 0, set()
    for item in a["items"]:
        if item["doc_id"] in seen:
            raise ValueError("duplicate doc_id")
        seen.add(item["doc_id"])
        if item["currency"] == a["local_currency"]:
            raise ValueError("local-currency items are not revalued")
        if item["currency"] not in rates:
            raise ValueError("missing closing rate for an item currency")
        book = _to_local(item["open_minor"], item["exponent"], item["book_rate_micro"], a["local_exponent"])
        closing = _to_local(item["open_minor"], item["exponent"], rates[item["currency"]], a["local_exponent"])
        delta = closing - book if item["side"] == "asset" else book - closing
        gain += max(delta, 0)
        loss += max(-delta, 0)
        out.append({"doc_id": item["doc_id"], "book_local_minor": book, "closing_local_minor": closing, "gain_loss_minor": delta})
    return {"local_currency": a["local_currency"], "items": out, "gain_minor": gain, "loss_minor": loss, "net_minor": gain - loss}

def _aging(a):
    limits = a["bucket_limits_days"]
    if limits != sorted(limits) or len(set(limits)) != len(limits):
        raise ValueError("bucket limits must strictly ascend")
    as_of = _d(a["as_of"])
    by_currency, seen = {}, set()
    for item in a["items"]:
        if item["doc_id"] in seen:
            raise ValueError("duplicate doc_id")
        seen.add(item["doc_id"])
        c = by_currency.setdefault(item["currency"], {"not_due": 0, "buckets": [0] * (len(limits) + 1), "weighted": 0, "overdue": 0, "positive": 0})
        days = (as_of - _d(item["due_date"])).days
        if days <= 0:
            c["not_due"] += item["open_minor"]
            continue
        index = next((i for i, limit in enumerate(limits) if days <= limit), len(limits))
        c["buckets"][index] += item["open_minor"]
        c["overdue"] += item["open_minor"]
        if item["open_minor"] > 0:
            c["weighted"] += item["open_minor"] * days
            c["positive"] += item["open_minor"]
    currencies = []
    for currency in sorted(by_currency):
        c = by_currency[currency]
        buckets, lower = [], 1
        for i, amount in enumerate(c["buckets"]):
            upper = limits[i] if i < len(limits) else None
            buckets.append({"from_days": lower, "to_days": upper, "amount_minor": amount})
            lower = (upper or 0) + 1
        currencies.append({"currency": currency, "not_due_minor": c["not_due"], "total_minor": c["not_due"] + c["overdue"], "buckets": buckets,
                           "weighted_days_overdue": rdiv(c["weighted"], c["positive"]) if c["positive"] > 0 else None})
    return {"as_of": a["as_of"], "currencies": currencies}

def _largest_remainder(amount, weights):
    total = sum(weights)
    if total <= 0:
        raise ValueError("weights must sum to a positive number")
    sign = -1 if amount < 0 else 1
    magnitude = abs(amount)
    floors = [magnitude * w // total for w in weights]
    remainders = sorted(range(len(weights)), key=lambda i: (-(magnitude * weights[i] % total), i))
    for i in remainders[: magnitude - sum(floors)]:
        floors[i] += 1
    return [sign * x for x in floors]

def _allocate(a):
    ids = [w["target_id"] for w in a["weights"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate target_id")
    shares = _largest_remainder(a["amount_minor"], [w["weight"] for w in a["weights"]])
    return {"currency": a["currency"], "allocations": [{"target_id": t, "amount_minor": s} for t, s in zip(ids, shares)], "total_minor": sum(shares)}

def _installment_schedule(a):
    advance = rdiv(a["gross_minor"] * a["advance_bps"], 10000)
    rest = a["gross_minor"] - advance
    n = a["installments"]
    each = rest // n
    schedule = [{"number": i + 1, "month": _add_months(a["start_month"], i), "amount_minor": each} for i in range(n)]
    schedule[-1]["amount_minor"] += rest - each * n
    return {"currency": a["currency"], "advance_minor": advance, "installments": schedule, "total_minor": advance + rest}

def _depreciation_schedule(a):
    if a["residual_minor"] > a["cost_minor"]:
        raise ValueError("residual exceeds cost")
    depreciable = a["cost_minor"] - a["residual_minor"]
    acquired = _d(a["acquisition_date"])
    first = f"{acquired.year:04d}-{acquired.month:02d}"
    if a["first_month_rule"] == "following_month":
        first = _add_months(first, 1)
    n = a["life_months"]
    charges = _largest_remainder(depreciable, [1] * n) if depreciable else [0] * n
    months, accumulated = [], 0
    for i, charge in enumerate(charges):
        accumulated += charge
        months.append({"month": _add_months(first, i), "charge_minor": charge, "accumulated_minor": accumulated, "net_book_minor": a["cost_minor"] - accumulated})
    return {"currency": a["currency"], "depreciable_minor": depreciable, "first_month": first, "last_month": months[-1]["month"], "months": months}

def _journal_check(a):
    errors, totals, seen = [], {}, set()
    period = a["posting_date"][:7]
    if not a["lines"]:
        errors.append({"line_id": None, "reason": "no_lines"})
    if period in a["locked_periods"]:
        errors.append({"line_id": None, "reason": "locked_period"})
    for line in a["lines"]:
        if line["line_id"] in seen:
            errors.append({"line_id": line["line_id"], "reason": "duplicate_line_id"})
        seen.add(line["line_id"])
        if line["debit_minor"] and line["credit_minor"]:
            errors.append({"line_id": line["line_id"], "reason": "both_sides"})
        if not line["debit_minor"] and not line["credit_minor"]:
            errors.append({"line_id": line["line_id"], "reason": "zero_line"})
        if not line["required_dimensions_present"]:
            errors.append({"line_id": line["line_id"], "reason": "missing_dimension"})
        t = totals.setdefault(line["currency"], [0, 0])
        t[0] += line["debit_minor"]
        t[1] += line["credit_minor"]
    currencies = []
    for currency in sorted(totals):
        debit, credit = totals[currency]
        currencies.append({"currency": currency, "debit_minor": debit, "credit_minor": credit, "difference_minor": debit - credit})
        if debit != credit:
            errors.append({"line_id": None, "reason": "unbalanced_currency"})
    return {"entry_id": a["entry_id"], "status": "invalid" if errors else "valid", "currencies": currencies, "errors": errors}

def _period_starts(as_of, granularity, periods):
    if granularity == "week":
        start = as_of - _timedelta(days=as_of.weekday())
        return [start + _timedelta(weeks=i) for i in range(periods)]
    first = as_of.replace(day=1)
    return [_d(_add_months(first.isoformat()[:7], i) + "-01") for i in range(periods)]

def _cash_projection(a):
    as_of = _d(a["as_of"])
    starts = _period_starts(as_of, a["granularity"], a["periods"])
    horizon_end = _d(_add_months(starts[-1].isoformat()[:7], 1) + "-01") if a["granularity"] == "month" else starts[-1] + _timedelta(weeks=1)
    opening = {}
    for b in a["opening_balances"]:
        if b["currency"] in opening:
            raise ValueError("duplicate opening balance currency")
        opening[b["currency"]] = b["amount_minor"]
    data, seen = {}, set()
    def bucket(currency):
        return data.setdefault(currency, {"periods": [[0, 0, 0, 0] for _ in starts], "overdue": [0, 0], "beyond": [0, 0]})
    for item in a["items"]:
        if item["item_id"] in seen:
            raise ValueError("duplicate item_id")
        seen.add(item["item_id"])
        if item["status"] == "confirmed" and item["probability_bps"] != 10000:
            raise ValueError("confirmed items must carry probability_bps 10000")
        amount = item["amount_minor"] if item["status"] == "confirmed" else rdiv(item["amount_minor"] * item["probability_bps"], 10000)
        when, _ = _business_roll(_d(item["base_date"]) + _timedelta(days=item["term_days"] + item["delay_days"]), a["holidays"])
        c = bucket(item["currency"])
        side = 0 if item["direction"] == "in" else 1
        if when < as_of:
            c["overdue"][side] += amount
            when = as_of
        if when >= horizon_end:
            c["beyond"][side] += amount
            continue
        index = max(i for i, s in enumerate(starts) if s <= when) if when >= starts[0] else 0
        column = (0 if item["status"] == "confirmed" else 1) + (0 if side == 0 else 2)
        c["periods"][index][column] += amount
    currencies = []
    for currency in sorted(set(data) | set(opening)):
        c = bucket(currency)
        balance = opening.get(currency, 0)
        periods, minimum, minimum_start = [], None, starts[0]
        for start, (ic, ie, oc, oe) in zip(starts, c["periods"]):
            balance += ic + ie - oc - oe
            periods.append({"period_start": start.isoformat(), "in_confirmed_minor": ic, "in_expected_minor": ie,
                            "out_confirmed_minor": oc, "out_expected_minor": oe, "closing_minor": balance})
            if minimum is None or balance < minimum:
                minimum, minimum_start = balance, start
        currencies.append({"currency": currency, "opening_minor": opening.get(currency, 0), "overdue_in_minor": c["overdue"][0],
                           "overdue_out_minor": c["overdue"][1], "beyond_horizon_in_minor": c["beyond"][0], "beyond_horizon_out_minor": c["beyond"][1],
                           "periods": periods, "minimum_closing_minor": minimum, "minimum_period_start": minimum_start.isoformat()})
    return {"as_of": a["as_of"], "granularity": a["granularity"], "currencies": currencies}

def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def _spot_match(a):
    for label, key in (("ordered", "spot_id"), ("aired", "event_id")):
        ids = [x[key] for x in a[label]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"duplicate {key}")
    candidates = {}
    for spot in a["ordered"]:
        start, end = _minutes(spot["window_start"]), _minutes(spot["window_end"])
        if end < start:
            raise ValueError("window_end precedes window_start; split windows that cross midnight")
        found = []
        for event in a["aired"]:
            if event["station_id"] != spot["station_id"] or event["air_date"] != spot["air_date"]:
                continue
            if a["match_material"] and event["material_id"] != spot["material_id"]:
                continue
            t = _minutes(event["air_time"])
            if start <= t <= end:
                found.append((event["event_id"], "exact"))
            elif end < t <= end + a["tolerance_minutes"]:
                found.append((event["event_id"], "tolerance"))
        candidates[spot["spot_id"]] = found
    # Order-independent assignment: first exact matches, then exact-or-tolerance. A pair is
    # assigned only when the spot has one open candidate event and that event has one open
    # claimant spot; anything still contested is returned as ambiguous for a human decision.
    matches, used = {}, set()
    for allowed in (("exact",), ("exact", "tolerance")):
        changed = True
        while changed:
            changed = False
            open_claims = {}
            for spot_id, found in candidates.items():
                if spot_id in matches:
                    continue
                for event_id, kind in found:
                    if event_id not in used and kind in allowed:
                        open_claims.setdefault(event_id, set()).add(spot_id)
            for spot_id in sorted(candidates):
                if spot_id in matches:
                    continue
                options = [c for c in candidates[spot_id] if c[0] not in used and c[1] in allowed]
                if len(options) == 1 and open_claims.get(options[0][0]) == {spot_id}:
                    matches[spot_id] = options[0]
                    used.add(options[0][0])
                    changed = True
    ambiguous, missing = [], []
    for spot in a["ordered"]:
        sid = spot["spot_id"]
        if sid in matches:
            continue
        open_found = [c[0] for c in candidates[sid] if c[0] not in used]
        if open_found:
            ambiguous.append({"spot_id": sid, "candidate_event_ids": sorted(open_found)})
        else:
            missing.append(sid)
    claimed = used | {e for x in ambiguous for e in x["candidate_event_ids"]}
    return {"matches": [{"spot_id": s["spot_id"], "event_id": matches[s["spot_id"]][0], "kind": matches[s["spot_id"]][1]} for s in a["ordered"] if s["spot_id"] in matches],
            "ambiguous": ambiguous, "ordered_not_aired": missing,
            "aired_not_ordered": [e["event_id"] for e in a["aired"] if e["event_id"] not in claimed]}

def _credit_exposure(a):
    exposure = a["ar_open_minor"] + a["approved_unbilled_minor"] + a["requested_minor"]
    within = exposure <= a["credit_limit_minor"]
    return {"currency": a["currency"], "exposure_after_minor": exposure, "headroom_minor": a["credit_limit_minor"] - exposure,
            "within_limit": within, "requires_override_approval": not within}

def _invoice_check(a):
    ids = [l["line_id"] for l in a["lines"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate line_id")
    by_rate = {}
    for line in a["lines"]:
        r = by_rate.setdefault(line["vat_bps"], [0, 0])
        r[0] += line["net_minor"]
        r[1] += rdiv(line["net_minor"] * line["vat_bps"], 10000)
    net = sum(v[0] for v in by_rate.values())
    vat = sum(v[1] for v in by_rate.values())
    computed = net + vat + a["perceptions_minor"] + a["other_charges_minor"] - a["withholdings_netted_minor"]
    diff = a["declared_total_minor"] - computed
    status = "matched" if diff == 0 else ("rounding_adjustment" if abs(diff) <= a["rounding_tolerance_minor"] else "mismatch")
    return {"currency": a["currency"], "net_minor": net, "vat_minor": vat, "computed_total_minor": computed, "difference_minor": diff, "status": status,
            "vat_by_rate": [{"vat_bps": k, "net_minor": by_rate[k][0], "vat_minor": by_rate[k][1]} for k in sorted(by_rate)]}

def check_approval_rules(rules):
    """Shared structural rules for AGENCY.md approvals; raises ValueError on anything that would weaken human approval."""
    seen = set()
    for i, rule in enumerate(rules):
        key = (rule["action"], rule["currency"])
        if key in seen:
            raise ValueError(f"approvals[{i}]: duplicate rule for {rule['action']} in {rule['currency']}")
        seen.add(key)
        tiers = rule["tiers"]
        if not tiers:
            raise ValueError(f"approvals[{i}]: at least one tier is required")
        if tiers[-1]["up_to_minor"] is not None:
            raise ValueError(f"approvals[{i}]: the last tier must be unbounded (up_to_minor null)")
        previous = -1
        for j, tier in enumerate(tiers):
            if not tier["roles"] or len(set(tier["roles"])) != len(tier["roles"]):
                raise ValueError(f"approvals[{i}].tiers[{j}]: roles must be non-empty and unique")
            if any(non_human(role) for role in tier["roles"]):
                raise ValueError(f"approvals[{i}].tiers[{j}]: approvers must be accountable human roles")
            if j and not set(tiers[j - 1]["roles"]) <= set(tier["roles"]):
                raise ValueError(f"approvals[{i}].tiers[{j}]: a higher tier must keep every approver of the tier below and may only add more")
            if j < len(tiers) - 1:
                if tier["up_to_minor"] is None or tier["up_to_minor"] <= previous:
                    raise ValueError(f"approvals[{i}].tiers[{j}]: thresholds must increase and only the last tier is unbounded")
                previous = tier["up_to_minor"]

def _approval_route(a):
    check_approval_rules(a["rules"])
    base = {"policy_version": a["policy_version"], "action": a["action"], "currency": a["currency"], "amount_minor": a["amount_minor"],
            "human_approval_required": True, "authorizes_execution": False}
    for rule in a["rules"]:
        if rule["action"] == a["action"] and rule["currency"] == a["currency"]:
            for index, tier in enumerate(rule["tiers"]):
                if tier["up_to_minor"] is None or a["amount_minor"] <= tier["up_to_minor"]:
                    return {**base, "status": "routed", "tier_index": index, "approver_roles": list(tier["roles"]), "quorum": "all_distinct"}
    return {**base, "status": "no_rule_confirm_locally", "tier_index": None, "approver_roles": [], "quorum": "confirm_locally"}

ERP_TOOLS = {
    "job_number": _job_number, "media_line_cost": _media_line_cost, "discount_cascade": _discount_cascade,
    "audience_metrics": _audience_metrics, "tiered_commission": _tiered_commission, "estimate_totals": _estimate_totals,
    "hourly_fee_settlement": _hourly_fee_settlement, "payment_terms": _payment_terms, "withholding": _withholding,
    "fx_revaluation": _fx_revaluation, "aging": _aging, "allocate": _allocate, "installment_schedule": _installment_schedule,
    "depreciation_schedule": _depreciation_schedule, "journal_check": _journal_check, "cash_projection": _cash_projection,
    "spot_match": _spot_match, "credit_exposure": _credit_exposure, "invoice_check": _invoice_check,
    "approval_route": _approval_route,
}
assert set(ERP_TOOLS) == set(ERP_SCHEMAS) == set(ERP_OUTPUT_SCHEMAS) == set(ERP_DESCRIPTIONS)
SCHEMAS.update(ERP_SCHEMAS)
OUTPUT_SCHEMAS.update(ERP_OUTPUT_SCHEMAS)
DESCRIPTIONS = {
    "plan_diff": "Compare normalized plan lines and flag committed changes; does not revise orders or approve execution.",
    "budget_check": "Calculate available budget from disjoint balances; does not reserve funds.",
    "reconcile": "Compare normalized order, delivery and invoice amounts; does not post entries.",
    "flat_rebate": "Calculate a flat rebate and client share; for tiers use tiered_commission.",
    "margin": "Calculate agency margin separately from managed media spend.",
    "payload_digest": "Hash a JSON proposal; this hash cannot authorize execution.",
    **ERP_DESCRIPTIONS,
}

def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON field")
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))

def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("Usage: agency_tools.py TOOL < input.json")
        raw = sys.stdin.buffer.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("Input exceeds 1 MiB")
        print(json.dumps(run(sys.argv[1], strict_json(raw)), allow_nan=False))
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
