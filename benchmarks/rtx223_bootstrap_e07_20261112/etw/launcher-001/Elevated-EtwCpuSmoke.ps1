$ErrorActionPreference = 'Stop'
$python = 'D:\HeteroSpec-PC\python311\python.exe'
$smoke = Join-Path $PSScriptRoot 'smoke.py'
$observer = Join-Path $PSScriptRoot 'build-002\observation.dll'
$output = Join-Path $PSScriptRoot 'ELEVATED_ETW_CPU_001.json'
$expected = @{
    $python = '5f7b89a612c9b8af1d6456cdfcd1dbe5ca630849e79aebced9bee9a6694952ec'
    $smoke = 'b1e367f3acc79f62a87693ca7abf70858476896424625279b283570654ba2656'
    $observer = 'e9e8a5f0a375f7d793104ce489a68db28ebcc3eae7c7a3b43b64f7b2e69366f2'
}
foreach ($path in $expected.Keys) {
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected[$path]) {
        throw "Frozen CPU smoke identity mismatch: $path"
    }
}
if (Test-Path -LiteralPath $output) { throw 'CPU smoke output already exists; retain it.' }
& $python -I -S -B $smoke $observer $output 1> (Join-Path $PSScriptRoot 'ELEVATED_ETW_CPU_001.stdout.log') 2> (Join-Path $PSScriptRoot 'ELEVATED_ETW_CPU_001.stderr.log')
exit $LASTEXITCODE
