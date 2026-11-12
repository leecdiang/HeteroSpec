from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v3';OUT.mkdir(exist_ok=False)
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());fixture=OUT/'fixture.cu';fixture.write_text('__global__ void hs_freeze_fixture() {}\n',encoding='ascii')
nvcc=str(HERE/'toolchain-v1/cuda/bin/nvcc.exe');cc=str(HERE/'toolchain-v1/vc/bin/Hostx64/x64')
variants=[('minimal',[]),('no-ccbin',None),('arch',['--generate-code=arch=compute_120a,code=[sm_120a]']),('deps',['-MD','-MF',str(OUT/'deps.d')]),('showIncludes',['-Xcompiler=/showIncludes'])]
records=[]
for name,extra in variants:
 folder=OUT/name;folder.mkdir();local=env.copy();local['TEMP']=local['TMP']=str(folder)
 argv=[nvcc,'-c',str(fixture),'-o',str(folder/'fixture.obj')]
 if extra is not None:argv+=['-ccbin',cc,*extra]
 (folder/'COMMAND.json').write_text(json.dumps({'argv':argv,'env':env,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest()},indent=2),encoding='utf8')
 with (folder/'compile.log').open('wb') as f:r=subprocess.run(argv,env=local,cwd=folder,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 records.append({'name':name,'code':r.returncode,'log':str(folder/'compile.log')});print(json.dumps(records[-1]),flush=True)
(OUT/'RESULT.json').write_text(json.dumps(records,indent=2),encoding='utf8')
