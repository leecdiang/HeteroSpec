param([string]$AuthorApprovedF0Sha,[string]$CpuCasePath)
$launcherBeginTicks=[Diagnostics.Stopwatch]::GetTimestamp()
$ErrorActionPreference='Stop'
$herePath=Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonPath='C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe'
$dllPath=Join-Path $herePath 'LauncherCapture.dll'
if($CpuCasePath){
    if($AuthorApprovedF0Sha){throw 'CPU test and production authorization cannot mix'}
    $caseConfig=Get-Content -LiteralPath $CpuCasePath -Raw | ConvertFrom-Json
    if($caseConfig.purpose -ne 'CPU_LAUNCH_TEST'){throw 'Explicit CPU-only case required'}
    $externalPath=$caseConfig.external_log_root
    $protectedPaths=[string[]]$caseConfig.protected_roots
    $controllerArgs='"'+(Join-Path $herePath 'cpu_controller.py')+'" "'+$CpuCasePath+'"'
    $seconds=[int]$caseConfig.launcher_seconds
    $soft=[long]$caseConfig.log_soft_bytes
}else{
    $f0Path=Join-Path $herePath 'F0.json'
    if((Get-FileHash -Algorithm SHA256 -LiteralPath $f0Path).Hash.ToLowerInvariant() -ne $AuthorApprovedF0Sha){throw 'Exact approved F0 required'}
    $f0=Get-Content -LiteralPath $f0Path -Raw | ConvertFrom-Json
    if([Security.Principal.WindowsIdentity]::GetCurrent().User.Value -ne $f0.launcher.owner_sid){throw 'Launcher ownership SID drift'}
    $externalPath=$f0.launcher.external_log_root
    $protectedPaths=[string[]]$f0.launcher.protected_roots
    $seconds=900;$soft=1048576
    if(Test-Path -LiteralPath $f0.launcher.run_root){throw 'Run root already used; no resume'}
    foreach($row in $f0.bound_files){if((Get-FileHash -Algorithm SHA256 -LiteralPath $row.path).Hash.ToLowerInvariant() -ne $row.sha256){throw ('Frozen file drift '+$row.path)}}
    $controllerArgs='"'+(Join-Path $herePath 'controller_entry.py')+'" --author-approved-f0-sha '+$AuthorApprovedF0Sha
}
$externalParent=[IO.DirectoryInfo]::new([IO.Path]::GetDirectoryName($externalPath))
while($null -ne $externalParent){
    if($externalParent.Exists -and (($externalParent.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)){throw 'External log ancestor is a reparse path'}
    $externalParent=$externalParent.Parent
}
Add-Type -Path $dllPath
$capture=[B570Capture]::new()
$launcherBeginNs=[long]([decimal]$launcherBeginTicks*1000000000/[Diagnostics.Stopwatch]::Frequency)
$result=$capture.Run($pythonPath,$controllerArgs,$externalPath,$protectedPaths,$seconds,$soft,$launcherBeginNs)
if($CpuCasePath){
    & $pythonPath (Join-Path $herePath 'external_audit.py') --cpu-case $CpuCasePath --launcher-begin-ns $launcherBeginNs
}else{
    & $pythonPath (Join-Path $herePath 'external_audit.py') --approved-f0-sha $AuthorApprovedF0Sha --launcher-begin-ns $launcherBeginNs
}
if($LASTEXITCODE -ne 0){exit 91}
exit $result
