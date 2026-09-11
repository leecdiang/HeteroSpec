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
    [int] $PostIdleSeconds = 30
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

function Write-RunEvent([string] $Message) {
    $line = "{0} {1}" -f (Get-Date).ToString("o"), $Message
    Add-Content -LiteralPath $eventsPath -Value $line -Encoding utf8
}

$manifest = [ordered]@{
    schema_version    = 1
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
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestPath -Encoding utf8
Write-RunEvent "STAGED: disconnect ToDesk before the delay and pre-idle intervals finish."

if ($DelaySeconds -gt 0) {
    Start-Sleep -Seconds $DelaySeconds
}
Write-RunEvent "DELAY_COMPLETE"
if ($PreIdleSeconds -gt 0) {
    Start-Sleep -Seconds $PreIdleSeconds
}

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
try {
    Write-RunEvent "STARTING"
    if (-not $process.Start()) {
        throw "Process failed to start."
    }
    "{0} pid={1}" -f (Get-Date).ToString("o"), $process.Id | Set-Content -LiteralPath (Join-Path $runDirectory "started.marker") -Encoding utf8
    $stdoutCopy = $process.StandardOutput.BaseStream.CopyToAsync($stdoutStream)
    $stderrCopy = $process.StandardError.BaseStream.CopyToAsync($stderrStream)
    $process.WaitForExit()
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

if ($PostIdleSeconds -gt 0) {
    Start-Sleep -Seconds $PostIdleSeconds
}

$finishedAt = Get-Date
$result = [ordered]@{
    exit_code   = $exitCode
    finished_at = $finishedAt.ToString("o")
    duration_s  = [Math]::Round(($finishedAt - $startedAt).TotalSeconds, 3)
    stdout      = $stdoutPath
    stderr      = $stderrPath
}
$markerName = if ($exitCode -eq 0) { "completed.marker" } else { "failed.marker" }
$result | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runDirectory $markerName) -Encoding utf8
Write-RunEvent "FINALIZED marker=$markerName"
exit $exitCode
