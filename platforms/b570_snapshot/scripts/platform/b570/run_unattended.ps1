[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string] $Command,

    [string[]] $CommandArgs = @(),

    [Parameter(Mandatory = $true)]
    [string] $OutputRoot,

    [string] $RunName = "b570-run",

    [ValidateRange(0, 86400)]
    [int] $DelaySeconds = 60,

    [ValidateRange(0, 3600)]
    [int] $PreIdleSeconds = 60,

    [ValidateRange(0, 3600)]
    [int] $PostIdleSeconds = 30,

    [string] $TelemetryCommand = "",

    [ValidateRange(50, 5000)]
    [int] $TelemetryPeriodMs = 100,

    [ValidateRange(60, 86400)]
    [int] $TelemetryMaxDurationSeconds = 86400
)

$ErrorActionPreference = "Stop"
$startedAt = Get-Date
$stamp = $startedAt.ToString("yyyyMMdd-HHmmss")
$safeName = $RunName -replace '[^A-Za-z0-9._-]', '_'
$runDirectory = Join-Path ([IO.Path]::GetFullPath($OutputRoot)) "$stamp-$safeName"

if (-not (Test-Path -LiteralPath $Command -PathType Leaf)) {
    throw "Command does not exist: $Command"
}
if (Test-Path -LiteralPath $runDirectory) {
    throw "Refusing to overwrite existing run directory: $runDirectory"
}

New-Item -ItemType Directory -Path $runDirectory | Out-Null
$stdoutPath = Join-Path $runDirectory "stdout.log"
$stderrPath = Join-Path $runDirectory "stderr.log"
$eventsPath = Join-Path $runDirectory "events.log"
$manifestPath = Join-Path $runDirectory "manifest.json"
$windowPath = Join-Path $runDirectory "workload-window.json"
$telemetryCsvPath = Join-Path $runDirectory "telemetry.csv"
$telemetryMetadataPath = Join-Path $runDirectory "telemetry.metadata.json"
$telemetryStopPath = Join-Path $runDirectory "telemetry.stop"
$telemetryStdoutPath = Join-Path $runDirectory "telemetry.stdout.log"
$telemetryStderrPath = Join-Path $runDirectory "telemetry.stderr.log"

function Write-RunEvent([string] $Message) {
    $line = "{0} {1}" -f (Get-Date).ToString("o"), $Message
    Add-Content -LiteralPath $eventsPath -Value $line -Encoding utf8
}

$manifest = [ordered]@{
    schema_version    = 2
    run_name          = $RunName
    run_directory     = $runDirectory
    launcher_pid      = $PID
    host              = $env:COMPUTERNAME
    command           = [IO.Path]::GetFullPath($Command)
    arguments         = $CommandArgs
    created_at        = $startedAt.ToString("o")
    delay_seconds     = $DelaySeconds
    pre_idle_seconds  = $PreIdleSeconds
    post_idle_seconds = $PostIdleSeconds
    qpc_frequency_hz  = [Diagnostics.Stopwatch]::Frequency
    telemetry         = if ($TelemetryCommand) { [ordered]@{
        command = [IO.Path]::GetFullPath($TelemetryCommand)
        period_ms = $TelemetryPeriodMs
        max_duration_seconds = $TelemetryMaxDurationSeconds
        csv = $telemetryCsvPath
        metadata = $telemetryMetadataPath
    } } else { $null }
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-RunEvent "STAGED: disconnect ToDesk before the delay and pre-idle intervals finish."

if ($DelaySeconds -gt 0) {
    Start-Sleep -Seconds $DelaySeconds
}
Write-RunEvent "DELAY_COMPLETE"

$telemetryProcess = $null
$telemetryStdoutStream = $null
$telemetryStderrStream = $null
$telemetryStartedAt = $null
$telemetryStartQpc = $null
if ($TelemetryCommand) {
    if (-not (Test-Path -LiteralPath $TelemetryCommand -PathType Leaf)) {
        throw "Telemetry command does not exist: $TelemetryCommand"
    }
    $telemetryInfo = [Diagnostics.ProcessStartInfo]::new()
    $telemetryInfo.FileName = [IO.Path]::GetFullPath($TelemetryCommand)
    $telemetryInfo.UseShellExecute = $false
    $telemetryInfo.CreateNoWindow = $true
    $telemetryInfo.RedirectStandardOutput = $true
    $telemetryInfo.RedirectStandardError = $true
    foreach ($argument in @($telemetryCsvPath, $telemetryMetadataPath, "$TelemetryMaxDurationSeconds", "$TelemetryPeriodMs", $telemetryStopPath)) {
        [void] $telemetryInfo.ArgumentList.Add($argument)
    }
    $telemetryStdoutStream = [IO.FileStream]::new($telemetryStdoutPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $telemetryStderrStream = [IO.FileStream]::new($telemetryStderrPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
    $telemetryProcess = [Diagnostics.Process]::new()
    $telemetryProcess.StartInfo = $telemetryInfo
    $telemetryStartedAt = Get-Date
    $telemetryStartQpc = [Diagnostics.Stopwatch]::GetTimestamp()
    if (-not $telemetryProcess.Start()) { throw "Telemetry process failed to start." }
    $telemetryStdoutCopy = $telemetryProcess.StandardOutput.BaseStream.CopyToAsync($telemetryStdoutStream)
    $telemetryStderrCopy = $telemetryProcess.StandardError.BaseStream.CopyToAsync($telemetryStderrStream)
    Write-RunEvent "TELEMETRY_START pid=$($telemetryProcess.Id) qpc=$telemetryStartQpc"
}

if ($PreIdleSeconds -gt 0) { Start-Sleep -Seconds $PreIdleSeconds }

$processInfo = [Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = [IO.Path]::GetFullPath($Command)
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
foreach ($argument in $CommandArgs) {
    [void] $processInfo.ArgumentList.Add($argument)
}

$stdoutStream = [IO.FileStream]::new($stdoutPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$stderrStream = [IO.FileStream]::new($stderrPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::Read)
$process = [Diagnostics.Process]::new()
$process.StartInfo = $processInfo

$exitCode = 255
$workloadStartedAt = $null
$workloadFinishedAt = $null
$workloadStartQpc = $null
$workloadEndQpc = $null
try {
    Write-RunEvent "STARTING"
    if (-not $process.Start()) {
        throw "Process failed to start."
    }
    $workloadStartQpc = [Diagnostics.Stopwatch]::GetTimestamp()
    $workloadStartedAt = Get-Date
    "{0} pid={1} qpc={2}" -f $workloadStartedAt.ToString("o"), $process.Id, $workloadStartQpc | Set-Content -LiteralPath (Join-Path $runDirectory "started.marker") -Encoding utf8
    $stdoutCopy = $process.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
    $stderrCopy = $process.StandardError.BaseStream.CopyToAsync($stderrStream)
    $process.WaitForExit()
    $workloadEndQpc = [Diagnostics.Stopwatch]::GetTimestamp()
    $workloadFinishedAt = Get-Date
    [void] $stdoutCopy.GetAwaiter().GetResult()
    [void] $stderrCopy.GetAwaiter().GetResult()
    $exitCode = $process.ExitCode
    Write-RunEvent "EXIT code=$exitCode"
}
catch {
    $_ | Out-String | Add-Content -LiteralPath $stderrPath -Encoding utf8
    Write-RunEvent "LAUNCHER_FAILURE"
}
finally {
    $stdoutStream.Dispose()
    $stderrStream.Dispose()
    $process.Dispose()
}

if ($PostIdleSeconds -gt 0) { Start-Sleep -Seconds $PostIdleSeconds }

$telemetryExitCode = $null
$telemetryFinishedAt = $null
$telemetryEndQpc = $null
if ($telemetryProcess) {
    New-Item -ItemType File -Path $telemetryStopPath | Out-Null
    if (-not $telemetryProcess.WaitForExit(15000)) {
        $telemetryProcess.Kill($true)
        Write-RunEvent "TELEMETRY_FORCED_STOP"
    }
    [void] $telemetryStdoutCopy.GetAwaiter().GetResult()
    [void] $telemetryStderrCopy.GetAwaiter().GetResult()
    $telemetryExitCode = $telemetryProcess.ExitCode
    $telemetryEndQpc = [Diagnostics.Stopwatch]::GetTimestamp()
    $telemetryFinishedAt = Get-Date
    Write-RunEvent "TELEMETRY_EXIT code=$telemetryExitCode qpc=$telemetryEndQpc"
    $telemetryStdoutStream.Dispose()
    $telemetryStderrStream.Dispose()
    $telemetryProcess.Dispose()
}

$window = [ordered]@{
    run_id = Split-Path -Leaf $runDirectory
    qpc_frequency_hz = [Diagnostics.Stopwatch]::Frequency
    workload_start_utc = if ($workloadStartedAt) { $workloadStartedAt.ToString("o") } else { $null }
    workload_end_utc = if ($workloadFinishedAt) { $workloadFinishedAt.ToString("o") } else { $null }
    workload_start_qpc = $workloadStartQpc
    workload_end_qpc = $workloadEndQpc
    workload_exit_code = $exitCode
    telemetry_start_utc = if ($telemetryStartedAt) { $telemetryStartedAt.ToString("o") } else { $null }
    telemetry_end_utc = if ($telemetryFinishedAt) { $telemetryFinishedAt.ToString("o") } else { $null }
    telemetry_start_qpc = $telemetryStartQpc
    telemetry_end_qpc = $telemetryEndQpc
    telemetry_exit_code = $telemetryExitCode
    telemetry_file = if ($TelemetryCommand) { $telemetryCsvPath } else { $null }
}
$window | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $windowPath -Encoding utf8

$finishedAt = Get-Date
$result = [ordered]@{
    exit_code   = $exitCode
    finished_at = $finishedAt.ToString("o")
    duration_s  = [Math]::Round(($finishedAt - $startedAt).TotalSeconds, 3)
    stdout      = $stdoutPath
    stderr      = $stderrPath
    workload_window = $windowPath
    telemetry_exit_code = $telemetryExitCode
    telemetry = if ($TelemetryCommand) { $telemetryCsvPath } else { $null }
}
$markerName = if ($exitCode -eq 0) { "completed.marker" } else { "failed.marker" }
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory $markerName) -Encoding utf8
Write-RunEvent "FINALIZED marker=$markerName"
exit $exitCode
