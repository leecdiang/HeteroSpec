param(
    [Parameter(Mandatory=$true)][string]$RepoRoot,
    [Parameter(Mandatory=$true)][string]$R0Root,
    [Parameter(Mandatory=$true)][string]$FormalRoot,
    [Parameter(Mandatory=$true)][string]$PythonPath
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $RepoRoot
$controlRoot = Join-Path (Split-Path -Parent $FormalRoot) ((Split-Path -Leaf $FormalRoot) + '-controller')
if (Test-Path -LiteralPath $FormalRoot) { throw 'Formal root already exists; no overwrite or resume.' }
New-Item -ItemType Directory -Path $controlRoot -ErrorAction Stop | Out-Null
$statePath = Join-Path $controlRoot 'status.json'
function Write-ControlState([string]$State, [int]$ExitCode) {
    [ordered]@{state=$State; updated_at=(Get-Date).ToUniversalTime().ToString('o'); exit_code=$ExitCode; formal_root=$FormalRoot} |
        ConvertTo-Json | Set-Content -LiteralPath $statePath -Encoding UTF8
}
try {
    Write-ControlState 'RUNNING_FORMAL' -1
    & $PythonPath -u scripts/platform/b570_direct_id_v1/study.py run --root $FormalRoot 1> (Join-Path $controlRoot 'formal.stdout.txt') 2> (Join-Path $controlRoot 'formal.stderr.txt')
    if ($LASTEXITCODE -ne 0) { throw "Formal runner exited $LASTEXITCODE; retained without rerun." }
    Write-ControlState 'VALIDATING_AND_ARCHIVING' -1
    & $PythonPath -u scripts/platform/b570_direct_id_v1/archive.py --root $FormalRoot --r0 $R0Root 1> (Join-Path $controlRoot 'archive.stdout.txt') 2> (Join-Path $controlRoot 'archive.stderr.txt')
    if ($LASTEXITCODE -ne 0) { throw "Archive/independent validation exited $LASTEXITCODE." }
    Write-ControlState 'COMPLETE_ARCHIVED' 0
    exit 0
} catch {
    $_ | Out-String | Set-Content -LiteralPath (Join-Path $controlRoot 'controller.error.txt') -Encoding UTF8
    Write-ControlState 'FAILED_RETAINED' 1
    exit 1
}
