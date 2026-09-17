[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$ApplicationCommand,
    [Parameter(Mandatory=$true)][string]$OutputPrefix,
    [ValidateSet('socwatch','socwatch,itt','socwatch,level-zero,xpu-os','socwatch,level-zero,xpu-os,itt')][string]$Collectors = 'socwatch,level-zero,xpu-os',
    [switch]$SkipConversion
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$utRoot = Join-Path $root 'tools\intel-unified-telemetry\v0.2.0-beta1.1\ut-tool-ext-v0.2.0-beta1.1'
$ut = Join-Path $utRoot 'bin\ut.exe'
$converter = Join-Path $utRoot 'bin\bin2perfetto.exe'
$vars = Join-Path $utRoot 'ut-vars.ps1'
$pwrConfig = Join-Path $root 'configs\platform\358h\ut-pwr-100ms.json'
$expectedUtHash = '47ff26a6e509ff753a7049d39aca35b4d4b78172290cbeef2c37eb26d2e7ddce'
$expectedZipHash = 'f78151fffa89a05b7551da3cbfaf53fcc22d6fffdb97605af00706d6393b6da1'

$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Intel Unified Telemetry qualification must run from an Administrator PowerShell. No trace was collected.'
}
foreach ($path in @($ut, $converter, $vars, $pwrConfig)) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Required Unified Telemetry file missing: $path" }
}
$actualUtHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ut).Hash.ToLowerInvariant()
if ($actualUtHash -ne $expectedUtHash) { throw "ut.exe hash mismatch: $actualUtHash" }

$battery = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$online = if ($battery) { [bool]($battery.BatteryStatus -in 2,6,7,8,9,11) } else { $null }
$discharging = if ($battery) { [bool]($battery.BatteryStatus -eq 1) } else { $null }
if ($online -ne $true -or $discharging -eq $true) { throw 'AC gate failed before telemetry collection.' }

$prefixDir = Split-Path -Parent $OutputPrefix
if ($prefixDir) { New-Item -ItemType Directory -Force -Path $prefixDir | Out-Null }
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
. $vars

$startedUtc = [DateTime]::UtcNow.ToString('o')
& $ut --output $OutputPrefix --config-level low --pwr-config $pwrConfig --enable $Collectors --app $ApplicationCommand
if ($LASTEXITCODE -ne 0) { throw "Unified Telemetry failed with exit code $LASTEXITCODE" }
$endedUtc = [DateTime]::UtcNow.ToString('o')

$bins = @(Get-ChildItem -LiteralPath $prefixDir -Filter ((Split-Path -Leaf $OutputPrefix) + '*.bin') -File)
if (-not ($bins.Name -match '\.socwatch\.bin$')) { throw 'Required socwatch power trace was not produced.' }
if ($Collectors -match 'level-zero' -and -not ($bins.Name -match '\.l0_npu\.bin$')) {
    throw 'Requested NPU metric trace was not produced; qualification fails closed.'
}
if (-not $SkipConversion) {
    & $converter --input ($OutputPrefix + '*') --output $OutputPrefix --format json
    if ($LASTEXITCODE -ne 0) { throw "bin2perfetto failed with exit code $LASTEXITCODE" }
}

$artifacts = @()
Get-ChildItem -LiteralPath $prefixDir -Filter ((Split-Path -Leaf $OutputPrefix) + '*') -File | Where-Object { $_.FullName -ne ($OutputPrefix + '.manifest.json') } | ForEach-Object {
    $artifacts += [ordered]@{ path=$_.FullName; bytes=$_.Length; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant() }
}
$manifest = [ordered]@{
    schema_version = 1
    role = 'qualification telemetry; never formal performance data'
    tool = 'Intel Unified Telemetry'
    version = (& $ut --version | Out-String).Trim()
    ut_exe_sha256 = $actualUtHash
    distribution_zip_sha256 = $expectedZipHash
    config_level = 'low'
    collectors = $Collectors
    sampling_policy = 'Frozen official-format custom power config sets samplingInterval=100 ms, reusing the B570 cadence; UT only permits CLI --sampling-interval in continuous mode.'
    power_config = [ordered]@{ path=$pwrConfig; sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $pwrConfig).Hash.ToLowerInvariant() }
    level_zero_config = [ordered]@{ path=(Join-Path $utRoot 'bin\configs\ze-low.json'); sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $utRoot 'bin\configs\ze-low.json')).Hash.ToLowerInvariant() }
    application_command = $ApplicationCommand
    conversion_skipped = [bool]$SkipConversion
    started_utc = $startedUtc
    ended_utc = $endedUtc
    power_online = $online
    discharging = $discharging
    power_scheme = ((powercfg /getactivescheme) -join ' ').Trim()
    artifacts = $artifacts
    overlap_rule = 'Report Package and NPU domains separately; never add overlapping domains.'
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath ($OutputPrefix + '.manifest.json')

