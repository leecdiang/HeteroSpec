# Read-only trace inventory. Does not start ETW, load a model or launch inference.
param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = "Stop"
$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($id)
$isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$wpr = Get-Command wpr.exe -ErrorAction SilentlyContinue
$gpuview = Get-Command GPUView.exe -ErrorAction SilentlyContinue
$paths = @(
  "${env:ProgramFiles(x86)}\Windows Kits\10\Windows Performance Toolkit\GPUView\GPUView.exe",
  "${env:ProgramFiles(x86)}\Windows Kits\10\Windows Performance Toolkit\GPUView\Log.cmd"
)
$available = @($paths | Where-Object { Test-Path -LiteralPath $_ })
$profileText = @()
$statusText = @()
if ($wpr) {
  $profileText = @(& $wpr.Source -profiles 2>&1 | ForEach-Object { $_.ToString() })
  $profilesExit = $LASTEXITCODE
  $statusText = @(& $wpr.Source -status 2>&1 | ForEach-Object { $_.ToString() })
  $statusExit = $LASTEXITCODE
}
$result = [ordered]@{
  schema = "heterospec.b570.trace_inventory.v1"
  utc = [DateTime]::UtcNow.ToString("o")
  administrative_session = $isAdmin
  wpr_path = if ($wpr) { $wpr.Source } else { $null }
  gpuview_path = if ($gpuview) { $gpuview.Source } else { $null }
  existing_WPT_paths = $available
  wpr_profiles_raw = $profileText
  wpr_status_raw = $statusText
  wpr_profiles_exit = $profilesExit
  wpr_status_exit = $statusExit
  model_loads = 0
  model_forwards = 0
  trace_started = $false
  physical_residency = "UNKNOWN"
  next_step = if ($isAdmin -and $available.Count -gt 0) { "BOUNDED_LOAD_TRACE_IMPLEMENTATION_REQUIRED" } else { "TRACE_PERMISSION_OR_TOOL_BLOCKED" }
}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding UTF8
Write-Output ($result | ConvertTo-Json -Depth 8)

