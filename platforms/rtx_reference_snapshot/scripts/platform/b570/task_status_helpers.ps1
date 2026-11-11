function Write-AtomicText {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)][string]$Text)
    $directory = Split-Path -Parent $Path
    if ($directory) { New-Item -ItemType Directory -Force -Path $directory | Out-Null }
    $temporary = "$Path.tmp.$PID"
    [System.IO.File]::WriteAllText($temporary, $Text, [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $temporary -Destination $Path -Force
}

function Write-TaskStatus {
    param(
        [Parameter(Mandatory)][string]$JsonPath,
        [Parameter(Mandatory)][string]$TextPath,
        [Parameter(Mandatory)][hashtable]$Status
    )
    $Status.updated_at = (Get-Date).ToString('o')
    Write-AtomicText -Path $JsonPath -Text (($Status | ConvertTo-Json -Depth 8) + "`n")
    $lines = foreach ($key in $Status.Keys) { "$key=$($Status[$key])" }
    Write-AtomicText -Path $TextPath -Text (($lines -join "`r`n") + "`r`n")
}
