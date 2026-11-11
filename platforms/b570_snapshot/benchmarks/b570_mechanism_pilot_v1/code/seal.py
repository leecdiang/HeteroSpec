"""Immutable CAS evidence sealing and actual clean CPU restore; no model load."""
from pathlib import Path
import json,hashlib,zipfile,subprocess,time,sys
R=Path(__file__).parent;G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
assert not (R/'LOCK.json').exists(),'worker must finish before sealing'
assert load(R/'INDEPENDENT_VERIFICATION.json')['status']=='PASS'
for s in (R/'sessions').iterdir():assert (s/'SESSION_CLOSE.json').exists(),'unfinished session '+s.name
(R/'packaging').mkdir(exist_ok=True)
head=subprocess.check_output([G,'rev-parse','HEAD'],cwd=R,text=True).strip()
subprocess.run([G,'bundle','create',str(R/'packaging/GIT_HISTORY.bundle'),'--all'],cwd=R,check=True)
files={};objects={}
for p in sorted(R.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(R);parts=rel.parts
 if parts[0] in ['archive','.git','__pycache__'] or p.name in ['STOP','LOCK.json'] or p.name.endswith('.tmp'):continue
 if parts[0] in ['build','candidate-build'] and not (p.suffix in ['.exe','.dll'] and p.parent.name=='Release') and p.name not in ['CMakeCache.txt','b570-pilot-target.vcxproj','b570-pilot-native.vcxproj','b570-pilot-cross.vcxproj','b570-candidate-target.vcxproj','b570-candidate-native.vcxproj','llama-b570-pilot.vcxproj','llama-common-b570-pilot.vcxproj']:continue
 if p.suffix=='.dll' and p.name!='llama-b570-pilot.dll':continue # published runtime external; new private library included
 if p.name in ['ARCHIVE_RESTORE.json','ARCHIVE_INDEX.json','DELIVERY_VERIFIED.json','REMOTE_READBACK.json']:continue
 h=sha(p);name=str(rel).replace('\\','/');files[name]=dict(sha256=h,bytes=p.stat().st_size);objects.setdefault(h,p)
index=dict(schema='heterospec.cas.v1',source_head=head,files=files,objects={h:dict(bytes=p.stat().st_size) for h,p in objects.items()},external_models_runtime=load(R/'ASSET_MANIFEST.json')['checked'],external_build_inputs=load(R/'BUILD_BINDINGS.json')['paths'],old_packages=[d['sha256'] for d in load(R/'STAGE0.json')['restores']],A_unused_initial_cross_binary='not executed; source recoverable in A epoch; only actual B helper binary is payload',model_forwards_during_packaging=0)
tmp=R/'archive'/('package-'+str(time.time_ns())+'.zip')
with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
 for i,(h,p) in enumerate(objects.items()):
  z.write(p,'objects/'+h)
  if i%200==0:print('PACK',i,'/',len(objects),flush=True)
 z.writestr('INDEX.json',json.dumps(index,sort_keys=True).encode('utf8'))
address=sha(tmp);archive=tmp.with_name(address+'.zip');tmp.rename(archive)
save(R/'ARCHIVE_INDEX.json',dict(archive=str(archive),sha256=address,bytes=archive.stat().st_size,files=len(files),objects=len(objects),source_head=head))
restore=R/'archive'/('restore-'+str(time.time_ns()));restore.mkdir()
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for h in objects:assert hashlib.sha256(z.read('objects/'+h)).hexdigest()==h
 for name,d in files.items():
  p=restore/name;assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read('objects/'+d['sha256']));assert sha(p)==d['sha256']
 print('RESTORED',len(files),flush=True)
# Runtime DLLs are not in the package; bind/read installed bytes without copying them.
for name,d in index['external_models_runtime'].items():assert sha(Path(name))==d['sha256']
for name,d in index['external_build_inputs'].items():assert sha(Path(name))==d['sha256']
import shutil
used=load(restore/'B_FREEZE.json')['binaries']
used=dict(used,**load(restore/'C_FREEZE.json')['binaries'])
for rel,h in used.items():
 if rel.endswith('.dll') and not (restore/rel).exists():
  assert sha(R/rel)==h;(restore/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/rel,restore/rel)
for filename,code in [('validate_A.py','A_VERIFICATION.json'),('validate_B.py','CAUSAL_RESULTS.json'),('derive_state_comparison.py','DONOR_STATE_COMPARISON.json'),('validate_C.py','C_VERIFICATION.json'),('validate_D.py','D_VERIFICATION.json'),('validate_E_bridge.py','E_BRIDGE_VERIFICATION.json'),('validate_E_final.py','E_VERIFICATION.json'),('independent_verify.py','INDEPENDENT_VERIFICATION.json'),('normative_review.py','NORMATIVE_REVIEW.json')]:
 if filename=='validate_B.py' and not (restore/'B_MANIFEST.json').exists():continue
 if filename=='validate_C.py' and not (restore/'C_VERIFICATION.json').exists():continue
 if filename=='validate_D.py' and not (restore/'D_VERIFICATION.json').exists():continue
 if filename=='validate_E_final.py' and not (restore/'E_VERIFICATION.json').exists():continue
 if filename=='validate_E_bridge.py' and not (restore/'E_BRIDGE_VERIFICATION.json').exists():continue
 cmd=[sys.executable,str(restore/filename),str(restore)]
 subprocess.run(cmd,cwd=restore,check=True)
 expected=load(R/code);got=load(restore/code)
 if code=='INDEPENDENT_VERIFICATION.json':expected.pop('utc',None);got.pop('utc',None)
 assert expected==got,'clean CPU rederivation differs '+code
subprocess.run([G,'clone',str(restore/'packaging/GIT_HISTORY.bundle'),str(restore/'source-history')],check=True,stdout=subprocess.DEVNULL)
assert subprocess.check_output([G,'rev-parse','HEAD'],cwd=restore/'source-history',text=True).strip()==head
receipt=dict(status='PASS',archive=str(archive),archive_sha256=address,archive_bytes=archive.stat().st_size,files=len(files),objects=len(objects),restore=str(restore),source_head=head,all_crc_sha_and_restored_mapping_verified=True,actual_clean_CPU_rederivation_identical=True,installed_external_assets_reread=True,private_executables_restored=True,history_bundle_restored=True,model_requests=0)
save(R/'ARCHIVE_RESTORE.json',receipt);print('SEALED',receipt,flush=True)
