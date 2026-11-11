[CmdletBinding()]
param([Parameter(Mandatory = $true)][string] $StageOutput)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$sessionLog = Join-Path $StageOutput "remote-session.log"
New-Item -ItemType Directory -Force -Path $StageOutput | Out-Null
function Log([string] $Message) { Add-Content -LiteralPath $sessionLog -Value ("{0} {1}" -f (Get-Date).ToString("o"), $Message) -Encoding utf8 }

Log "Launcher active; disconnect the current ToDesk session now."
Log "Waiting 120 seconds before the required 60-second disconnected idle settling interval."
Start-Sleep -Seconds 120
Log "Starting required 60-second disconnected idle settling interval."
Start-Sleep -Seconds 60

$outerRoot = Join-Path $StageOutput "unattended"
& (Join-Path $PSScriptRoot "run_unattended.ps1") -Command "$PSHOME\pwsh.exe" -CommandArgs @(
    "-NoProfile", "-File", (Join-Path $PSScriptRoot "run_b570_formal_stage.ps1"), "-OutputDirectory", $StageOutput
) -OutputRoot $outerRoot -RunName "b570-correctness-verification" -DelaySeconds 0 -PreIdleSeconds 0 -PostIdleSeconds 30
$exitCode = $LASTEXITCODE
Log "Formal stage finished with exit code $exitCode."

Log "Remote reconnection may now occur."
exit $exitCode
