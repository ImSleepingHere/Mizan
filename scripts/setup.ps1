param([string]$Python = 'python', [string]$Pnpm = 'pnpm')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& $Python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
# pnpm does not need to be installed globally: fall back to the copy npx fetches (Node.js 24+ includes npx).
$env:CI = 'true'
$pnpmCommand = @($Pnpm)
if (-not (Get-Command $Pnpm -ErrorAction SilentlyContinue)) {
    if (-not (Get-Command 'npx.cmd' -ErrorAction SilentlyContinue)) { throw 'Node.js 24+ is required (it provides npx). Install it from nodejs.org and run setup again.' }
    $pnpmCommand = @('npx.cmd', '--yes', 'pnpm')
}
$pnpmExe = $pnpmCommand[0]
$pnpmPrefix = @($pnpmCommand | Select-Object -Skip 1)
Push-Location frontend
try {
    & $pnpmExe @pnpmPrefix install --frozen-lockfile
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed. Use Node 24+.' }
    & $pnpmExe @pnpmPrefix run build
    if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
} finally { Pop-Location }
Write-Host 'Setup complete. Next: download the local model (see docs/HANDOVER.md), then run Check Mizan Setup.cmd.'
