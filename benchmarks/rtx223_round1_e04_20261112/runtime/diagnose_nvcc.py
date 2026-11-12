"""CPU compiler-driver diagnostics only; never load the numerical DLL."""
from pathlib import Path
import hashlib,json,os,subprocess,time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v2';OUT.mkdir(exist_ok=False)
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());job=json.loads((ROOT/'e04/freeze/COMMANDS.json').read_bytes())[0]
variants=[('original-env',True,False),('without-showIncludes',False,False),('full-inherited-env',False,True)]
receipts=[]
for name,show,inherited in variants:
 folder=OUT/name;folder.mkdir();(folder/'keep').mkdir();(folder/'temp').mkdir()
 args=job['argv'].copy()
 for flag,value in [('-o',str(folder/'acc.obj')),('-MF',str(folder/'acc.d')),('-MT',str(folder/'acc.obj')),('--keep-dir',str(folder/'keep'))]:args[args.index(flag)+1]=value
 if not show:args.remove('-Xcompiler=/showIncludes')
 args.append('-v');effective=os.environ.copy() if inherited else {};effective.update(env);effective['TEMP']=effective['TMP']=str(folder/'temp')
 (folder/'COMMAND.json').write_text(json.dumps({'argv':args,'codegen_env':env,'full_inherited_env':inherited},indent=2),encoding='utf8')
 with (folder/'compile.log').open('wb') as f:r=subprocess.run(args,env=effective,cwd=folder,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 receipts.append({'name':name,'returncode':r.returncode,'argv':args,'log_sha256':hashlib.sha256((folder/'compile.log').read_bytes()).hexdigest()})
 print(json.dumps(receipts[-1]),flush=True)
 if r.returncode==0:break
(OUT/'RESULT.json').write_text(json.dumps({'receipts':receipts,'GPU_launches':0,'DLL_loads':0},indent=2),encoding='utf8')
