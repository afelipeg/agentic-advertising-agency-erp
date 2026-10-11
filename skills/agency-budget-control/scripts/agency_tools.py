#!/usr/bin/env python3
"""Read-only agency calculations. Python standard library; no network or ledger writes."""
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
    except (ValueError, TypeError, UnicodeError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
