param([Parameter(Mandatory=$true)][string]$CasePath)
$ErrorActionPreference='Stop'
$herePath=Split-Path -Parent $MyInvocation.MyCommand.Path
$config=Get-Content -LiteralPath $CasePath -Raw -Encoding UTF8 | ConvertFrom-Json
if(-not ([IO.Path]::GetFullPath($config.root)).StartsWith(([IO.Path]::GetFullPath($config.cpu8_legacy_root)+'\runs\'),[StringComparison]::OrdinalIgnoreCase)){throw 'New task root required'}
$begin=[long]([decimal][Diagnostics.Stopwatch]::GetTimestamp()*1000000000/[Diagnostics.Stopwatch]::Frequency)
Add-Type -Path ([IO.Path]::GetFullPath($config.cpu8_compiled_dll))
$capture=[B570Capture]::new()
$python='C:/Users/DIANG/AppData/Local/Programs/Python/Python312/python.exe'
$arguments='-B "'+(Join-Path $herePath 'controller.py')+'" "'+$CasePath+'"'
$code=$capture.Run($python,$arguments,$config.launcher_log_dir,[string[]]$config.protected_roots,[int]$config.launcher_seconds,1048576,$begin)
exit $code
