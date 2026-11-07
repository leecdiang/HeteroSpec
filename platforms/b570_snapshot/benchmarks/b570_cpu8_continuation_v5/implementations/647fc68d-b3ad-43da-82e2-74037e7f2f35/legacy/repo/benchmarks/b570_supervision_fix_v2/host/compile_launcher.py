"""One CPU build, invoked only through the observed cold broker."""
import argparse,subprocess
from pathlib import Path
from common import DESIGN,HERE,BASE,load,sha,need,now,write_new
from development_binding import source_hashes

p=argparse.ArgumentParser();p.add_argument('--compiler',required=True);a=p.parse_args()
freeze_path=DESIGN/'SOURCE_REVIEW_FREEZE.json';freeze=load(freeze_path)
need(freeze.get('scope')=='source_review_only' and freeze.get('review_status')=='scoped-clean','review required')
expected=source_hashes(freeze)
need(all(sha(DESIGN/k)==v for k,v in expected.items()),'pre-build source drift')
compiler=Path(a.compiler);need(compiler.is_absolute() and compiler.is_file() and not compiler.is_symlink(),'compiler identity required')
compiler_hash=sha(compiler);dll=HERE/'LauncherCapture.dll';need(not dll.exists(),'fresh build required')
argv=[str(compiler),'/nologo','/target:library','/out:'+str(dll),str(HERE/'LauncherCapture.cs')]
begin=now()
with (BASE/'task/COMPILER.stdout.log').open('xb') as out,(BASE/'task/COMPILER.stderr.log').open('xb') as err:
    proc=subprocess.Popen(argv,stdout=out,stderr=err,cwd=BASE)
    try:code=proc.wait(timeout=120)
    except subprocess.TimeoutExpired:
        proc.kill();proc.wait();raise
end=now();need(code==0 and dll.is_file(),'CPU build failed')
need(sha(compiler)==compiler_hash and all(sha(DESIGN/k)==v for k,v in expected.items()),'build input drift')
write_new(DESIGN/'results/BUILD_RECORD.json',dict(source_review_sha256=sha(freeze_path),source_hashes=expected,
    compiler_sha256=compiler_hash,argv=argv,pid=proc.pid,begin_ns=begin,end_ns=end,exit_code=code,dll_sha256=sha(dll)))
print('CPU launcher build complete; Windows acceptance remains pending')
