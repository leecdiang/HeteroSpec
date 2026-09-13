[CmdletBinding()]
param([Parameter(Mandatory)][string]$OutputDirectory, [int]$DurationSeconds = 120)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$json = Join-Path $OutputDirectory 'status.json'
$txt = Join-Path $OutputDirectory 'status.txt'
$status = [ordered]@{
    schema = 'heterospec.b570.scheduler-selftest.v1'
    state = 'RUNNING'
    task_name = 'HeteroSpec_B570_SelfTest'
    main_pid = $PID
    parent_pid = (Get-CimInstance Win32_Process -Filter "ProcessId=$PID").ParentProcessId
    started_at = (Get-Date).ToString('o')
    heartbeat_index = 0
}
try {
    $deadline = (Get-Date).AddSeconds($DurationSeconds)
    while ((Get-Date) -lt $deadline) {
        $status.heartbeat_index++
        $status.elapsed_seconds = [Math]::Round(((Get-Date) - [datetime]$status.started_at).TotalSeconds, 1)
        Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
        Start-Sleep -Seconds 10
    }
    $status.state = 'PASS'
    $status.completed_at = (Get-Date).ToString('o')
    Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
    Write-AtomicText -Path (Join-Path $OutputDirectory 'PASS.marker') -Text ($status.completed_at + "`n")
    exit 0
} catch {
    $status.state = 'FAIL'; $status.error = ($_ | Out-String)
    Write-TaskStatus -JsonPath $json -TextPath $txt -Status $status
    exit 1
}
