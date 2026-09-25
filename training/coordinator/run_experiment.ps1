# Coordinator fine-tuning experiment: one-shot runner.
# Repairs the training environment if needed, pauses the Mizan model server to free the GPU,
# runs smoke test -> training -> paired evaluation, restores the server, runs the GGUF control,
# and writes coordinator_report.md. The live Mizan model is never replaced.
#
# Usage (from anywhere):  powershell -ExecutionPolicy Bypass -File training\coordinator\run_experiment.ps1
# Optional: -SkipTraining (re-evaluate an existing checkpoint)  -SkipGguf (skip the secondary control)
param([switch]$SkipTraining, [switch]$SkipGguf)

$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$root = (Resolve-Path (Join-Path $here '..\..')).Path
$trainPy = Join-Path $root '.training-venv\Scripts\python.exe'
$appPy = Join-Path $root '.venv\Scripts\python.exe'
$log = Join-Path $here 'run.log'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'
trap { Add-Content $log ("ERROR: " + ($_ | Out-String)); Write-Host $_ -ForegroundColor Red; break }

function Step($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan; Add-Content $log "`n=== $(Get-Date -Format s) $msg ===" }
function Run($label, $exe, [string[]]$argList) {
    # stdout goes to the console and run.log; stderr goes to <label>.stderr.log (tail copied to run.log on failure).
    $errFile = Join-Path $here (($label -replace '\W', '_') + '.stderr.log')
    $ErrorActionPreference = 'Continue'
    & $exe @argList 2> $errFile | Tee-Object -FilePath $log -Append
    $code = $LASTEXITCODE
    if ($code -ne 0) {
        Add-Content $log "FAILED: $label (exit code $code). Last stderr lines:"
        if (Test-Path $errFile) { Get-Content $errFile -Tail 60 | Out-String | Add-Content $log }
        throw "$label failed with exit code $code (see $log)"
    }
}
function TorchStatus { $ErrorActionPreference = 'Continue'; (& $trainPy -c "import torch;print(torch.__version__, torch.cuda.is_available())" 2>$null | Select-Object -Last 1) }

Set-Location $here
if (-not (Test-Path $trainPy)) { throw "Training environment not found at $trainPy" }

# 1. PyTorch must be the CUDA build. A later install replaced it with 2.14.0+cpu.
Step 'Checking PyTorch'
$status = TorchStatus
Write-Host "torch: $status"
Add-Content $log "torch: $status"
if ("$status" -notmatch 'True$') {
    Step 'Repairing PyTorch: reinstalling torch 2.8.0 (CUDA 12.8)'
    $ErrorActionPreference = 'Continue'
    for ($i = 0; $i -lt 3; $i++) { & $trainPy -m pip uninstall -y torch *> $null }
    $ErrorActionPreference = 'Stop'
    $site = Join-Path $root '.training-venv\Lib\site-packages'
    Get-ChildItem $site -Directory -Filter 'torch-*.dist-info' | Remove-Item -Recurse -Force
    if (Test-Path (Join-Path $site 'torch')) { Remove-Item (Join-Path $site 'torch') -Recurse -Force }
    $installed = $false
    for ($attempt = 1; $attempt -le 4 -and -not $installed; $attempt++) {
        Add-Content $log "torch download attempt $attempt"
        try { Run 'torch install' $trainPy @('-m', 'pip', 'install', '--no-deps', '--timeout', '120', '--retries', '10', 'torch==2.8.0', '--index-url', 'https://download.pytorch.org/whl/cu128'); $installed = $true }
        catch { Write-Host "Download attempt $attempt failed; retrying..." -ForegroundColor Yellow; Start-Sleep 10 }
    }
    if (-not $installed) { throw 'Could not download PyTorch after 4 attempts. Check the internet connection and run again.' }
    $status = TorchStatus
    Write-Host "torch: $status"
    if ("$status" -notmatch 'True$') { throw 'PyTorch still cannot see the GPU after repair. Stopping before any training.' }
}

# 2. Free the GPU: pause Mizan's llama-server (restored in the finally block).
Step 'Pausing Mizan model server'
$server = Get-Process llama-server -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$root*" }
$wasRunning = [bool]$server
if ($wasRunning) { $server | Stop-Process -Force; Start-Sleep 3; Write-Host 'Paused.' } else { Write-Host 'Not running.' }

try {
    if (-not $SkipTraining) {
        Step 'Smoke test (one training step)'
        Run 'smoke test' $trainPy @('-u', 'train.py', '--smoke')
        Step 'Training (2 epochs, LoRA r8, selection by validation loss)'
        Run 'training' $trainPy @('-u', 'train.py')
    }
    Step 'Paired evaluation on frozen test set (pretrained vs fine-tuned)'
    Run 'evaluation' $trainPy @('-u', 'train.py', '--evaluate-only')
}
finally {
    if ($wasRunning) {
        Step 'Restoring Mizan model server'
        & (Join-Path $root 'scripts\start-model.ps1')
    }
}

if (-not $SkipGguf) {
    if ($wasRunning -or (Get-Process llama-server -ErrorAction SilentlyContinue)) {
        Step 'Secondary control: deployed GGUF model'
        Run 'GGUF baseline' $appPy @('-u', 'gguf_baseline.py')
    } else { Write-Host 'Model server was not running; skipping GGUF control.' }
}

Step 'Writing report'
Run 'report' $appPy @('compare.py')
Write-Host "`nDone. Report: $(Join-Path $here 'coordinator_report.md')" -ForegroundColor Green
