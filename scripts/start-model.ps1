$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$modelFile=Join-Path $projectRoot '.models\qwen3-8b.gguf'
$runtimeFile=Join-Path $projectRoot '.runtime\ollama\lib\ollama\llama-server.exe'
$adapterFile=Join-Path $projectRoot '.models\mizan-coordinator-lora.gguf'
if (-not (Test-Path -LiteralPath $modelFile)) { throw 'Install the local model first.' }
try { $modelHealth=Invoke-RestMethod 'http://127.0.0.1:11435/health' -TimeoutSec 2; if ($modelHealth.status -eq 'ok') { return } } catch {}
$env:GGML_BACKEND_PATH=Join-Path $projectRoot '.runtime\ollama\lib\ollama\cuda_v12\ggml-cuda.dll'
$env:PATH=(Join-Path $projectRoot '.runtime\ollama\lib\ollama\cuda_v12')+';'+$env:PATH
# Fine-tuned coordinator adapter: loaded with scale 0 and enabled per request for coordinator calls only.
$modelArgs=@('-m',('"'+$modelFile+'"'),'--host','127.0.0.1','--port','11435','--alias','qwen3-8b','--ctx-size','16384','--parallel','1','--gpu-layers','99','--no-webui')
if (Test-Path -LiteralPath $adapterFile) { $modelArgs+=@('--lora',('"'+$adapterFile+'"'),'--lora-init-without-apply') }
$modelProcess=Start-Process -FilePath $runtimeFile -ArgumentList $modelArgs -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'work\model.stdout.log') -RedirectStandardError (Join-Path $projectRoot 'work\model.stderr.log')
$modelProcess.Id | Set-Content (Join-Path $projectRoot 'work\model.pid')
Write-Host 'Local model is starting. Mizan will show when it is ready.'
