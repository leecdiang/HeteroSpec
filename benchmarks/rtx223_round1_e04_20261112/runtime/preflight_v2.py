"""New dependency-parser and owned-file locking checks only; no native DLL calls."""
from pathlib import Path
import datetime,hashlib,json,sys
from input_closure_v2 import ReadFreeze,parse_nvcc_dep

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'e04/preflight-v2';OUT.mkdir(exist_ok=False)
target='C:/workspace/object with space.obj';source='C:/workspace/source.cu';header='C:/workspace/SDK Include/header.h'
esc=lambda s:s.replace(' ','\\ ')
valid=[esc(target)+': '+source+' '+esc(header)+'\n',esc(target)+' : \\\n '+source+' \\\n '+esc(header)+'\n',r'C:\workspace\plain.obj : C:\workspace\source.cu C:\workspace\header.h'+'\n',esc(target)+': '+source+' '+source+' '+esc(header)+'\n']
cases=[]
for i,text in enumerate(valid):
 try:
  t='C:/workspace/plain.obj' if i==2 else target
  deps=parse_nvcc_dep(text,t,source);ok=len(deps)==(3 if i==3 else 2);error=None
 except Exception as exc:ok=False;error=repr(exc)
 cases.append({'name':'valid-'+str(i),'PASS':ok,'error':error})
bad=['','\n',esc(target)+': '+source+'\n',esc(target)+': '+source+' '+esc(header),esc(target)+': '+source+' '+esc(header)+' \\\n',esc(target)+': '+source+' '+esc(header)+'\nother: other\n','wrong.obj: '+source+' '+esc(header)+'\n',esc(target)+': '+source+' '+source+' '+source+' '+esc(header)+'\n',esc(target)+': '+source+' $(UNPINNED)\n',esc(target)+': '+source+' relative.h\n',esc(target)+': '+source+' C:/bad?.h\n',esc(target)+': '+source+' '+esc(header)+'\x00\n',esc(target)+': '+source+' '+esc(header)+' '+source+'\n']
for i,text in enumerate(bad):
 try:parse_nvcc_dep(text,target,source);ok=False;error=None
 except ValueError as exc:ok=True;error=str(exc)
 cases.append({'name':'reject-'+str(i),'PASS':ok,'error':error})
actual=ROOT/'runtime/preflight-v10/acc.d'
try:
 actualdeps=parse_nvcc_dep(actual.read_text(encoding='utf8'),str(ROOT/'runtime/preflight-v10/acc.obj'),str(ROOT/'runtime/source-v1/ggml/src/ggml-cuda/acc.cu'));cases.append({'name':'actual-nvcc-recipe','PASS':len(actualdeps)>50,'dependencies':len(actualdeps),'recipe_sha256':hashlib.sha256(actual.read_bytes()).hexdigest()})
except Exception as exc:cases.append({'name':'actual-nvcc-recipe','PASS':False,'error':repr(exc)})
fixture=OUT/'owned-lock-fixture.bin';fixture.write_bytes(b'original');held=ReadFreeze();held.add(fixture)
try:
 cases.append({'name':'locked-read','PASS':fixture.read_bytes()==b'original'})
 for name,action in [('write',lambda:fixture.write_bytes(b'changed')),('truncate',lambda:fixture.open('wb').close()),('delete',lambda:fixture.unlink())]:
  try:action();ok=False;error=None
  except PermissionError as exc:ok=True;error=repr(exc)
  cases.append({'name':'locked-deny-'+name,'PASS':ok,'error':error})
finally:held.release()
fixture.write_bytes(b'released');cases.append({'name':'released-write','PASS':fixture.read_bytes()==b'released'});fixture.unlink();cases.append({'name':'released-delete','PASS':not fixture.exists()})
result={'schema':'heterospec.e04.new-preflight.v2','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'PASS' if all(c['PASS'] for c in cases) else 'FAIL','cases':cases,'count':len(cases),'GPU_launches':0,'DLL_loads':0,'scope':'strict Make dependency grammar incl observed nvcc duplicate and own temporary file locking only','source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__),Path(__file__).with_name('input_closure_v2.py')]}}
(OUT/'RESULT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2));raise SystemExit(0 if result['status']=='PASS' else 2)
