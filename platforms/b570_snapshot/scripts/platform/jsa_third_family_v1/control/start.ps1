$ErrorActionPreference = 'Stop'
$repoPath = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$localPath = Join-Path (Split-Path $repoPath -Parent) 'third-family'
$policy = Get-Content -LiteralPath (Join-Path $repoPath 'benchmarks/jsa_third_family_v1/AUTORUN_BOUNDARY.json') -Raw | ConvertFrom-Json
$runnerPath = Join-Path $PSScriptRoot 'autorun.py'
if (Test-Path -LiteralPath (Join-Path $localPath 'runs/formal')) { throw 'Formal run already exists. It must not be replayed.' }
New-Item -ItemType Directory -Path (Join-Path $localPath 'autorun') -Force | Out-Null
$taskProcess = Start-Process -FilePath $policy.python -ArgumentList @('-u', ('"' + $runnerPath + '"')) -WorkingDirectory $repoPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $localPath 'autorun/launch.stdout.log') -RedirectStandardError (Join-Path $localPath 'autorun/launch.stderr.log') -PassThru
[pscustomobject]@{ PID = $taskProcess.Id; Status = 'Detached background workflow started'; Log = (Join-Path $localPath 'autorun/run.log') } | Format-List
