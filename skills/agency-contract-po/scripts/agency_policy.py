#!/usr/bin/env python3
"""Validate an agency policy overlay (AGENCY.md). Python standard library; no network, clock or writes.

AGENCY.md holds the parameters of one agency (approval tiers, currencies, tax rates, chart of
accounts, job typologies, commercial defaults, enabled connectors). Only the fenced block tagged
``json agency-policy`` is policy; prose around it is commentary with no authority.

The overlay can tighten or parameterise the control contract, never relax it: every approval
tier names accountable human roles, segregation of duties stays on, secrets are rejected and
unknown fields are rejected.

Usage: agency_policy.py [PATH]   (default: ./AGENCY.md, then ~/.agency-erp/AGENCY.md)
Exit code 0 when valid, 1 otherwise. Output is JSON.
"""
import json
from pathlib import Path
import re
import sys
import unicodedata

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agency_tools import (APPROVAL_ACTIONS, APPROVAL_RULE, BPS, CURRENCY, DATE, LETTER, ROLE, VERSION_ID,  # noqa: E402
                          arr, check_approval_rules, enum, integer, non_human, obj, strict_json, validate)

MAX_BYTES = 262_144
SECTIONS = ("agency", "currencies", "roles", "approvals", "taxes", "fx", "jobs", "commercial", "collections", "accounting", "connectors")
PROFILES = ("solo", "studio", "performance", "agency")
TEXT = {"type": "string", "pattern": "^[^\\n\\r`<>]{1,160}$"}
COUNTRY = {"type": "string", "pattern": "^[A-Z]{2}$"}
TIMEZONE = {"type": "string", "pattern": "^(UTC|[A-Z][A-Za-z_]+(/[A-Za-z0-9_+-]+){1,2})$"}
VERSION = VERSION_ID
TAX_CODE = {"type": "string", "pattern": "^[A-Z0-9_]{2,20}$"}
ACCOUNT_CODE = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]{0,31}$"}
CONNECTOR = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{1,63}$"}

POLICY_SCHEMA = obj({
    "policy_version": VERSION,
    "agency": obj({"name": TEXT, "base_currency": CURRENCY, "countries": arr(COUNTRY, 30), "timezone": TIMEZONE,
                   "fiscal_year_start_month": integer(1, 12)}),
    "currencies": arr(obj({"code": CURRENCY, "exponent": integer(0, 4)}), 30),
    "roles": arr(ROLE, 50),
    "segregation_of_duties": {"type": "boolean"},
    "approvals": arr(APPROVAL_RULE, 200),
    "taxes": obj({"reviewed_by_role": ROLE, "reviewed_on": DATE,
                  "rates": arr(obj({"code": TAX_CODE, "country": COUNTRY, "kind": enum("vat", "withholding", "perception", "other"),
                                    "rate_bps": BPS, "applies_to": TEXT}), 200)}),
    "fx": obj({"source": TEXT, "revaluation": enum("monthly", "quarterly", "none")}),
    "jobs": obj({"typologies": arr(obj({"code": LETTER, "label": TEXT, "sales_allowed": {"type": "boolean"}}), 26)}),
    "commercial": obj({"default_payment_terms_days": integer(0, 365), "default_agency_fee_bps": BPS,
                       "overcommission_engine": enum("flat", "value_scale", "slab", "marginal", "stepped", "none"),
                       "plan_change_tolerance_bps": BPS}),
    "collections": obj({"dunning_days": arr(integer(1, 3650), 10), "credit_limit_review": enum("monthly", "quarterly", "annual")}),
    "accounting": obj({"close_day": integer(1, 28), "accounts": arr(obj({"purpose": ROLE, "code": ACCOUNT_CODE}), 200)}),
    "connectors": obj({"profile": enum(*PROFILES), "enabled": arr(CONNECTOR, 50)}),
})

BLOCK = re.compile(r"^```json agency-policy[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
POLICY_TAG = re.compile(r"(?i)agency[\s_-]*policy")
SECRET_PATTERNS = (
    ("credential assignment", re.compile(r"(?i)\b(api[_-]?key|secret|password|passwd|client[_-]?secret|access[_-]?token|refresh[_-]?token|bearer)\b\s*[:=]")),
    ("bearer token", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{16,}")),
    ("provider key", re.compile(r"\b(sk|pk|rk)[-_](live|test|proj|ant)?[-_]?[A-Za-z0-9]{16,}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("long account or card number", re.compile(r"(?<![\d-])\d(?:[ -]?\d){14,}(?![\d-])")),
)
OVERRIDE_PATTERNS = re.compile(
    r"(?i)(ignore (all |any )?(previous|prior|above|the) (instructions|rules)|auto[- ]?approv|without (a |any )?(human )?(approval|sign[- ]?off|review)|"
    r"skip (the )?(approval|sign[- ]?off|review)|bypass|disable (the )?(control|approval|check)|"
    r"no (human )?(approval|sign[- ]?off|review|approver)s? (is |are )?(needed|required|necessary))")


def normalize(text):
    """NFKC, Unicode dashes to '-', CRLF to LF, so look-alike characters cannot slip past the checks."""
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    return re.sub(r"[\u2010-\u2015\u2212\u00ad]", "-", text)


def structure_errors(text):
    """The canonical block must be the only fence that mentions the policy, at top level, outside HTML comments."""
    errors, open_fence, canonical = [], None, 0
    lines = text.split("\n")
    for number, line in enumerate(lines, 1):
        match = FENCE.match(line)
        if open_fence is None:
            if match:
                info = match.group(2).strip()
                if POLICY_TAG.search(info):
                    if line.rstrip() != "```json agency-policy":
                        errors.append(f"line {number}: policy fences must be written exactly as ```json agency-policy")
                    else:
                        canonical += 1
                        before = "\n".join(lines[:number - 1])
                        if before.count("<!--") > before.count("-->"):
                            errors.append(f"line {number}: the policy block is inside an HTML comment")
                open_fence = match.group(1)
        elif match and match.group(1)[0] == open_fence[0] and len(match.group(1)) >= len(open_fence) and not match.group(2).strip():
            open_fence = None
        elif POLICY_TAG.search(line) and FENCE.match(line):
            errors.append(f"line {number}: a policy fence nested inside another code block is not allowed")
    if open_fence is not None:
        errors.append("unclosed code fence")
    return errors
REGISTRY_CANDIDATES = ("../integrations/registry.json", "../references/provider-registry.json")


def _registry_ids():
    here = Path(__file__).resolve().parent
    for candidate in REGISTRY_CANDIDATES:
        path = (here / candidate).resolve()
        if path.is_file():
            data = json.loads(path.read_text())
            items = data if isinstance(data, list) else data.get("providers", [])
            return {item["id"] for item in items}
    return None


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def _duplicates(values):
    seen, dup = set(), set()
    for value in values:
        (dup if value in seen else seen).add(value)
    return sorted(dup)


def check_text(text):
    """Return (policy, errors, warnings) for the full text of an AGENCY.md file."""
    errors, warnings = [], []
    text = normalize(text)
    errors += structure_errors(text)
    for label, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            errors.append(f"possible secret ({label}); keep credentials in the host's secret store, never in AGENCY.md")
    blocks = BLOCK.findall(text)
    if len(blocks) != 1:
        errors.append(f"expected exactly one ```json agency-policy block, found {len(blocks)}")
        return None, errors, warnings
    if OVERRIDE_PATTERNS.search(blocks[0]):
        errors.append("policy values try to weaken approvals or controls; AGENCY.md sets parameters, it cannot relax the control contract")
    elif OVERRIDE_PATTERNS.search(BLOCK.sub("", text)):
        warnings.append("commentary outside the policy block mentions weakening approvals or controls; it has no authority and agents ignore it")
    try:
        policy = strict_json(blocks[0])
        validate(policy, POLICY_SCHEMA, "$")
    except (ValueError, RecursionError) as exc:
        errors.append(f"policy block: {exc}")
        return None, errors, warnings
    values = normalize("\n".join(_strings(policy)))
    if OVERRIDE_PATTERNS.search(values) and not any("weaken" in e for e in errors):
        errors.append("policy values try to weaken approvals or controls; AGENCY.md sets parameters, it cannot relax the control contract")
    errors += semantic_errors(policy, warnings)
    return (policy if not errors else None), errors, warnings


def semantic_errors(p, warnings):
    errors = []
    if p["segregation_of_duties"] is not True:
        errors.append("segregation_of_duties must be true: the maker of a proposal can never approve it")
    roles = set(p["roles"])
    for name, values in (("roles", p["roles"]), ("currencies", [c["code"] for c in p["currencies"]]),
                         ("countries", p["agency"]["countries"]), ("taxes.rates", [t["code"] for t in p["taxes"]["rates"]]),
                         ("jobs.typologies", [t["code"] for t in p["jobs"]["typologies"]]),
                         ("accounting.accounts", [a["purpose"] for a in p["accounting"]["accounts"]]),
                         ("connectors.enabled", p["connectors"]["enabled"])):
        if _duplicates(values):
            errors.append(f"{name}: duplicate values {_duplicates(values)}")
    software = sorted(r for r in roles if non_human(r))
    if software:
        errors.append(f"roles: {software} name software, not accountable human roles")
    currencies = {c["code"] for c in p["currencies"]}
    if p["agency"]["base_currency"] not in currencies:
        errors.append("agency.base_currency must be listed in currencies")
    if p["taxes"]["reviewed_by_role"] not in roles:
        errors.append("taxes.reviewed_by_role must be listed in roles")
    try:
        check_approval_rules(p["approvals"])
    except ValueError as exc:
        errors.append(str(exc))
    for i, rule in enumerate(p["approvals"]):
        if rule["currency"] not in currencies:
            errors.append(f"approvals[{i}]: currency {rule['currency']} is not listed in currencies")
        unknown = sorted({r for t in rule["tiers"] for r in t["roles"]} - roles)
        if unknown:
            errors.append(f"approvals[{i}]: roles {unknown} are not listed in roles")
    days = p["collections"]["dunning_days"]
    if days != sorted(set(days)):
        errors.append("collections.dunning_days must be strictly increasing")
    countries = set(p["agency"]["countries"])
    for rate in p["taxes"]["rates"]:
        if rate["country"] not in countries:
            errors.append(f"taxes.rates {rate['code']}: country {rate['country']} is not in agency.countries")
    known = _registry_ids()
    if known is None:
        warnings.append("connector registry not found; connector ids were not checked")
    else:
        unknown = sorted(set(p["connectors"]["enabled"]) - known)
        if unknown:
            errors.append(f"connectors.enabled: unknown connector ids {unknown}")
    covered = {r["action"] for r in p["approvals"]}
    missing = [a for a in APPROVAL_ACTIONS if a not in covered]
    if missing:
        warnings.append("no approval tiers for " + ", ".join(missing) + "; skills still require human approval and mark the approver as confirm locally")
    if not p["taxes"]["rates"]:
        warnings.append("taxes.rates is empty; tax skills treat rates as confirm locally")
    return errors


def check_file(path):
    path = Path(path)
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        return None, [f"{path} exceeds {MAX_BYTES} bytes"], []
    return check_text(raw.decode("utf-8"))


def default_path():
    for candidate in (Path.cwd() / "AGENCY.md", Path.home() / ".agency-erp" / "AGENCY.md"):
        if candidate.is_file():
            return candidate
    return None


def main(argv):
    if len(argv) > 2:
        print("Usage: agency_policy.py [PATH]", file=sys.stderr)
        return 2
    path = Path(argv[1]) if len(argv) == 2 else default_path()
    if path is None or not path.is_file():
        print(json.dumps({"valid": False, "errors": ["AGENCY.md not found (looked in ./AGENCY.md and ~/.agency-erp/AGENCY.md)"], "warnings": []}))
        return 1
    try:
        policy, errors, warnings = check_file(path)
    except (OSError, UnicodeError) as exc:
        policy, errors, warnings = None, [f"cannot read {path}: {exc}"], []
    report = {"valid": not errors, "path": str(path), "errors": errors, "warnings": warnings}
    if policy:
        report["policy_version"] = policy["policy_version"]
        report["approval_rules"] = len(policy["approvals"])
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
