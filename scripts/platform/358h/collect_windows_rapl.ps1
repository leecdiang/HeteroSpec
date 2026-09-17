[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$OutputCsv,
    [Parameter(Mandatory=$true)][string]$MetadataJson,
    [int]$PeriodMs = 1000,
    [int]$MaxDurationSeconds = 3600,
    [string]$StopFile = ""
)

$ErrorActionPreference = "Stop"
if ($PeriodMs -lt 1000) { throw "Windows Get-Counter diagnostic cadence must be at least 1000 ms." }

$counterMap = [ordered]@{
    package_mw = '\Energy Meter(RAPL_Package0_PKG)\Power'
    core_mw    = '\Energy Meter(RAPL_Package0_PP0)\Power'
    graphics_mw = '\Energy Meter(RAPL_Package0_PP1)\Power'
    dram_mw    = '\Energy Meter(RAPL_Package0_DRAM)\Power'
}
$available = (Get-Counter -ListSet 'Energy Meter').PathsWithInstances
foreach ($path in $counterMap.Values) {
    if ($available -notcontains $path) { throw "Required counter missing: $path" }
}

function Get-PowerState {
    $battery = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
    $online = $null
    $charging = $null
    $discharging = $null
    if ($battery) {
        $online = [bool]($battery.BatteryStatus -in 2, 6, 7, 8, 9, 11)
        $charging = [bool]($battery.BatteryStatus -in 6, 7, 8, 9)
        $discharging = [bool]($battery.BatteryStatus -eq 1)
    }
    [ordered]@{
        utc = [DateTime]::UtcNow.ToString('o')
        power_online = $online
        charging = $charging
        discharging = $discharging
        battery_percent = if ($battery) { [int]$battery.EstimatedChargeRemaining } else { $null }
        power_scheme = ((powercfg /getactivescheme) -join ' ').Trim()
    }
}

$before = Get-PowerState
if ($before.power_online -ne $true -or $before.discharging -eq $true) {
    throw "AC gate failed: PowerOnline must be true and Discharging must be false."
}

$outDir = Split-Path -Parent $OutputCsv
if ($outDir) { New-Item -ItemType Directory -Force -Path $outDir | Out-Null }
$metaDir = Split-Path -Parent $MetadataJson
if ($metaDir) { New-Item -ItemType Directory -Force -Path $metaDir | Out-Null }

$frequency = [Diagnostics.Stopwatch]::Frequency
$deadline = [Diagnostics.Stopwatch]::GetTimestamp() + [int64]($MaxDurationSeconds * $frequency)
$rows = [Collections.Generic.List[object]]::new()
while ([Diagnostics.Stopwatch]::GetTimestamp() -lt $deadline) {
    if ($StopFile -and (Test-Path -LiteralPath $StopFile)) { break }
    $qpc = [Diagnostics.Stopwatch]::GetTimestamp()
    $sample = Get-Counter -Counter @($counterMap.Values) -MaxSamples 1
    $byPath = @{}
    foreach ($s in $sample.CounterSamples) { $byPath[$s.Path.ToLowerInvariant()] = [double]$s.CookedValue }
    $row = [ordered]@{ utc = [DateTime]::UtcNow.ToString('o'); qpc_ticks = $qpc; qpc_frequency = $frequency }
    foreach ($entry in $counterMap.GetEnumerator()) {
        $wanted = $entry.Value.ToLowerInvariant()
        $matched = $byPath.GetEnumerator() | Where-Object { $_.Key.EndsWith($wanted) } | Select-Object -First 1
        if (-not $matched) { throw "Counter sample missing: $($entry.Value)" }
        $raw = [double]$matched.Value
        $row[$entry.Key] = $raw
        $row[$entry.Key.Replace('_mw','_w')] = $raw / 1000.0
    }
    $rows.Add([pscustomobject]$row)
    if ($PeriodMs -gt 1000) { Start-Sleep -Milliseconds ($PeriodMs - 1000) }
}
$rows | Export-Csv -NoTypeInformation -Encoding UTF8 -LiteralPath $OutputCsv
$after = Get-PowerState
[ordered]@{
    schema_version = 1
    role = 'secondary diagnostic telemetry; not the primary 358H energy boundary'
    source = 'Windows Energy Meter performance counters'
    requested_period_ms = $PeriodMs
    row_count = $rows.Count
    qpc_frequency = $frequency
    conversion = 'Cooked Power values divided by 1000 and recorded as W; scale must pass qualification sanity before use.'
    overlap_rule = 'Package, core, graphics, and DRAM are overlapping/related domains and MUST NOT be summed.'
    counters = $counterMap
    before = $before
    after = $after
} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $MetadataJson

