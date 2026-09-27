param([int]$Port = 8000, [string]$Database = '')
# Puts the local demo database back to its freshly seeded state (four scenarios, no proposals, empty audit trail).
# The current database is kept as a timestamped backup in data\backups; nothing is deleted outright.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Run scripts/setup.ps1 first to create the project environment.' }
Set-Location -LiteralPath $projectRoot

$running = $false
try { Invoke-RestMethod -Uri "http://127.0.0.1:$Port/api/health" -TimeoutSec 2 | Out-Null; $running = $true } catch { }
if ($running) { throw "Mizan is still running on port $Port. Stop it (Ctrl+C in its window) and run the reset again." }

if ($Database) { $database = [System.IO.Path]::GetFullPath($Database) } else { $database = Join-Path $projectRoot 'data\mizan.sqlite3' }
$data = Split-Path -Parent $database
New-Item -ItemType Directory -Force -Path $data | Out-Null
$env:MIZAN_DB = $database
if (Test-Path -LiteralPath $database) {
    $backups = Join-Path $data 'backups'
    New-Item -ItemType Directory -Force -Path $backups | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    foreach ($suffix in '', '-wal', '-shm') {
        $file = "$database$suffix"
        if (Test-Path -LiteralPath $file) { Move-Item -LiteralPath $file -Destination (Join-Path $backups "mizan-$stamp.sqlite3$suffix") }
    }
    Write-Host "Previous database saved to $backups\mizan-$stamp.sqlite3"
}

& $pythonPath -c "import backend.main; from backend.store import init_db; from backend.agent_engine import init_agents; from backend.recruitment import init_recruitment; init_db(); init_agents(); init_recruitment(); print('Fresh demo database created: baseline, diagnostic, shortfall and faculty scenarios.')"
if ($LASTEXITCODE -ne 0) { throw 'Seeding the demo database failed.' }
