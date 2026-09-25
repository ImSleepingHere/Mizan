# Restart the local model server (picks up the coordinator adapter in .models\ if present).
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Get-Process llama-server -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$projectRoot*" } | Stop-Process -Force
Start-Sleep 3
& (Join-Path $PSScriptRoot 'start-model.ps1')
$began = Get-Date
while (((Get-Date) - $began).TotalSeconds -lt 240) {
    try { if ((Invoke-RestMethod 'http://127.0.0.1:11435/health' -TimeoutSec 3).status -eq 'ok') { Write-Host 'Model server ready.'; return } } catch {}
    Start-Sleep 3
}
throw 'Model server did not become ready within 4 minutes. See work\model.stderr.log'
