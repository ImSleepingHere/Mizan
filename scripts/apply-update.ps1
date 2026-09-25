# Applies the coordinator + interface update: restart model server with the adapter, measure the
# deployed coordinator, then restart the Mizan app so the new backend and interface load.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$log = Join-Path $projectRoot 'work\update.log'
$py = Join-Path $projectRoot '.venv\Scripts\python.exe'
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTHONUNBUFFERED = '1'
function Step($m) { Write-Host "`n=== $m ===" -ForegroundColor Cyan; Add-Content $log "`n=== $(Get-Date -Format s) $m ===" }
trap { Add-Content $log ("ERROR: " + ($_ | Out-String)); Write-Host $_ -ForegroundColor Red; break }
Set-Location $projectRoot

Step 'Restarting model server with the fine-tuned coordinator'
& (Join-Path $PSScriptRoot 'restart-model.ps1') *>&1 | Tee-Object -FilePath $log -Append
$adapters = Invoke-RestMethod 'http://127.0.0.1:11435/lora-adapters' -TimeoutSec 5
Add-Content $log ("adapters: " + ($adapters | ConvertTo-Json -Compress))

Step 'Measuring the deployed coordinator (120 test cases, before vs after)'
$ErrorActionPreference = 'Continue'
& $py -u (Join-Path $projectRoot 'training\coordinator\deployed_eval.py') 2> (Join-Path $projectRoot 'work\deployed_eval.stderr.log') | Tee-Object -FilePath $log -Append
$evalCode = $LASTEXITCODE
$ErrorActionPreference = 'Stop'
if ($evalCode -ne 0) { Add-Content $log "deployed_eval exit code $evalCode (see work\deployed_eval.stderr.log)" }

Step 'Restarting the Mizan app'
Get-CimInstance Win32_Process -Filter "name='python.exe'" | Where-Object { $_.CommandLine -like '*backend.main:app*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
Start-Sleep 2
Start-Process powershell.exe -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + (Join-Path $PSScriptRoot 'start.ps1') + '"')) -WorkingDirectory $projectRoot
$began = Get-Date
while (((Get-Date) - $began).TotalSeconds -lt 90) {
    try { if ((Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3).status -eq 'ok') { Add-Content $log 'app: ready'; break } } catch {}
    Start-Sleep 2
}
Step 'Update applied'
Write-Host "`nDone. Open http://127.0.0.1:8000" -ForegroundColor Green
