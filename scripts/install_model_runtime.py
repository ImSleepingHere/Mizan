"""Install a pinned runtime bundle and Qwen3 8B GGUF inside this repository."""
import hashlib
from pathlib import Path
import zipfile
import httpx

ROOT=Path(__file__).resolve().parents[1]
VERSION="0.34.3"
URL=f"https://github.com/ollama/ollama/releases/download/v{VERSION}/ollama-windows-amd64.zip"
DIGEST="306ce9e81e3491d147f558e60d7a389499f244d10f71859c6e4e899241d1b4ae"

def install():
    archive=ROOT/"work"/f"ollama-{VERSION}.zip"
    archive.parent.mkdir(exist_ok=True)
    if not archive.exists() or hashlib.file_digest(archive.open("rb"),"sha256").hexdigest()!=DIGEST:
        with httpx.stream("GET",URL,follow_redirects=True,timeout=120) as response,archive.open("wb") as target:
            response.raise_for_status()
            read=0;reported=0
            for chunk in response.iter_bytes(1024*1024):
                target.write(chunk);read+=len(chunk)
                if read-reported>100*1024*1024:
                    print(f"Runtime download: {read//(1024*1024)} MiB",flush=True);reported=read
    with archive.open("rb") as stream:
        assert hashlib.file_digest(stream,"sha256").hexdigest()==DIGEST,"Runtime checksum mismatch"
    destination=(ROOT/".runtime"/"ollama").resolve()
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        for entry in bundle.infolist():
            resolved=(destination/entry.filename).resolve()
            if not resolved.is_relative_to(destination):
                raise ValueError("Unsafe archive path")
        bundle.extractall(destination)
    print(f"Verified Ollama {VERSION} installed in .runtime/ollama",flush=True)

def install_model():
    digest="a3de86cd1c132c822487ededd47a324c50491393e6565cd14bafa40d0b8e686f"
    destination=ROOT/".models"/"qwen3-8b.gguf"
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        with destination.open("rb") as source:
            if hashlib.file_digest(source,"sha256").hexdigest()==digest:
                print("Model checksum verified");return
    partial=destination.with_suffix(".download")
    with httpx.stream("GET","https://registry.ollama.ai/v2/library/qwen3/blobs/sha256:"+digest,follow_redirects=True,timeout=120) as response,partial.open("wb") as output:
        response.raise_for_status()
        for chunk in response.iter_bytes(4*1024*1024):output.write(chunk)
    with partial.open("rb") as source:
        if hashlib.file_digest(source,"sha256").hexdigest()!=digest:raise ValueError("Model checksum mismatch")
    partial.replace(destination)
    print("Qwen3 8B model verified")

if __name__=="__main__":
    install()
    install_model()
