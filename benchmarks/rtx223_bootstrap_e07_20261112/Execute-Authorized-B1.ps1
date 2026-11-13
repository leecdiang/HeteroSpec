$ErrorActionPreference = 'Stop'
$root = 'C:\Users\ASUS\Documents\ChatGPT\HeteroSpec\rtx223-e07'
$state = 'D:\HeteroSpec-PC\rtx223-bootstrap-b1'
$python = 'D:\HeteroSpec-PC\python311\python.exe'
$runner = Join-Path $root 'runner-v3\runner.py'
$approval = Join-Path $root 'OWNER_APPROVAL.json'
$stdout = Join-Path $root 'B1.stdout.log'
$stderr = Join-Path $root 'B1.stderr.log'
if (Test-Path (Join-Path $state 'attempt.jsonl')) { throw 'One-shot attempt already reserved; stop.' }
if ((Get-Date).ToUniversalTime() -lt [DateTime]'2026-11-12T15:40:00Z') { throw 'Window has not opened.' }
if ((Get-Date).ToUniversalTime() -gt [DateTime]'2026-11-12T15:58:29Z') { throw 'Window no longer fits.' }
$expected = Get-Content -Raw -Encoding utf8 (Join-Path $root 'LAUNCH_IDENTITIES.json') | ConvertFrom-Json
foreach ($row in $expected.files) {
    if ((Get-FileHash -LiteralPath $row.path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $row.sha256) {
        throw ('Identity drift ' + $row.path)
    }
}
if ((Test-Path $stdout) -or (Test-Path $stderr)) { throw 'Launch evidence exists; preserve it.' }
New-Item -ItemType Directory -Force $state | Out-Null
$start = (Get-Date).ToUniversalTime().ToString('o')
$procs = Get-CimInstance Win32_Process
$tasks = Get-ScheduledTask
$services = Get-CimInstance Win32_Service
$pattern = 'HeteroSpec|rtx223|rtx221|native-probe|worker.exe|ggml|llama'
$taskHits = @($tasks | Where-Object { ($_.TaskName + ' ' + (($_.Actions | ForEach-Object { $_.Execute + ' ' + $_.Arguments + ' ' + $_.ClassId }) -join ' ')) -match $pattern })
$svcHits = @($services | Where-Object { ($_.Name + ' ' + $_.PathName) -match $pattern })
$worker = @($procs | Where-Object { $_.Name -match '^(worker|native-probe|cpu-probe|llama.*|nvcc)\.exe$' })
$hostEvidence = [ordered]@{
 start_utc=$start; end_utc=(Get-Date).ToUniversalTime().ToString('o')
 processes=@{rows=$procs.Count;system_pid4=@($procs|Where-Object ProcessId -eq 4).Count;candidate_image_hits=$worker.Count;unreadable_commandlines=@($procs|Where-Object {-not $_.CommandLine}).Count}
 task_scheduler=@{rows=$tasks.Count;project_matches=@($taskHits|Select-Object TaskName,State)}
 services=@{rows=$services.Count;project_matches=@($svcHits|Select-Object Name,State)}
}
$hostPath = Join-Path $root 'HOST_PRE_B1.json'
if (Test-Path $hostPath) { throw 'Host receipt already exists.' }
$hostEvidence | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 -LiteralPath $hostPath
if ($worker.Count -or $taskHits.Count -or $svcHits.Count) { throw 'Visible competing task or dispatch source.' }
$owner = Get-Content -Raw -Encoding utf8 $approval | ConvertFrom-Json
$clearance = [ordered]@{
 observed_utc=(Get-Date).ToUniversalTime().ToString('o'); device_uuid=$owner.device_uuid
 nonce=$owner.nonce;source_chats=@('221','223-interrupted','223-successor')
 pending=@();other_leases=@();fenced_through='2026-11-12T23:59:59+08:00'
 dispatcher_ownership='Single owner-authorized Codex task controls this B1 launcher. Known original sessions ended per owner, no competing visible dedicated workers, scheduled tasks or services; runner additionally holds the shared UUID mutex, checks legacy markers and rejects foreign NVML compute occupants.'
 host_snapshot=@{path=$hostPath;sha256=(Get-FileHash $hostPath -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$clearPath = Join-Path $state 'dispatch-clearance.json'
if (Test-Path $clearPath) { throw 'Unexpected existing clearance; stop.' }
$clearance | ConvertTo-Json -Depth 6 | Set-Content -Encoding utf8 -LiteralPath $clearPath
& $python -I -B -S $runner $approval $expected.approval_sha256 1> $stdout 2> $stderr
$code = $LASTEXITCODE
@{exit_code=$code;finished_utc=(Get-Date).ToUniversalTime().ToString('o');retry=$false} |
 ConvertTo-Json | Set-Content -Encoding utf8 (Join-Path $root 'B1_LAUNCH_RESULT.json')
exit $code
