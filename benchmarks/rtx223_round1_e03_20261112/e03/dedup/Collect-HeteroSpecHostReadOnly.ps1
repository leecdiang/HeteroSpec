# Run in the owner's normal Windows PowerShell. Queries only; no worker launch.
$studyRoot = 'C:\Users\ASUS\Documents\ChatGPT\HeteroSpec'
$gpuUuid = 'GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd'
$observedUtc = [DateTime]::UtcNow.ToString('o')
$candidateNames = @('worker.exe','llama-cli.exe','llama-server.exe','llama-bench.exe','python.exe','pythonw.exe','nvcc.exe','zig.exe','cmake.exe','ninja.exe','opencode.exe')
$processRead = [ordered]@{ Status='UNKNOWN'; HostProcessCount=$null; Candidates=@(); ErrorType=$null }
try {
    $hostProcesses = @(Get-CimInstance Win32_Process -Property Name,ProcessId,ParentProcessId,CreationDate,ExecutablePath -ErrorAction Stop)
    $processRead.Status = 'READ_SUCCEEDED_NOT_A_THREAD_COMPLETION_ATTESTATION'
    $processRead.HostProcessCount = $hostProcesses.Count
    $processRead.Candidates = @($hostProcesses | Where-Object { $_.Name -in $candidateNames -or $_.Name -like 'llama*.exe' } | ForEach-Object {
        [ordered]@{ Name=$_.Name; PID=$_.ProcessId; ParentPID=$_.ParentProcessId; CreatedUtc=$(if ($_.CreationDate) { $_.CreationDate.ToUniversalTime().ToString('o') } else { $null }); ExecutablePath=$_.ExecutablePath }
    })
} catch { $processRead.Status='READ_FAILED_UNKNOWN'; $processRead.ErrorType=$_.Exception.GetType().FullName }
$lockPaths = @(
    'D:\HeteroSpec-PC\RTX_EXPERIMENT.lock',
    "$studyRoot\rtx221-round1-20261112\resources\WINDOWS_RTX_EPOCH.lock"
)
$ledgerPaths = @(
    'D:\rtx192-review-v2\ledger.sqlite',
    'D:\rtx211-q8-20261109\ledger.sqlite',
    "$studyRoot\q8rtx213-supplement-runtime-20261109\ledger.sqlite",
    "$studyRoot\rtx221-round1-20261112\resources\ledger.sqlite",
    "$studyRoot\rtx223-round1-resume-20261112-e02\continuation\safety\runtime\family-ledger.sqlite"
)
$fileReads = @(foreach ($path in @($lockPaths + $ledgerPaths + @($ledgerPaths | ForEach-Object { "$_-wal"; "$_-shm" }))) {
    $entry = [ordered]@{ Path=$path; Status='UNKNOWN'; Bytes=$null; ModifiedUtc=$null; SHA256=$null; StableDuringRead=$null; LeaseMetadata=$null }
    try {
        $before = Get-Item -LiteralPath $path -ErrorAction Stop
        $entry.Bytes=$before.Length; $entry.ModifiedUtc=$before.LastWriteTimeUtc.ToString('o')
        $entry.SHA256=(Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToLowerInvariant()
        if ($path -in $lockPaths) {
            # Select known non-secret lease fields only; never emit raw lock contents.
            try {
                $lease = Get-Content -LiteralPath $path -Raw -ErrorAction Stop | ConvertFrom-Json -ErrorAction Stop
                $safe = [ordered]@{}
                foreach ($field in @('pid','owner_pid','process_id','process_creation_filetime')) {
                    if ($lease.PSObject.Properties.Name -contains $field -and [string]$lease.$field -match '^\d{1,20}$') { $safe[$field]=[string]$lease.$field }
                }
                if ([string]$lease.device_uuid -eq $gpuUuid) { $safe.device_uuid=$gpuUuid }
                if ([string]$lease.epoch -match '^rtx(?:221|223)-round1-[A-Za-z0-9-]{1,80}$') { $safe.epoch=[string]$lease.epoch }
                $entry.LeaseMetadata=$safe
            } catch { $entry.LeaseMetadata='UNREADABLE_OR_NOT_JSON_DO_NOT_DELETE' }
        }
        $after = Get-Item -LiteralPath $path -ErrorAction Stop
        $entry.StableDuringRead=($before.Length -eq $after.Length -and $before.LastWriteTimeUtc -eq $after.LastWriteTimeUtc)
        $entry.Status='OBSERVED'
    } catch [System.Management.Automation.ItemNotFoundException] { $entry.Status='MISSING' }
      catch { $entry.Status='UNREADABLE_UNKNOWN_DO_NOT_DELETE' }
    $entry
})
$gpuRead = @()
if (Get-Command nvidia-smi.exe -ErrorAction SilentlyContinue) {
    foreach ($query in @('--query-gpu=index,uuid,name,memory.total,memory.used,driver_version','--query-compute-apps=pid,process_name,used_memory')) {
        $output = & nvidia-smi.exe "--id=$gpuUuid" $query --format=csv 2>&1 | Out-String
        $gpuRead += [ordered]@{ Query=$query; ExitCode=$LASTEXITCODE; Output=$output.Trim() }
    }
}
[ordered]@{
    Schema='heterospec.owner-readonly-host-evidence.v1'; ObservedUtc=$observedUtc; FinishedUtc=[DateTime]::UtcNow.ToString('o')
    ComputerName=$env:COMPUTERNAME; PowerShellPID=$PID; Processes=$processRead; Files=$fileReads; GPU=$gpuRead
    NoCommandLinesCollected=$true; NoSettingsOrProcessesChanged=$true
    ThreadTerminalEvidence='OWNER_MUST_PROVIDE_SEPARATELY'; EmptyProcessOrGPUResultsDoNotAdmitExecution=$true
} | ConvertTo-Json -Depth 8
