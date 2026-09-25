$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
New-Item -ItemType Directory -Path 'work' -Force | Out-Null
$testTemp = Join-Path 'work' ('pytest-' + [guid]::NewGuid().ToString('N'))
& '.\.venv\Scripts\python.exe' -m pytest -q --basetemp=$testTemp
exit $LASTEXITCODE
