param([Parameter(Mandatory=$true)][string]$CasePath)
$ErrorActionPreference='Stop'
$launcherBegin=[Diagnostics.Stopwatch]::GetTimestamp()
$herePath=Split-Path -Parent $MyInvocation.MyCommand.Path
$caseConfig=Get-Content -LiteralPath $CasePath -Raw | ConvertFrom-Json
if($caseConfig.purpose -ne 'CPU_INTEGRATION' -and $caseConfig.purpose -ne 'FROZEN_SCIENCE'){throw 'Registered purpose required'}
if($caseConfig.purpose -eq 'FROZEN_SCIENCE'){
    $f0=Get-Content -LiteralPath $caseConfig.stage_f0 -Raw | ConvertFrom-Json
    if((Get-FileHash -LiteralPath $caseConfig.stage_f0 -Algorithm SHA256).Hash.ToLowerInvariant() -ne $caseConfig.F0_sha256){throw 'Frozen stage F0 mismatch'}
    foreach($row in $f0.bound_files){if((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256){throw ('Frozen binding drift '+$row.path)}}
}
Add-Type -Path (Join-Path $herePath 'LauncherCapture.dll')
$capture=[B570Capture]::new()
$beginNs=[long]([decimal]$launcherBegin*1000000000/[Diagnostics.Stopwatch]::Frequency)
$pythonPath='C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe'
$arguments='-B "'+(Join-Path $herePath 'controller.py')+'" "'+$CasePath+'"'
$code=$capture.Run($pythonPath,$arguments,$caseConfig.launcher_log_dir,[string[]]$caseConfig.protected_roots,[int]$caseConfig.launcher_seconds,1048576,$beginNs)
exit $code
