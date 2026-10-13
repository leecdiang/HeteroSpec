"""Actual fresh network Git readback, batched raw blobs and complete restoration."""
from closure import *
def git(*args,cwd=REPO):return subprocess.check_output(['git',*args],cwd=cwd)
def fetch_blobs(dest,oids,log):
 attempts=[]
 for attempt in range(3):
  p=subprocess.run(['git','-c','fetch.negotiationAlgorithm=noop','fetch','origin','--no-tags','--no-write-fetch-head','--recurse-submodules=no','--filter=blob:none','--stdin'],input=('\n'.join(sorted(set(oids)))+'\n').encode(),capture_output=True,cwd=dest)
  attempts.append(dict(attempt=attempt,returncode=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));save(log,attempts)
  if p.returncode==0:return
 raise AssertionError('Actual remote transport incomplete')
def readback():
 dest=Path('C:/hs/b570-mem-remote-readback-v1');assert not dest.exists();head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip()
 p=subprocess.run(['git','clone','--filter=blob:none','--depth','1','--single-branch','--branch',branch,'--no-checkout','https://github.com/leecdiang/HeteroSpec.git',str(dest)],capture_output=True)
 save(R/'REMOTE_CLONE.json',dict(returncode=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace')));assert p.returncode==0,p.stderr.decode(errors='replace')
 assert git('rev-parse','HEAD',cwd=dest).decode().strip()==head
 trees=git('ls-tree','-r',head,'benchmarks/b570_memory_followup_v1','artifacts/b570_memory_followup_v1',cwd=dest).decode().splitlines();fetch_blobs(dest,[s.split()[2] for s in trees],R/'REMOTE_FETCH.json');files=[]
 for s in trees:
  rel=s.split('\t')[1];b=git('show',head+':'+rel,cwd=dest);assert b==(REPO/rel).read_bytes()==git('show',head+':'+rel);p=dest/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b);files.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 save(R/'REMOTE_READBACK.json',dict(status='PASS',head=head,fresh_actual_remote_repository=str(dest),files=files,all_remote_git_blobs_equal_local_committed_and_working_bytes=True,archive_sha256=load(PUBLIC/'CAS_INDEX.json')['archive_sha256']))
 restore(dest,'C:/hs/b570-mem-remote-restored-v1',R/'REMOTE_RESTORE.json')
 for name in ['REMOTE_READBACK.json','REMOTE_RESTORE.json','REMOTE_CLONE.json','REMOTE_FETCH.json']:shutil.copyfile(R/name,PUBLIC/name)
 print('ACTUAL REMOTE DELIVERY RESTORE PASS',head,len(files),flush=True)
def final_readback():
 dest=Path('C:/hs/b570-mem-remote-readback-v1');head=git('rev-parse','HEAD').decode().strip();branch=git('branch','--show-current').decode().strip()
 p=subprocess.run(['git','fetch','origin',branch,'--depth','1','--filter=blob:none'],cwd=dest,capture_output=True);assert p.returncode==0,p.stderr.decode(errors='replace');assert git('rev-parse','FETCH_HEAD',cwd=dest).decode().strip()==head
 trees=git('ls-tree','-r',head,'benchmarks/b570_memory_followup_v1','artifacts/b570_memory_followup_v1',cwd=dest).decode().splitlines();fetch_blobs(dest,[s.split()[2] for s in trees],R/'FINAL_FETCH.json');files=[]
 for s in trees:
  rel=s.split('\t')[1];b=git('show',head+':'+rel,cwd=dest);assert b==(REPO/rel).read_bytes()==git('show',head+':'+rel);files.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
 receipt=dict(status='COMPLETE_BOUNDED_ENGINEERING_AND_EVIDENCE_DELIVERY',actual_final_head=head,actual_remote_git_blob_files_verified=len(files),all_files=files,archive_sha256=load(PUBLIC/'CAS_INDEX.json')['archive_sha256'],actual_fresh_remote_restore=load(R/'REMOTE_RESTORE.json'),qualified_gpu_feasibility=False,physical_residency='UNKNOWN',formal_requests=0,next_gpu_action='STOP_UNDER_CURRENT_PROTOCOL',final_metadata_readback_verified=True)
 save(R/'FINAL_DELIVERY.json',receipt);print('FINAL EXACT HEAD VERIFIED',head,len(files),flush=True)
if __name__=='__main__':
 if sys.argv[1]=='readback':readback()
 else:final_readback()
