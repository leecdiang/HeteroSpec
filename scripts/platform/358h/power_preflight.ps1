[CmdletBinding()]
param(
    [switch]$RequireAdministrator,
    [string]$OutputPath = ''
)

$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$issues = [Collections.Generic.List[string]]::new()
$battery = Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue | Select-Object -First 1
$online = if ($battery) { [bool]($battery.BatteryStatus -in 2,6,7,8,9,11) } else { $null }
$charging = if ($battery) { [bool]($battery.BatteryStatus -in 6,7,8,9) } else { $null }
$discharging = if ($battery) { [bool]($battery.BatteryStatus -eq 1) } else { $null }
if ($online -ne $true) { $issues.Add('PowerOnline is not positively true.') }
if ($discharging -eq $true) { $issues.Add('Battery reports discharging.') }

$principal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
$admin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($RequireAdministrator -and -not $admin) { $issues.Add('Administrator shell is required for Intel Unified Telemetry.') }

$ut = Join-Path $root 'tools\intel-unified-telemetry\v0.2.0-beta1.1\ut-tool-ext-v0.2.0-beta1.1\bin\ut.exe'
$utHash = if (Test-Path -LiteralPath $ut) { (Get-FileHash -Algorithm SHA256 -LiteralPath $ut).Hash.ToLowerInvariant() } else { $null }
if ($utHash -ne '47ff26a6e509ff753a7049d39aca35b4d4b78172290cbeef2c37eb26d2e7ddce') { $issues.Add('Intel Unified Telemetry executable is missing or hash-mismatched.') }

$draft = Join-Path $root 'models\gguf\Qwen3-0.6B-Q8_0.gguf'
$draftHash = if (Test-Path -LiteralPath $draft) { (Get-FileHash -Algorithm SHA256 -LiteralPath $draft).Hash.ToLowerInvariant() } else { $null }
if ($draftHash -ne '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031') { $issues.Add('Canonical draft GGUF is missing or hash-mismatched.') }

$target = Join-Path $root 'models\gguf\Qwen3-8B-Q8_0.gguf'
$targetHash = if (Test-Path -LiteralPath $target) { (Get-FileHash -Algorithm SHA256 -LiteralPath $target).Hash.ToLowerInvariant() } else { $null }
if ($targetHash -ne '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6') { $issues.Add('Frozen target GGUF is not yet present with the expected hash.') }

$result = [ordered]@{
    utc = [DateTime]::UtcNow.ToString('o')
    ready = ($issues.Count -eq 0)
    power_online = $online
    charging = $charging
    discharging = $discharging
    battery_percent = if ($battery) { [int]$battery.EstimatedChargeRemaining } else { $null }
    power_scheme = ((powercfg /getactivescheme) -join ' ').Trim()
    administrator = $admin
    unified_telemetry_sha256 = $utHash
    draft_gguf_sha256 = $draftHash
    target_gguf_sha256 = $targetHash
    issues = @($issues)
}
$json = $result | ConvertTo-Json -Depth 6
if ($OutputPath) {
    $parent = Split-Path -Parent $OutputPath
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $json | Set-Content -Encoding UTF8 -LiteralPath $OutputPath
}
$json
if ($issues.Count -gt 0) { exit 2 }

