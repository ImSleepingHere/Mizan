$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$modelFile=Join-Path $projectRoot '.models\qwen3-8b.gguf'
$runtimeFile=Join-Path $projectRoot '.runtime\ollama\lib\ollama\llama-server.exe'
$adapterFile=Join-Path $projectRoot '.models\mizan-coordinator-lora.gguf'
if (-not (Test-Path -LiteralPath $modelFile)) { throw 'Install the local model first.' }
try { $modelHealth=Invoke-RestMethod 'http://127.0.0.1:11435/health' -TimeoutSec 2; if ($modelHealth.status -eq 'ok') { return } } catch {}
# NVIDIA GPU -> CUDA engine with every layer on the GPU. No NVIDIA GPU (e.g. AMD/Intel laptops) -> the bundled CPU
# engines (llama.cpp picks the best one for the processor, e.g. zen4). Override with MIZAN_MODEL_DEVICE=cpu|cuda.
$device=$env:MIZAN_MODEL_DEVICE
if (-not $device) { $device='cpu'; try { if ((& nvidia-smi --query-gpu=name --format=csv,noheader 2>$null) -and $LASTEXITCODE -eq 0) { $device='cuda' } } catch {} }
$gpuLayers='0'
if ($device -eq 'cuda') {
    $env:GGML_BACKEND_PATH=Join-Path $projectRoot '.runtime\ollama\lib\ollama\cuda_v12\ggml-cuda.dll'
    $env:PATH=(Join-Path $projectRoot '.runtime\ollama\lib\ollama\cuda_v12')+';'+$env:PATH
    $gpuLayers='99'
} else {
    Remove-Item Env:GGML_BACKEND_PATH -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Force -Path (Join-Path $projectRoot 'work') | Out-Null
$device | Set-Content (Join-Path $projectRoot 'work\model.device')
# Fine-tuned coordinator adapter: loaded with scale 0 and enabled per request for coordinator calls only.
$modelArgs=@('-m',('"'+$modelFile+'"'),'--host','127.0.0.1','--port','11435','--alias','qwen3-8b','--ctx-size','16384','--parallel','1','--gpu-layers',$gpuLayers,'--no-webui')
if (Test-Path -LiteralPath $adapterFile) { $modelArgs+=@('--lora',('"'+$adapterFile+'"'),'--lora-init-without-apply') }
$modelProcess=Start-Process -FilePath $runtimeFile -ArgumentList $modelArgs -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'work\model.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'work\model.stderr.log')
$modelProcess.Id | Set-Content (Join-Path $projectRoot 'work\model.pid')
if ($device -eq 'cuda') { Write-Host 'Local model is starting on the NVIDIA GPU. Mizan will show when it is ready.' }
else { Write-Host 'Local model is starting on the processor (no NVIDIA GPU found). AI features will be slow; timetable features are unaffected.' }
