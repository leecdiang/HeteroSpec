"""Authenticated remote P1 body verification and fresh sequential raw reconstruction."""
import concurrent.futures,base64,hashlib,json,pathlib,subprocess,urllib.request,zipfile,shutil,sys,os
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,file_sha,encode
from raw_audit import audit
REPO=ROOT.parents[1];GIT=r'C:/hs/pr108-tools/git/cmd/git.exe';COMMIT='d744f59a242b4a78a3eb959ab5f83f74795ef6ff'
def main():
 credential=subprocess.run([GIT,'credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True,env=dict(os.environ,GIT_TERMINAL_PROMPT='0')).stdout;fields=dict(x.split('=',1) for x in credential.splitlines() if '=' in x);token=fields['password']
 listing=subprocess.check_output([GIT,'ls-tree','-r','-z',COMMIT,'--','benchmarks/b570_geometry_state_codesign_v1/p1'],cwd=REPO).decode().split(chr(0));entries=[]
 for line in listing:
  if not line:continue
  meta,name=line.split(chr(9),1);mode,kind,blob=meta.split();assert kind=='blob';entries.append((name,blob))
 dest=ROOT/'_host/p1_remote_readback';assert not dest.exists();dest.mkdir()
 def fetch(entry):
  name,blob=entry;url='https://api.github.com/repos/leecdiang/HeteroSpec/git/blobs/'+blob
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HeteroSpec-P1-restore','Authorization':'Bearer '+token}),timeout=45) as response:body=json.load(response)
  assert body['sha']==blob and body['encoding']=='base64';data=base64.b64decode(body['content']);assert hashlib.sha1(('blob '+str(len(data))+chr(0)).encode()+data).hexdigest()==blob;assert data==(REPO/name).read_bytes();p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
  return dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob=blob)
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:remote_files=list(executor.map(fetch,entries))
 remote=dest/'benchmarks/b570_geometry_state_codesign_v1/p1';parts=read_json(remote/'ARCHIVE_PARTS.json');archive=ROOT/'_host/P1_REMOTE_COMPLETE_CAS.zip'
 with archive.open('xb') as out:
  for part in parts['parts']:
   data=(remote/part['path']).read_bytes();assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256'];out.write(data)
 assert archive.stat().st_size==parts['archive_bytes'] and file_sha(archive)==parts['archive_sha256'];manifest=read_json(remote/'ARCHIVE_MANIFEST.json');audited=[];incomplete=[];restored_files=0
 with zipfile.ZipFile(archive) as z:
  assert z.read('MANIFEST.json')==encode(manifest);objects={x['sha256'] for x in manifest['files']};assert set(z.namelist())=={'MANIFEST.json'}|{'objects/'+h for h in objects}
  for h in objects:assert hashlib.sha256(z.read('objects/'+h)).hexdigest()==h
  plan=json.loads(z.read('objects/'+next(x['sha256'] for x in manifest['files'] if x['path']=='p0/PLAN_P1.json')));runtime=json.loads(z.read('objects/'+next(x['sha256'] for x in manifest['files'] if x['path']=='p0/RUNTIME.json')));slots={s['slot']:s for s in plan['slots']};groups={}
  for row in manifest['files']:
   if row['path'].startswith('_host/run/') and len(row['path'].split('/'))>3:groups.setdefault(row['path'].split('/')[2],[]).append(row)
  for slot,rows in sorted(groups.items()):
   target=ROOT/'_host'/('p1-remote-restore-'+slot);assert not target.exists();target.mkdir()
   try:
    for row in rows:
     data=z.read('objects/'+row['sha256']);assert len(data)==row['bytes'];p=target/pathlib.PurePosixPath(row['path']).name;p.write_bytes(data);assert file_sha(p)==row['sha256'];restored_files+=1
    if (target/'NORMALIZED.json').exists():audit(target,slots[slot],runtime);audited.append(slot)
    else:incomplete.append(slot)
   finally:
    resolved=target.resolve();assert resolved.is_relative_to((ROOT/'_host').resolve()) and resolved.name=='p1-remote-restore-'+slot;shutil.rmtree(resolved)
  contract=json.loads(z.read('objects/'+next(x['sha256'] for x in manifest['files'] if x['path']=='p1/EXECUTION_CONTRACT_AUDIT.json')));assert contract['status']=='VIOLATION_REQUIRES_STOP' and len(contract['violations'])==8
 result=dict(status='PASS_AUTHENTICATED_REMOTE_BYTES_AND_FRESH_SEQUENTIAL_RESTORE',scientific_qualification='FAILED_EXECUTION_CONTRACT_AND_INCOMPLETE_P1; transport success does not repair science',commit=COMMIT,remote_files=remote_files,files_verified=len(remote_files),archive_sha256=file_sha(archive),logical_files=manifest['logical_files'],unique_objects=manifest['unique_objects'],restored_slot_files=restored_files,complete_slots_independently_reaudited=audited,incomplete_slots_retained=incomplete,contract_violations_recovered=8,native_starts_added=0,original_F0_unchanged=True)
 with (ROOT/'p1/REMOTE_RESTORE.json').open('xb') as f:f.write(encode(result))
 print(json.dumps({k:v for k,v in result.items() if k not in ('remote_files','complete_slots_independently_reaudited')}))
if __name__=='__main__':main()
