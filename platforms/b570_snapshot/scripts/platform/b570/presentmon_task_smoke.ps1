[CmdletBinding()]
param([Parameter(Mandatory)][string]$OutputDirectory, [int]$DurationSeconds = 30)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
$collector = 'C:\hs\pm\Release\b570_presentmon_telemetry.exe'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$json = Join-Path $OutputDirectory 'status.json'; $txt = Join-Path $OutputDirectory 'status.txt'
$csv = Join-Path $OutputDirectory 'telemetry.csv'; $meta = Join-Path $OutputDirectory 'telemetry.metadata.json'
$stop = Join-Path $OutputDirectory 'telemetry.stop'; $stdout = Join-Path $OutputDirectory 'stdout.log'; $stderr = Join-Path $OutputDirectory 'stderr.log'
$status = [ordered]@{schema='heterospec.b570.presentmon-detach.v1';state='RUNNING';task_name='HeteroSpec_B570_PresentMon_SelfTest';main_pid=$PID;started_at=(Get-Date).ToString('o');heartbeat_index=0;collector_pid=$null}
try {
    if (-not (Test-Path -LiteralPath $collector)) { throw "Collector missing: $collector" }
    Remove-Item -LiteralPath $stop -Force -ErrorAction SilentlyContinue
    $p = Start-Process -FilePath $collector -ArgumentList @($csv,$meta,'3600','100',$stop) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru -WindowStyle Hidden
    $status.collector_pid = $p.Id
    $deadline = (Get-Date).AddSeconds($DurationSeconds)
    while ((Get-Date) -lt $deadline) {
        if ($p.HasExited) { throw "Collector exited early: $($p.ExitCode)" }
        $status.heartbeat_index++; Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
        Start-Sleep -Seconds 10
    }
    New-Item -ItemType File -Force -Path $stop | Out-Null
    if (-not $p.WaitForExit(15000)) { throw 'Collector did not stop within 15 seconds' }
    # Windows PowerShell can leave ExitCode unpopulated after the timed overload.
    # Refresh the process object after the handle is signalled before validating it.
    $p.WaitForExit(); $p.Refresh(); $collectorExitCode = $p.ExitCode
    if ($null -ne $collectorExitCode -and $collectorExitCode -ne 0) { throw "Collector exit code $collectorExitCode" }
    $rows = @((Get-Content -LiteralPath $csv | Select-Object -Skip 1)).Count
    if ($rows -lt 100) { throw "Too few telemetry rows: $rows" }
    $metadata = Get-Content -LiteralPath $meta -Raw | ConvertFrom-Json
    $status.state='PASS'; $status.collector_exit_code=$collectorExitCode; $status.collector_exit_code_available=($null -ne $collectorExitCode); $status.csv_rows=$rows; $status.metadata_present=$true; $status.completed_at=(Get-Date).ToString('o')
    Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
    Write-AtomicText -Path (Join-Path $OutputDirectory 'PASS.marker') -Text ($status.completed_at + "`n")
    exit 0
} catch {
    if ($p -and -not $p.HasExited) { New-Item -ItemType File -Force -Path $stop | Out-Null; $p.WaitForExit(5000) | Out-Null }
    $status.state='FAIL'; $status.error=($_ | Out-String)
    Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
    exit 1
}
