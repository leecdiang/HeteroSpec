$ErrorActionPreference = 'Stop'
$phaseLog = Join-Path $PSScriptRoot 'ELEVATED_ACL_CPU_001.bootstrap.log'
if (Test-Path -LiteralPath $phaseLog) { throw 'Retain existing ACL bootstrap log.' }
Start-Transcript -LiteralPath $phaseLog | Out-Null
try {
    $python = 'D:\HeteroSpec-PC\python311\python.exe'
    $smoke = Join-Path (Split-Path $PSScriptRoot -Parent) 'acl\test_staged_cpu_elevated.py'
    if ((Get-FileHash -LiteralPath $python).Hash.ToLowerInvariant() -ne '5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec') { throw 'Python identity mismatch' }
    if ((Get-FileHash -LiteralPath $smoke).Hash.ToLowerInvariant() -ne 'c1be405d8e72e18caa172ae5229b03c71b76e60c1b6ca7ed6612d4869459d3f5') { throw 'ACL CPU source identity mismatch' }
    & $python -I -S -B $smoke 1> (Join-Path $PSScriptRoot 'ELEVATED_ACL_CPU_001.stdout.log') 2> (Join-Path $PSScriptRoot 'ELEVATED_ACL_CPU_001.stderr.log')
    $exitCode = $LASTEXITCODE
    Write-Output ('CPU_ACL_EXIT=' + $exitCode)
} catch {
    Write-Output ($_ | Out-String)
    $exitCode = 1
} finally {
    Stop-Transcript | Out-Null
}
exit $exitCode
