from pathlib import Path
import json,subprocess,time,shutil,hashlib
p=Path(__file__).resolve().parent;e=p.parent/'rtx223-e11-u-contract';out=p/'build-M';env=json.loads((e/'build-003/COMMANDS.json').read_bytes())['environment'];env['TEMP']=env['TMP']=str(p);cmake=e/'tools/cmake-3.31.8-windows-x86_64/bin/cmake.exe'
cmd=[str(cmake),'--build',str(out),'--target','rtx244_worker','rtx244_reference','-j','2'];start=time.monotonic()
with (out/'resume-001.stdout.log').open('xb') as a,(out/'resume-001.stderr.log').open('xb') as b:cp=subprocess.run(cmd,env=env,cwd=p,stdout=a,stderr=b,timeout=1800,creationflags=0x08000000)
report=dict(argv=cmd,returncode=cp.returncode,seconds=time.monotonic()-start,previous_failure='Worker compiled before updated include path was picked up;preserved original build log;no GPU/model execution')
(out/'RESUME_001.json').write_text(json.dumps(report,indent=2),encoding='utf8')
if cp.returncode:(p/'BUILD_STOP').write_text('M resume failed;see logs',encoding='utf8');raise SystemExit(1)
stage=p.parent/'rtx223-e07/staging-B1/numeric-001'
for name in ['cudart64_12.dll','cublas64_12.dll','cublasLt64_12.dll','msvcp140.dll','vcruntime140.dll','vcruntime140_1.dll','vcomp140.dll']:
 shutil.copy2(stage/name,out/'bin'/name)
for name in ['native_worker.cpp','native_reference.cpp','CMakeLists.txt']:shutil.copy2(p/name,out/name)
manifest=dict(source='0fb8f157702702f33f4e018de8701b2569a1bc28',files=[dict(path=str(q),bytes=q.stat().st_size,sha256=hashlib.sha256(q.read_bytes()).hexdigest()) for q in sorted((out/'bin').iterdir()) if q.suffix in ['.dll','.exe']],source_files=[dict(path=str(p/n),sha256=hashlib.sha256((p/n).read_bytes()).hexdigest()) for n in ['native_worker.cpp','native_reference.cpp']],no_numerical_load=True)
(p/'M_READY.json').write_text(json.dumps(manifest,indent=2),encoding='utf8');print(json.dumps(dict(M_READY=True,seconds=report['seconds'])))
