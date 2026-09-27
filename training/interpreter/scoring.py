"""Scoring for interpreter test/dev sets. Strict exact match is the headline; per-field accuracy and
silent guesses (an expected unsupported code missing from the prediction) are reported by language."""
from collections import defaultdict

FIELDS = ["task", "scope", "target_sections", "day_filter", "move", "max_changes", "protected_sections", "locked_days",
          "keep_days", "keep_time", "keep_room", "allowed_time_window", "min_break", "day_to_empty", "slot_search",
          "date_scope.kind", "duration_change", "delivery_mode", "unsupported_codes", "needs_clarification", "date_note"]
DAY_ORDER = ["sun", "mon", "tue", "wed", "thu"]


def _days(v):
    return sorted(set(v or []), key=DAY_ORDER.index)


def normalize(field, value):
    """Order-insensitive lists and all-null objects treated as null, applied identically to both sides."""
    if isinstance(value, dict) and field not in {"date_scope.kind"}:
        value = dict(value)
        if "days" in value:
            value["days"] = _days(value["days"])
        if all(v is None for k, v in value.items() if k != "days") and not value.get("days") and field in {"move", "duration_change", "allowed_time_window"}:
            return None
    if field in {"target_sections"}:
        return sorted(set(value or []))
    if field in {"day_filter", "locked_days"}:
        return _days(value)
    if field == "protected_sections":
        return sorted([dict(section=p["section"], days=_days(p.get("days"))) for p in value or []], key=lambda p: p["section"])
    if field == "unsupported_codes":
        return sorted(set(value or []))
    return value


def get(record, field):
    if field == "unsupported_codes":
        return [u["code"] if isinstance(u, dict) else u for u in record.get("unsupported", [])]
    if field == "date_scope.kind":
        return (record.get("date_scope") or {}).get("kind")
    return record.get(field)


def field_ok(case, predicted, field):
    got = normalize(field, get(predicted, field))
    options = [get(case["expected"], field)] + list(case.get("acceptable", {}).get(field, []))
    if any(normalize(field, o) == got for o in options):
        return True
    # Dotted acceptable entries ("slot_search.same_time_for_all") relax one sub-field of an object.
    for key, alternatives in case.get("acceptable", {}).items():
        if key.startswith(field + ".") and isinstance(got, dict):
            sub = key.split(".", 1)[1]
            expected = normalize(field, get(case["expected"], field))
            if isinstance(expected, dict) and got.get(sub) in alternatives and {**expected, sub: got.get(sub)} == got:
                return True
    return False


def score_case(case, predicted):
    if predicted is None:
        fields = {f: False for f in FIELDS}
        return dict(id=case["id"], lang=case["lang"], valid=False, passed=False, fields=fields,
                    silent_guesses=sorted(get(case["expected"], "unsupported_codes")), false_flags=[])
    fields = {f: field_ok(case, predicted, f) for f in FIELDS}
    expected_codes = set(get(case["expected"], "unsupported_codes"))
    for alt in case.get("acceptable", {}).get("unsupported_codes", []):
        if set(alt) <= set(get(predicted, "unsupported_codes")):
            expected_codes = set(alt)
    got_codes = set(get(predicted, "unsupported_codes"))
    return dict(id=case["id"], lang=case["lang"], valid=True, passed=all(fields.values()), fields=fields,
                silent_guesses=sorted(expected_codes - got_codes), false_flags=sorted(got_codes - expected_codes))


def summarize(results):
    def block(rows):
        n = len(rows)
        return dict(cases=n, strict_pass=sum(r["passed"] for r in rows), valid=sum(r["valid"] for r in rows),
                    silent_guess_cases=sum(bool(r["silent_guesses"]) for r in rows),
                    silent_guess_codes=sum(len(r["silent_guesses"]) for r in rows),
                    false_flag_cases=sum(bool(r["false_flags"]) for r in rows),
                    field_accuracy={f: sum(r["fields"][f] for r in rows) for f in FIELDS})
    by_lang = defaultdict(list)
    for r in results:
        by_lang[r["lang"]].append(r)
    return dict(overall=block(results), by_language={k: block(v) for k, v in sorted(by_lang.items())},
                failures={r["id"]: [f for f, ok in r["fields"].items() if not ok] for r in results if not r["passed"]})
