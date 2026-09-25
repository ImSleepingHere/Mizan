"""Secondary control from PROTOCOL.md: the deployed GGUF model on the same frozen test set.

Runs against the live Mizan model server (llama-server on 127.0.0.1:11435).
Quantization and runtime differ from the NF4 comparison, so this is reported separately.
Uses only the standard library, so it runs with the project's normal .venv.
"""
from pathlib import Path
import json, re, time, urllib.request
from benchmark import messages, grade

ROOT = Path(__file__).resolve().parent
BASE = 'http://127.0.0.1:11435'


def wait_for_server(limit=300):
    began = time.monotonic()
    while time.monotonic() - began < limit:
        try:
            with urllib.request.urlopen(BASE + '/health', timeout=3) as r:
                if json.load(r).get('status') == 'ok':
                    return
        except Exception:
            pass
        time.sleep(3)
    raise SystemExit('Model server on port 11435 did not become healthy; start it with scripts/start-model.ps1')


def ask(case):
    body = {
        'model': 'qwen3-8b',
        'messages': messages(case),
        'temperature': 0,
        'max_tokens': 128,  # same output cap as the NF4 comparison
        'chat_template_kwargs': {'enable_thinking': False},
    }
    req = urllib.request.Request(BASE + '/v1/chat/completions', data=json.dumps(body).encode('utf8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)['choices'][0]['message'].get('content') or ''


def main():
    wait_for_server()
    cases = [json.loads(l) for l in (ROOT / 'test.jsonl').read_text(encoding='utf8').splitlines() if l.strip()]
    results, began = [], time.monotonic()
    for n, case in enumerate(cases, 1):
        raw = ask(case)
        # If the server ignores enable_thinking, strip the reasoning block before grading and count it.
        clean = re.sub(r'<think>.*?</think>', '', raw, flags=re.S).strip()
        results.append({'id': case['id'], 'kind': case['kind'], 'language': case['language'], 'output': raw,
                        'thinking_leaked': '<think>' in raw, 'metrics': grade(clean, case)})
        if n % 10 == 0 or n == len(cases):
            print(json.dumps({'evaluation': 'gguf_baseline', 'done': n, 'total': len(cases)}), flush=True)
    (ROOT / 'gguf_baseline_predictions.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')
    keys = ['valid', 'routing_correct', 'disposition_correct', 'pass', 'premature_finalization']
    summary = {'label': 'gguf_baseline', 'count': len(results), 'seconds': round(time.monotonic() - began, 2),
               'metrics': {k: sum(r['metrics'][k] for r in results) for k in keys},
               'thinking_leaked': sum(r['thinking_leaked'] for r in results)}
    (ROOT / 'gguf_baseline_summary.json').write_text(json.dumps(summary, indent=2), encoding='utf8')
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
