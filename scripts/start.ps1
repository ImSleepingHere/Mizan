param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup.ps1 first to create the project environment.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\dist\index.html'))) { throw 'Build the frontend first with scripts/setup.ps1.' }
Set-Location -LiteralPath $projectRoot
if (Test-Path -LiteralPath (Join-Path $projectRoot '.models\qwen3-8b.gguf')) { & (Join-Path $PSScriptRoot 'start-model.ps1') }
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2
    if ($health.version -eq '0.2.0' -and $health.mode -eq 'local_demo') {
        Write-Host "Mizan is already running at http://127.0.0.1:$Port"
        exit 0
    }
} catch { }
Write-Host "Mizan is available at http://127.0.0.1:$Port. Press Ctrl+C to stop."
& $pythonPath -m uvicorn backend.main:app --host 127.0.0.1 --port $Port
exit $LASTEXITCODE
