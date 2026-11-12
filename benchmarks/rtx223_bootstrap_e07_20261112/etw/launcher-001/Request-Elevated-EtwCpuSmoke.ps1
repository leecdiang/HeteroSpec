# Invoke only after explicit user approval for one elevated CPU-only ETW test.
$ErrorActionPreference = 'Stop'
$task = Join-Path $PSScriptRoot 'Elevated-EtwCpuSmoke.ps1'
$hostProgram = (Get-Process -Id $PID).Path
$args = '-NoProfile -NonInteractive -File "' + $task + '"'
$process = Start-Process -FilePath $hostProgram -Verb RunAs -WindowStyle Hidden -ArgumentList $args -PassThru -Wait
exit $process.ExitCode
