from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'preflight-v5'
env=json.loads((ROOT/'e04/freeze/ENVIRONMENT.json').read_bytes());fixture=OUT/'fixture.cu';fixture.write_text('__global__ void hs_freeze_fixture() {}\n',encoding='ascii')
nvcc=str(HERE/'toolchain-v1/cuda/bin/nvcc.exe')
variants=[('full-layout',str(OUT/'msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64')),('short-copy-alias','C:/workspace/hs223e04-native-tc/bin/Hostx64/x64')]
records=[]
for name,cc in variants:
 folder=OUT/name;folder.mkdir();local=env.copy();local['TEMP']=local['TMP']=str(folder)
 argv=[nvcc,'-c',str(fixture),'-o',str(folder/'fixture.obj'),'-ccbin',cc,'--generate-code=arch=compute_120a,code=[sm_120a]']
 (folder/'COMMAND.json').write_text(json.dumps({'argv':argv,'env':env,'fixture_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'scope':'CPU-only owncopy path diagnostic; junctionpoints onlyatownednewcopy, nooldpaths'},indent=2),encoding='utf8')
 with (folder/'compile.log').open('wb') as f:r=subprocess.run(argv,env=local,cwd=folder,stdout=f,stderr=subprocess.STDOUT,timeout=180)
 records.append({'name':name,'code':r.returncode,'log':str(folder/'compile.log')});print(json.dumps(records[-1]),flush=True)
(OUT/'RESULT.json').write_text(json.dumps(records,indent=2),encoding='utf8')
