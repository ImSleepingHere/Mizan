"""Score the live interpreter (base model, no adapter) on the dev set or, once, on the handwritten test set.

  .venv\\Scripts\\python.exe training\\interpreter\\eval_interpreter.py --set dev
  .venv\\Scripts\\python.exe training\\interpreter\\eval_interpreter.py --set test --final

The test set is scored once: the run refuses to overwrite existing test results.
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
from backend import interpreter, local_model  # noqa: E402
from scoring import score_case, summarize  # noqa: E402

FROZEN_TEST_SHA256 = "c28ce2a667fc3617107abe14543ae19ad8b3af6525075243a007ed61fd73a765"  # canonical LF, same cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["dev", "test"], required=True)
    parser.add_argument("--final", action="store_true", help="required to score the handwritten test set")
    parser.add_argument("--only", nargs="*", help="dev only: case IDs to run")
    args = parser.parse_args()
    path = HERE / ("dev.jsonl" if args.set == "dev" else "handwritten_test.jsonl")
    out = HERE / f"results_{args.set}.json"
    if args.set == "test":
        if not args.final:
            sys.exit("The handwritten test set is scored once, at the end. Pass --final to do that.")
        if out.exists():
            sys.exit(f"{out.name} already exists; the test set has been scored.")
        digest = hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if digest != FROZEN_TEST_SHA256:
            sys.exit("handwritten_test.jsonl differs from the frozen version; refusing to score.")
        if args.only:
            sys.exit("--only is not allowed on the test set")
    if not local_model.status()["available"]:
        sys.exit("Local model service is not running (scripts/start-model.ps1).")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if args.only:
        cases = [c for c in cases if c["id"] in set(args.only)]
    results, predictions, started = [], [], time.monotonic()
    for case in cases:
        try:
            interp, telemetry = interpreter.interpret(case["text"], case["context"])
            predicted = interp.model_dump()
            error = None
        except Exception as exc:  # invalid or unparseable output counts as a failure
            predicted, telemetry, error = None, {}, f"{type(exc).__name__}: {str(exc)[:300]}"
        scored = score_case(case, predicted)
        results.append(scored)
        predictions.append(dict(id=case["id"], predicted=predicted, error=error, telemetry=telemetry, passed=scored["passed"]))
        mark = "PASS" if scored["passed"] else "fail " + ",".join(f for f, ok in scored["fields"].items() if not ok)
        print(f"{case['id']} [{case['lang']}] {mark}" + (f"  silent:{scored['silent_guesses']}" if scored["silent_guesses"] else "") + (f"  ERROR {error}" if error else ""))
    summary = summarize(results)
    summary.update(set=args.set, model=local_model.MODEL, adapter="none (base model)", seconds=round(time.monotonic() - started, 1))
    out.write_text(json.dumps(dict(summary=summary, predictions=predictions), ensure_ascii=False, indent=2), encoding="utf-8")
    o = summary["overall"]
    print(f"\nstrict {o['strict_pass']}/{o['cases']} · valid {o['valid']} · silent-guess cases {o['silent_guess_cases']} · false-flag cases {o['false_flag_cases']}")
    for lang, b in summary["by_language"].items():
        print(f"  {lang}: strict {b['strict_pass']}/{b['cases']} · silent {b['silent_guess_cases']}")


if __name__ == "__main__":
    main()
