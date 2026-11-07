param([Parameter(Mandatory=$true)][string]$OutputPath,
      [Parameter(Mandatory=$true)][string]$RepoRoot,
      [Parameter(Mandatory=$true)][string]$PythonPath,
      [Parameter(Mandatory=$true)][string]$GitPath)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $RepoRoot
$env:PATH = (Split-Path -Parent $GitPath) + ';' + $env:PATH
$selfProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$PID"
$parentProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($selfProcess.ParentProcessId)"
$pythonVersion = & $PythonPath --version
if ($LASTEXITCODE -ne 0) { throw 'Python unavailable in scheduled context' }
$studyBranch = & git branch --show-current
if ($LASTEXITCODE -ne 0 -or $studyBranch -ne 'experiment/b570-direct-id-qualification-v1') { throw 'Wrong scheduled-context branch' }
[ordered]@{status='PASS';utc=(Get-Date).ToUniversalTime().ToString('o');pid=$PID;
    parent_pid=$selfProcess.ParentProcessId;parent_name=$parentProcess.Name;
    user=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name;
    python_version=$pythonVersion;branch=$studyBranch;working_directory=$PWD.Path;
    inference_executed=$false;energy_collector_started=$false} |
    ConvertTo-Json | Set-Content -LiteralPath $OutputPath -Encoding UTF8
