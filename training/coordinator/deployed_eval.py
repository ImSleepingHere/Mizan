"""Measure the deployed coordinator exactly as the app calls it (live llama-server, production prompt and JSON schema).

Runs the frozen 120-case test set three times through backend.agent_engine.model_decision:
  1. pretrained            - adapter disabled, original live prompt (what Mizan ran before)
  2. pretrained-tunedprompt - adapter loaded but at scale 0, training prompt: isolates the prompt change
  3. fine-tuned            - adapter enabled, training prompt (what Mizan runs now)
Arm 2 vs arm 3 is the effect of fine-tuning alone (same prompt, same request, only the adapter scale differs).
The 120 cases come from the same generator as the training data: this measures the implemented workflow, not real-world ability.
Run from the project root with the app environment:  .venv\\Scripts\\python.exe training\\coordinator\\deployed_eval.py
"""
from pathlib import Path
import json, os, sys, time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from benchmark import grade  # noqa: E402
from backend import local_model  # noqa: E402
from backend.agent_engine import model_decision  # noqa: E402

KEYS = ['valid', 'routing_correct', 'disposition_correct', 'pass', 'premature_finalization']


_structured = local_model.structured


def _base_only(system, content, schema, timeout=90, adapter_id=None, compact=False):
    return _structured(system, content, schema, timeout, None, compact)


def wait_for_model(limit=300):
    began = time.monotonic()
    while time.monotonic() - began < limit:
        if local_model.status()['available']:
            return
        time.sleep(3)
    raise SystemExit('Model server is not running on port 11435.')


def run(mode, cases):
    os.environ['MIZAN_COORDINATOR_ADAPTER'] = '0' if mode == 'pretrained' else '1'
    local_model._ADAPTERS['checked'] = 0.0
    adapter = local_model.coordinator_adapter()
    # Arm 2: the exact fine-tuned request (training prompt, compact JSON) with every adapter at scale 0.
    local_model.structured = _base_only if mode == 'pretrained-tunedprompt' else _structured
    if mode != 'pretrained' and not adapter:
        raise SystemExit('The coordinator adapter is not loaded in the model server. Restart it with scripts/restart-model.ps1.')
    results, began = [], time.monotonic()
    for n, case in enumerate(cases, 1):
        actions = ['delegate'] if case['context']['pending_specialists'] else ['finalize']
        try:
            decision, telemetry = model_decision('coordinator', case['context'], actions)
            output = decision.model_dump(); metrics = grade(output, case)
        except Exception as error:  # schema/validation failures count as invalid, as in production
            output = {'error': str(error)[:300]}; telemetry = {}
            metrics = {k: False for k in KEYS}
        results.append({'id': case['id'], 'kind': case['kind'], 'language': case['language'], 'output': output,
                        'metrics': metrics, 'model': telemetry.get('model')})
        if n % 20 == 0 or n == len(cases):
            print(json.dumps({'mode': mode, 'done': n, 'total': len(cases)}), flush=True)
    summary = {'mode': mode, 'count': len(results), 'seconds': round(time.monotonic() - began, 1),
               'metrics': {k: sum(bool(r['metrics'][k]) for r in results) for k in KEYS}}
    return results, summary


def main():
    wait_for_model()
    cases = [json.loads(l) for l in (HERE / 'test.jsonl').read_text(encoding='utf8').splitlines() if l.strip()]
    out = {}
    for mode in ['pretrained', 'pretrained-tunedprompt', 'fine-tuned']:
        results, summary = run(mode, cases)
        (HERE / f'deployed_{mode.replace("-", "")}_predictions.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
        out[mode] = summary; print(json.dumps(summary), flush=True)
    os.environ['MIZAN_COORDINATOR_ADAPTER'] = '1'; local_model.structured = _structured
    (HERE / 'deployed_eval_summary.json').write_text(json.dumps(out, indent=2), encoding='utf8')


if __name__ == '__main__':
    main()
