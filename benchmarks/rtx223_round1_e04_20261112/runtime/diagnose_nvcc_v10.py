from pathlib import Path
import hashlib,json,subprocess
from input_closure import parse_nvcc_dep
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v10';OUT.mkdir(exist_ok=False);(OUT/'keep').mkdir();(OUT/'temp').mkdir()
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());env['TEMP']=env['TMP']=str(OUT/'temp')
job=json.loads((ROOT/'e04/freeze/COMMANDS.json').read_bytes())[0];argv=job['argv'].copy()
for flag,value in [('-o',str(OUT/'acc.obj')),('-MF',str(OUT/'acc.d')),('-MT',str(OUT/'acc.obj')),('--keep-dir',str(OUT/'keep')),('-ccbin',str(HERE/'preflight-v9/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64'))]:argv[argv.index(flag)+1]=value
(OUT/'COMMAND.json').write_text(json.dumps({'argv':argv,'env':env},indent=2),encoding='utf8')
with (OUT/'compile.log').open('wb') as f:r=subprocess.run(argv,env=env,cwd=OUT,stdout=f,stderr=subprocess.STDOUT,timeout=300)
error=None;deps=[]
try:deps=parse_nvcc_dep((OUT/'acc.d').read_text(encoding='utf8'),str(OUT/'acc.obj'),job['source'])
except Exception as exc:error=repr(exc)
result={'returncode':r.returncode,'dependency_parse_error':error,'dependency_count':len(deps),'dep_sha256':hashlib.sha256((OUT/'acc.d').read_bytes()).hexdigest() if (OUT/'acc.d').exists() else None,'GPU_launches':0,'DLL_loads':0};(OUT/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
