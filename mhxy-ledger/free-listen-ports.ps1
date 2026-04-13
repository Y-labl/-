# Release TCP listen ports before starting mhxy-ledger (Windows).
# ASCII-only. Run via: powershell -ExecutionPolicy Bypass -File free-listen-ports.ps1 [3001] [5173] ...
param(
  [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
  [int[]] $Ports = @(3001, 5173)
)

$hadError = $false
$uniquePorts = $Ports | Select-Object -Unique

foreach ($port in $uniquePorts) {
  $conns = @(Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
  if ($conns.Count -eq 0) { continue }

  foreach ($procId in ($conns.OwningProcess | Select-Object -Unique)) {
    Write-Host "[mhxy-ledger] Port $port listen PID $procId -> Stop-Process -Force"
    try {
      Stop-Process -Id $procId -Force -ErrorAction Stop
    } catch {
      Write-Host "[mhxy-ledger] Failed to stop PID ${procId}: $($_.Exception.Message)"
      $hadError = $true
    }
  }
}

if ($hadError) { exit 1 }
exit 0
