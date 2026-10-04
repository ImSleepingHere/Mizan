"""Local-only inference. No institutional data is sent to an AI provider."""
import json
import os
import threading
import time
from urllib.parse import urlparse
import httpx

MODEL=os.environ.get("MIZAN_MODEL","qwen3-8b")
LOCK=threading.Lock()
# The fine-tuned coordinator is a LoRA adapter loaded by llama-server (see scripts/start-model.ps1).
# It is applied only to coordinator calls; the other agents keep the unmodified base model.
ADAPTER_MARKER="coordinator"
_ADAPTERS={"checked":0.0,"items":[]}


def base_url():
    url=os.environ.get("MIZAN_MODEL_URL","http://127.0.0.1:11435")
    parsed=urlparse(url)
    if parsed.hostname not in {"127.0.0.1","localhost","::1"} or parsed.scheme!="http" or parsed.username or parsed.password:
        raise ValueError("Mizan model inference must use a local loopback service")
    return url.rstrip("/")


def adapter_enabled():
    """Set MIZAN_COORDINATOR_ADAPTER=0 to roll back to the pretrained coordinator without restarting the model."""
    return os.environ.get("MIZAN_COORDINATOR_ADAPTER","1")!="0"


def adapters(max_age=30):
    """LoRA adapters loaded in the model server, cached briefly."""
    if time.monotonic()-_ADAPTERS["checked"]<max_age:
        return _ADAPTERS["items"]
    try:
        with httpx.Client(base_url=base_url(),timeout=3,trust_env=False) as client:
            response=client.get('/lora-adapters');response.raise_for_status()
        items=[a for a in response.json() if isinstance(a,dict) and "id" in a]
    except (httpx.HTTPError,ValueError):
        items=[]
    _ADAPTERS.update(checked=time.monotonic(),items=items)
    return items


def coordinator_adapter():
    if not adapter_enabled():
        return None
    return next((a for a in adapters() if ADAPTER_MARKER in str(a.get("path","")).lower()),None)


def status():
    try:
        with httpx.Client(base_url=base_url(),timeout=3,trust_env=False) as client:
            response=client.get('/health');response.raise_for_status()
        adapter=coordinator_adapter()
        return dict(available=True,model=MODEL,local=True,message="Ready",
                    coordinator_adapter=bool(adapter),coordinator_model=("fine-tuned" if adapter else "pretrained"))
    except (httpx.HTTPError,ValueError):
        return dict(available=False,model=MODEL,local=True,message="Local model service is not running",
                    coordinator_adapter=False,coordinator_model="unavailable")


def structured(system,content,schema,timeout=90,adapter_id=None,compact=False):
    started=time.monotonic()
    # MIZAN_MODEL_TIMEOUT raises the wait for slow hardware (scripts/start.ps1 sets it when the model runs on the CPU).
    timeout=max(timeout,float(os.environ.get("MIZAN_MODEL_TIMEOUT") or 0))
    loaded=adapters()
    body={"model":MODEL,"stream":False,
          "messages":[{"role":"system","content":system},
                      {"role":"user","content":json.dumps(content,ensure_ascii=False,separators=(',',':') if compact else None)}],
          "response_format":{"type":"json_schema","json_schema":{"name":"decision","schema":schema}},
          "temperature":0,"max_tokens":900,"chat_template_kwargs":{"enable_thinking":False}}
    if loaded:
        # Explicit per-request scales: only the requested adapter is active; every other call runs the base model.
        body["lora"]=[{"id":a["id"],"scale":1.0 if a["id"]==adapter_id else 0.0} for a in loaded]
    with LOCK:
        with httpx.Client(base_url=base_url(),timeout=timeout,trust_env=False) as client:
            response=client.post('/v1/chat/completions',json=body)
            response.raise_for_status()
    result=response.json()
    text=result["choices"][0]["message"]["content"]
    try:
        data=json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("Local model returned invalid structured output") from exc
    return data,{"model":MODEL+("+coordinator-lora" if adapter_id is not None else ""),
                 "output_tokens":result.get("usage",{}).get("completion_tokens",0),
                 "input_tokens":result.get("usage",{}).get("prompt_tokens",0),
                 "duration_seconds":round(time.monotonic()-started,3)}
