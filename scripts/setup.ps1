param([string]$Python = '', [string]$Pnpm = '')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not $Python) {
    if (Get-Command 'py' -ErrorAction SilentlyContinue) {
        $Python = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null
        if ($LASTEXITCODE -ne 0) { $Python = '' }
    }
    if (-not $Python) { $Python = 'python' }
}
$pythonVersion = & $Python -c 'import sys; print(str(sys.version_info.major)+chr(46)+str(sys.version_info.minor))'
if ($LASTEXITCODE -ne 0 -or $pythonVersion -ne '3.12') { throw 'Use Python 3.12 for this tested release. Install it or pass -Python with its executable path.' }
Write-Host "Using Python $pythonVersion at $Python"
& $Python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Creating the Python 3.12 environment failed.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
# pnpm does not need to be installed globally: fall back to the copy npx fetches (Node.js 24+ includes npx).
$env:CI = 'true'
$pnpmCommand = @($Pnpm)
if (-not $Pnpm) {
    if (-not (Get-Command 'npx.cmd' -ErrorAction SilentlyContinue)) { throw 'Node.js 24+ is required (it provides npx). Install it from nodejs.org and run setup again.' }
    $pnpmCommand = @('npx.cmd', '--yes', 'pnpm@12.9.1')
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
Write-Host 'Setup complete. Timetable features are ready. For optional AI features, download the local model (docs/HANDOVER.md). Run Check Mizan Setup.cmd, then Start Mizan.cmd.'
