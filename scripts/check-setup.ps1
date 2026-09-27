# Checks that this PC can run the Mizan demo and says exactly what is missing. Changes nothing.
$ErrorActionPreference = 'Continue'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$problems = 0
function Report([bool]$ok, [string]$what, [string]$fix, [switch]$optional) {
    if ($ok) { Write-Host "  [OK]   $what" -ForegroundColor Green }
    elseif ($optional) { Write-Host "  [WARN] $what - $fix" -ForegroundColor Yellow }
    else { Write-Host "  [MISS] $what - $fix" -ForegroundColor Red; $script:problems++ }
}
Write-Host "Mizan setup check`n"
Report (Test-Path '.venv\Scripts\python.exe') 'Python environment (.venv)' 'run scripts\setup.ps1'
Report (Test-Path 'frontend\dist\index.html') 'Built website (frontend\dist)' 'run scripts\setup.ps1'
Report (Test-Path '.runtime\ollama\lib\ollama\llama-server.exe') 'Model runtime (.runtime)' 'run: .venv\Scripts\python.exe scripts\install_model_runtime.py'
Report (Test-Path '.models\qwen3-8b.gguf') 'Base model Qwen3-8B (.models\qwen3-8b.gguf, 5.2 GB)' 'run: .venv\Scripts\python.exe scripts\install_model_runtime.py'
Report (Test-Path '.models\mizan-coordinator-lora.gguf') 'Fine-tuned coordinator adapter' 'pull the latest code from GitHub (it is in the repository)'
$gpu = $null
try { $gpu = (& nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null) } catch { }
Report ([bool]$gpu) ("NVIDIA GPU: " + ($(if ($gpu) { $gpu } else { 'none found' }))) 'the model will run on the CPU and be very slow; Ask Mizan, agents and CV analysis may time out' -optional
foreach ($port in 8000, 11435) {
    $busy = $false
    try { $busy = [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop) } catch { }
    Report (-not $busy) "Port $port free" 'Mizan (or another program) is already running; close it before starting' -optional
}
if (Test-Path 'data\mizan.sqlite3') { Write-Host '  [INFO] Demo database exists. Run "Reset Mizan Demo.cmd" before the demo for a clean start.' }
else { Write-Host '  [INFO] No demo database yet; it is created on first start.' }
Write-Host ''
if ($problems -eq 0) { Write-Host 'Ready. Double-click "Start Mizan.cmd" and open http://127.0.0.1:8000' -ForegroundColor Green }
else { Write-Host "$problems item(s) missing. Fix them in order, then run this check again. Full guide: docs\HANDOVER.md" -ForegroundColor Red }
