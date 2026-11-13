"""Compile/link and inspect PE bytes using compiler tools; never load the outputs."""
from pathlib import Path
import os,json,hashlib,subprocess,time,datetime
p=Path(__file__).resolve().parent;e11=p.parent/'rtx223-e11-u-contract'
src=e11/'full-backend-002/src';build=e11/'full-backend-002/build'
recipe=json.loads((e11/'build-003/COMMANDS.json').read_bytes());env=recipe['environment'].copy()
env['TEMP']=env['TMP']=str(p);cl=Path(env['PATH'].split(';')[0])/'cl.exe';link=cl.with_name('link.exe');dump=cl.with_name('dumpbin.exe')
inc=src/'ggml/include';libs=[build/'ggml/src/ggml-cuda/ggml-cuda.lib',build/'ggml/src/ggml-base.lib']
out=p/'link-only';out.mkdir(exist_ok=False)
sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
inputs=[Path(__file__),p/'backend_api_link_only.cpp',cl,link,dump,*libs,*[build/'bin'/x for x in ['ggml-cuda.dll','ggml-base.dll']],*inc.glob('*.h')]
before={str(q):dict(sha256=sha(q),bytes=q.stat().st_size) for q in inputs}
with (out/'INPUTS.json').open('x',encoding='utf8') as f:json.dump(before,f,indent=2)
exe=out/'NOLOAD-api-link-proof.dll';obj=out/'api.obj'
commands=[('compile',[str(cl),'/nologo','/std:c++17','/O2','/EHsc','/MD','/DGGML_SHARED','/DGGML_BACKEND_SHARED','/I'+str(inc),'/sourceDependencies',str(out/'headers.json'),'/c',str(p/'backend_api_link_only.cpp'),'/Fo'+str(obj)]),('link',[str(link),'/NOLOGO','/DLL','/NOENTRY','/MACHINE:X64','/OUT:'+str(exe),str(obj),*[str(q) for q in libs]])]
for name,target in [('full-cuda',build/'bin/ggml-cuda.dll'),('full-base',build/'bin/ggml-base.dll'),('link-proof',exe)]:
 commands.append((name,[str(dump),'/DEPENDENTS','/IMPORTS','/EXPORTS',str(target)]))
results=[];started=time.monotonic()
for name,argv in commands:
 cp=subprocess.run(argv,cwd=out,env=env,capture_output=True,timeout=60,creationflags=0x08000000)
 (out/(name+'.stdout.log')).write_bytes(cp.stdout);(out/(name+'.stderr.log')).write_bytes(cp.stderr)
 results.append(dict(step=name,argv=argv,returncode=cp.returncode))
 if cp.returncode:break
changes=[q for q,row in before.items() if sha(q)!=row['sha256']]
headers=json.loads((out/'headers.json').read_bytes()) if (out/'headers.json').exists() else {}
deps=headers.get('Data',{}).get('Includes',[])
dependencies=[dict(path=q,sha256=sha(q),bytes=Path(q).stat().st_size) for q in deps]
report=dict(pass_=len(results)==5 and all(x['returncode']==0 for x in results) and not changes,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),steps=results,seconds=time.monotonic()-started,input_changes=changes,actual_header_dependencies=dependencies,link_proof_sha256=sha(exe) if exe.exists() else None,numerical_DLL_loads=0,CUDA_initializations=0,GPU_contexts=0,explicit_kernel_calls=0,limitations='PE symbol resolution only;neither full backend nor link proof DLL was loaded;not a runtime smoke or path selection proof')
with (out/'RESULT.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps({k:report[k] for k in ['pass_','seconds','input_changes','numerical_DLL_loads','CUDA_initializations','explicit_kernel_calls','limitations']}))
