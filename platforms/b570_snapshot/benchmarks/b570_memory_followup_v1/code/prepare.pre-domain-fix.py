"""CPU-only exact remote design/source recovery and engineering input binding."""
from common import *
import shutil,sys
HEAD='ab9dc1f935618931c3779f46a95f3b056b707457'
remote=Path('C:/hs/b570-mem-plan-readback-v1')
if not remote.exists():
 subprocess.run(['git','clone','--filter=blob:none','--depth','1','--single-branch','--branch','codex/b570-memory-followup-20261011','--no-checkout','https://github.com/leecdiang/HeteroSpec.git',str(remote)],check=True)
assert git('rev-parse','HEAD',cwd=remote).decode().strip()==HEAD,'Live design head changed'
paths=git('diff-tree','--no-commit-id','--name-only','-r',HEAD,cwd=REPO).decode().splitlines()
# Both commits' complete new directories, not just the last commit's delta.
paths=git('ls-tree','-r','--name-only',HEAD,'docs/experiments/b570_memory_followup_20261011','scripts/platform/b570_memory_followup_v1',cwd=REPO).decode().splitlines()
rows=[]
for rel in paths:
 b=git('show',HEAD+':'+rel,cwd=remote);local=git('show',HEAD+':'+rel);assert b==local== (REPO/rel).read_bytes(),rel
 rows.append(dict(path=rel,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),git_blob=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()))
save(R/'PLAN_REMOTE_READBACK.json',dict(status='PASS',utc=now(),actual_remote_head=HEAD,files=rows,forward_calls=0,fresh_remote_repository=str(remote)))
for name in ['test_audit.py','audit.py']:
 cmd=[sys.executable,str(REPO/'scripts/platform/b570_memory_followup_v1'/name)]
 p=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8');assert p.returncode==0,p.stderr;save(R/('STATIC_'+name+'.json'),dict(status='PASS',stdout=p.stdout,stderr=p.stderr,scope='STATIC_NO_RUNTIME_APPROVAL'))
prior=Path('C:/hs/b570-opt-remote-restored-v1');old=Path('C:/hs/b570-opt-pr82-restored-v1');bound=load(old/'SOURCE_BINDINGS.json')
for rel,m in bound.items():assert sha(old/rel)==m['sha256'] and (old/rel).stat().st_size==m['bytes']
save(R/'INHERITED_RECHECK.json',dict(status='PASS',utc=now(),source_files=len(bound),PR82_restore=load('C:/hs/b570-opt-run-v1/PR82_RESTORE.json'),PR86_final=load('C:/hs/b570-opt-run-v1/FINAL_DELIVERY.json'),PR86_actual_restoration=load('C:/hs/b570-opt-run-v1/REMOTE_RESTORE.json') if Path('C:/hs/b570-opt-run-v1/REMOTE_RESTORE.json').exists() else load('C:/hs/b570-opt-v1/benchmarks/b570_optimization_v1/REMOTE_READBACK.json'),historical_loads=11,historical_forwards=0,upstream_numeric_commit='NOT_CERTIFIED'))
source=load(DOC/'SOURCE_BINDINGS.json');blobs=[]
for x in source['copied_historical_logs']+source['reviewed_sources']:
 b=git('show',x['source_head']+':'+x['source_path']);assert hashlib.sha256(b).hexdigest()==x['sha256'] and len(b)==x['bytes'];p=R/'source-blobs'/(x['sha256']+'.blob');p.parent.mkdir(exist_ok=True);p.write_bytes(b);blobs.append(dict(**x))
oldbind=load('C:/hs/b570-opt-run-v1/PLAN_SOURCE_VERIFICATION.json')['source_blobs']
for x in oldbind:
 b=Path(x['local_path']).read_bytes();assert hashlib.sha256(b).hexdigest()==x['sha256'];p=R/'source-blobs'/(x['sha256']+'.blob');p.write_bytes(b)
save(R/'SOURCE_RECHECK.json',dict(status='PASS',fixed_new_source_blobs=blobs,inherited_source_blobs=oldbind,forward_calls=0))
eng=next(x for x in oldbind if x['path'].endswith('/ENGINEERING_INPUTS.json'));data=load(R/'source-blobs'/(eng['sha256']+'.blob'))['families']['Llama'];assert len(data)==12
# Inputs are deliberately exposed engineering tasks. RTX confirmation is never input to a selector.
rows=[]
for x in data:
 rows.append({k:x[k] for k in ['id','raw_prompt','formatted_prompt','prompt_ids','cap']});assert len(x['prompt_ids'])<=768 and x['cap']==128
assert sum(x['id'].startswith('MBPP/') for x in rows)==6 and sum(x['id'].startswith('GSM8K/') for x in rows)==6
save(R/'ENGINEERING_INPUTS.json',rows)
reserved=set(load(REPO/'docs/experiments/b570_optimization_20261011/BASE_EXCLUSIONS.json')['excluded_ids'])
def ids(x):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in ['id','task_id'] and isinstance(v,str) and (v.startswith('MBPP/') or v.startswith('GSM8K/')):reserved.add(v)
   else:ids(v)
 elif isinstance(x,list):
  for v in x:ids(v)
for x in oldbind:
 if '/CONFIRMATION_INPUTS.json' in x['path'] or '/ENGINEERING_INPUTS.json' in x['path']:ids(load(R/'source-blobs'/(x['sha256']+'.blob')))
for x in rows:reserved.add(x['id'])
save(R/'MANDATORY_EXCLUSIONS.json',dict(status='MINIMUM_PLUS_FULL_BOUND_RTX_INPUT_POOLS',ids=sorted(reserved),fresh_confirmation_selected=False,selector_read_confirmation_data=False))
print('Design remote16 blobs, inherited307 source files and engineering12 binding PASS',flush=True)
