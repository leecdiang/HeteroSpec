"""Local CAS ZIP seal and clean restore; no weights or runtime DLL payloads."""
import json,hashlib,zipfile,subprocess,sys,os,time
from pathlib import Path
ROOT=Path(__file__).parent
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def seal():
 if (ROOT/'LOCK.json').exists():raise RuntimeError('Inference lock still exists; no sealing live outputs')
 stamp=time.time_ns();dest=ROOT/'archive';dest.mkdir(exist_ok=True);bundle=ROOT/'recovery'/f'frozen-source-{stamp}.bundle'
 subprocess.run(['git','bundle','create',str(bundle),'--all'],cwd=ROOT,check=True)
 selected=[];excluded=[]
 for p in ROOT.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(ROOT);parts=set(rel.parts)
  if parts & {'.git','archive','remote-readback','__pycache__','tokenizer-build'} or any(s.startswith('restore-') for s in rel.parts):continue
  if 'build' in parts and not (rel.parts[:2]==('build','Release') and p.suffix=='.exe'):continue
  if p.suffix.lower() in ['.dll','.gguf']:
   excluded.append({'path':str(rel).replace('\\','/'),'sha256':sha(p),'bytes':p.stat().st_size,'reason':'Installed immutable external runtime/model; payload excluded'});continue
  if p.name.endswith('.tmp'):continue
  selected.append(p)
 models=read(ROOT/'PROTOCOL.json')['models'] if (ROOT/'PROTOCOL.json').exists() else {k:v for k,v in read(ROOT/'ASSET_POST.json')['checked'].items() if k.endswith('.gguf')}
 index={'schema':'heterospec.local.cas-zip.v1','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':{},'objects':{},'external_payloads':excluded,'old_capsule_dependency':{k:v for k,v in read(ROOT/'ASSET_POST.json')['checked'].items() if 'raw-capsule-v1' in k},'raw_units':sum(1 for _ in (ROOT/'raw').glob('*/RESULT.json')),'models_excluded':models}
 tmp=dest/f'pending-{stamp}.zip'
 with zipfile.ZipFile(tmp,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
  for p in sorted(selected):
   h=sha(p);rel=str(p.relative_to(ROOT)).replace('\\','/');size=p.stat().st_size
   index['files'][rel]={'sha256':h,'bytes':size}
   if h not in index['objects']:
    z.write(p,'objects/'+h);index['objects'][h]={'bytes':size,'crc32':z.getinfo('objects/'+h).CRC}
  z.writestr('INDEX.json',json.dumps(index,indent=2,ensure_ascii=False)+'\n')
 digest=sha(tmp);sealed=dest/(digest+'.zip');tmp.rename(sealed)
 restore=dest/f'restore-{stamp}';restore.mkdir(exist_ok=False)
 with zipfile.ZipFile(sealed) as z:
  assert z.testzip() is None,'ZIP CRC failure'
  for h,m in index['objects'].items():
   info=z.getinfo('objects/'+h);assert info.CRC==m['crc32'] and info.file_size==m['bytes']
  for name,m in index['files'].items():
   target=restore/name;assert target.resolve().is_relative_to(restore.resolve()),'Unsafe path'
   target.parent.mkdir(parents=True,exist_ok=True)
   with z.open('objects/'+m['sha256']) as source,target.open('xb') as out:
    while data:=source.read(8*1024*1024):out.write(data)
   assert target.stat().st_size==m['bytes'] and sha(target)==m['sha256']
 before=read(restore/'INDEPENDENT_VERIFICATION.json')
 command=[sys.executable,str(restore/'independent_verify.py'),str(restore)]
 if before['status']=='PASS_STRUCTURAL_PARTIAL':command.append('--allow-partial')
 result=subprocess.run(command,capture_output=True,text=True)
 save(dest/f'CPU_RESTORE-{stamp}.json',{'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
 assert result.returncode==0,result.stdout+result.stderr
 assert read(restore/'INDEPENDENT_VERIFICATION.json')==before,'Clean restore rederivation differs'
 restored_bundle=restore/bundle.relative_to(ROOT);history=dest/f'history-{stamp}.git'
 subprocess.run(['git','clone','--quiet','--bare',str(restored_bundle),str(history)],check=True)
 restored_head=subprocess.check_output(['git','--git-dir',str(history),'rev-parse','HEAD'],text=True).strip()
 assert restored_head==index['source_commit'],'Frozen Git history HEAD differs'
 numerical=read(ROOT/'EXECUTION_FREEZE.json')['numerical_assets'] if (ROOT/'EXECUTION_FREEZE.json').exists() else read(ROOT/'RECOVERY_AMENDMENT.json')['unchanged_numerical_assets'];binary_checks=[]
 if not (ROOT/'EXECUTION_FREEZE.json').exists() and (ROOT/'TIMER_AMENDMENT.json').exists():numerical=dict(numerical,**read(ROOT/'TIMER_AMENDMENT.json')['new_assets'])
 if not (ROOT/'EXECUTION_FREEZE.json').exists() and (ROOT/'MATCHED_RESERVATION_AMENDMENT.json').exists():
  amendment=read(ROOT/'MATCHED_RESERVATION_AMENDMENT.json');numerical=dict(numerical,**{'build/Release/b570-closeout-target.exe':amendment['new_target_sha256'],'src/target.cpp':amendment['new_target_source_sha256']})
 for name,h in numerical.items():
  path=restore/name if name.endswith('.exe') or name.startswith('src/') else ROOT/name
  assert path.is_file() and sha(path)==h,name
  binary_checks.append({'path':str(path),'sha256':h,'restore_payload':path.is_relative_to(restore)})
 external_checks=[]
 for name,m in read(ROOT/'ASSET_POST.json')['checked'].items():
  if str(ROOT).lower() in name.lower():continue
  assert Path(name).exists() and sha(name)==m['sha256'],name
  external_checks.append({'path':name,'sha256':m['sha256']})
 receipt={'status':'PASS','archive':str(sealed),'archive_sha256':digest,'archive_bytes':sealed.stat().st_size,'files':len(index['files']),'objects':len(index['objects']),'raw_units':index['raw_units'],'restore':str(restore),'crc_all_objects':True,'all_restored_file_sha256':True,'CPU_rederivation_identical':True,'frozen_git_history_restored_head':restored_head,'bound_numerical_assets':binary_checks,'external_installed_asset_checks':external_checks,'source_bundle':str(bundle),'source_bundle_sha256':sha(bundle),'model_forwards':0,'external_model_identity_only':'Full byte hashes verified; no new inference or model qualification performed during restore'}
 save(ROOT/'ARCHIVE_RESTORE.json',receipt);save(ROOT/'ARCHIVE_INDEX.json',index)
 print({k:receipt[k] for k in ['status','archive','archive_bytes','files','objects','raw_units']},flush=True)
if __name__=='__main__':seal()
