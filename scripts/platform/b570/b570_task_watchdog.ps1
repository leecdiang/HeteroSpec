[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$RunRoot,
    [string]$FormalTaskName = 'HeteroSpec_B570_Formal',
    [string]$StatusPath,
    [int]$StaleSeconds = 300
)
$ErrorActionPreference='Continue'
. (Join-Path $PSScriptRoot 'task_status_helpers.ps1')
$repo=(Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$central=if($StatusPath){$StatusPath}else{Join-Path $repo 'work\b570\current_task_status.json'}
$watchJson=Join-Path $RunRoot 'watchdog-status.json'; $watchTxt=Join-Path $RunRoot 'watchdog-status.txt'
$started=Get-Date
while($true){
    $task=Get-ScheduledTask -TaskName $FormalTaskName -ErrorAction SilentlyContinue
    $info=Get-ScheduledTaskInfo -TaskName $FormalTaskName -ErrorAction SilentlyContinue
    $value=$null
    if(Test-Path $central){try{$value=Get-Content $central -Raw|ConvertFrom-Json}catch{}}
    $age=$null
    if($value -and $value.heartbeat_at){try{$age=((Get-Date)-([datetime]$value.heartbeat_at)).TotalSeconds}catch{}}
    $watch=[ordered]@{schema='heterospec.b570.watchdog.v1';state='WATCHING';formal_task_state=$task.State;formal_task_last_result=$info.LastTaskResult;heartbeat_age_seconds=$age;checked_at=(Get-Date).ToString('o')}
    Write-TaskStatus -JsonPath $watchJson -TextPath $watchTxt -Status $watch
    if($value.state -in @('COMPLETE','COMPLETE_STOP_RULE','FAILED_INFRASTRUCTURE','RUNTIME_FAILURE','PRECONDITION_FAILURE','CONFIGURATION_ERROR','FINALIZING')){break}
    if($age -ne $null -and $age -gt $StaleSeconds){
        $snapshot=[ordered]@{detected_at=(Get-Date).ToString('o');reason="central heartbeat stale for $([math]::Round($age,1)) seconds";formal_task=$task;formal_task_info=$info;processes=@(Get-Process|Where-Object{$_.ProcessName -match 'python|llama|presentmon|powershell'}|Select-Object Id,ProcessName,StartTime)}
        Write-AtomicText -Path (Join-Path $RunRoot 'FAILED_INFRASTRUCTURE.snapshot.json') -Text (($snapshot|ConvertTo-Json -Depth 8)+"`n")
        $failed=[ordered]@{schema='heterospec.b570.formal-task.v1';run_id=(Split-Path $RunRoot -Leaf);state='FAILED_INFRASTRUCTURE';stage='watchdog';detail=$snapshot.reason;heartbeat_at=(Get-Date).ToString('o')}
        Write-TaskStatus -JsonPath $central -TextPath ([System.IO.Path]::ChangeExtension($central,'.txt')) -Status $failed
        Stop-ScheduledTask -TaskName $FormalTaskName -ErrorAction SilentlyContinue
        break
    }
    if(((Get-Date)-$started).TotalSeconds -gt 180 -and $task.State -ne 'Running' -and -not $value){break}
    Start-Sleep -Seconds 60
}
