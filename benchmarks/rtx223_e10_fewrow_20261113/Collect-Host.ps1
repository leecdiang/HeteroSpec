param([string]$destination)
$ErrorActionPreference='Stop'
$start=[DateTimeOffset]::UtcNow.ToString('o')
$processes=Get-CimInstance Win32_Process
$tasks=Get-ScheduledTask
$services=Get-CimInstance Win32_Service
$pattern='HeteroSpec|rtx223|rtx221|native-probe|worker.exe|ggml|llama|capture.exe|operator.*exe'
$taskHits=@($tasks|Where-Object {($_.TaskName+' '+(($_.Actions|ForEach-Object {$_.Execute+' '+$_.Arguments+' '+$_.ClassId}) -join ' ')) -match $pattern})
$serviceHits=@($services|Where-Object {($_.Name+' '+$_.PathName) -match $pattern})
$workers=@($processes|Where-Object {$_.Name -match '^(worker|native-probe|cpu-probe|capture|operator.*|llama.*|nvcc)\.exe$'})
$receipt=[ordered]@{start_utc=$start;end_utc=[DateTimeOffset]::UtcNow.ToString('o');all_processes=@($processes|Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine);all_tasks=@($tasks|Select-Object TaskPath,TaskName,State,Actions);project_tasks=@($taskHits|Select-Object TaskName,State);project_services=@($serviceHits|Select-Object Name,State);competing_workers=@($workers|Select-Object ProcessId,Name)}
if(Test-Path -LiteralPath $destination){throw 'Existing host receipt'}
$receipt|ConvertTo-Json -Depth 7|Set-Content -Encoding utf8 -LiteralPath $destination
if($workers.Count -or $taskHits.Count -or $serviceHits.Count){throw 'Competing task or dispatcher'}
