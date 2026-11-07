"""CPU-only exact remote design/source recovery and engineering input binding."""
from common import *
import shutil,sys,urllib.request,re,os
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
 if x['id'].startswith('MBPP/') and len(rows)<6:rows.append({k:x[k] for k in ['id','raw_prompt','formatted_prompt','prompt_ids','cap']})
# PR83 exposed panel is HumanEval/MBPP, not PR87's MBPP/GSM grid. Freeze
# six already reserved/exposed GSM IDs prospectively, without reading outcomes.
dataset=R/'datasets/gsm8k-test.jsonl';dataset.parent.mkdir(exist_ok=True)
if not dataset.exists():
 revision='3101c7d5072418e28b9008a6636bde82a006892c'
 url=f'https://raw.githubusercontent.com/openai/grade-school-math/{revision}/grade_school_math/data/test.jsonl';b=urllib.request.urlopen(url).read();dataset.write_bytes(b);save(R/'DATASET_BINDINGS.json',dict(repository='openai/grade-school-math',revision=revision,url=url,sha256=sha(dataset),bytes=len(b),scope='full_corpus_availability_not_all_task_exposure'))
gsm=[json.loads(s) for s in dataset.read_text().splitlines()]
base_ids=load(REPO/'docs/experiments/b570_optimization_20261011/BASE_EXCLUSIONS.json')['excluded_ids']
for ident in sorted(x for x in base_ids if x.startswith('GSM8K/test/'))[:6]:
 question=gsm[int(ident.rsplit('/',1)[1])]['question'];rows.append(dict(id=ident,raw_prompt='Solve the following math problem. Show your reasoning and give the final answer.\n\n'+question,cap=128))
assert len(rows)==12 and sum(x['id'].startswith('MBPP/') for x in rows)==6 and sum(x['id'].startswith('GSM8K/') for x in rows)==6
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
skip={'.git','models','vendor','third_party','node_modules','datasets','build','candidate-build','tokenizer-build','candidate-src','candidate-common','archive','source-history','__pycache__','gguf','source-blobs'}
mechanical={'EXPOSURE_AUDIT.json','EXPOSURE_CATALOG.json','EXPOSURE_SUMMARY.json','E_EXPOSURE_AUDIT.json','E_EXPOSURE_CATALOG.json','INPUT_CANDIDATES.json','E_SELECTION.json','MANDATORY_EXCLUSIONS.json','HISTORY_AUDIT.json'}
roots=[Path('C:/hs'),Path('C:/Users/DIANG/Documents/ChatGPT/HeteroSpec'),Path('C:/Users/DIANG/.codex/worktrees')];catalog={};hits={};seen=set();errors=[];rx=re.compile(rb'\b(?:MBPP/\d+|GSM8K/test/\d+)\b')
for root in roots:
 for directory,dirs,files in os.walk(root):
  dirs[:]=[n for n in dirs if n not in skip and not n.startswith('.venv')]
  for name in files:
   p=Path(directory)/name
   if name in mechanical or p.suffix.lower() not in {'.json','.jsonl','.md','.txt','.csv','.log','.py','.tex','.yaml'}:continue
   if p.stat().st_size>128*1024*1024:continue
   if p.is_relative_to(R):continue
   try:b=p.read_bytes()
   except OSError as e:errors.append(dict(path=str(p),error=str(e)));continue
   h=hashlib.sha256(b).hexdigest();catalog[str(p)]=dict(sha256=h,bytes=len(b))
   if h in seen:continue
   seen.add(h)
   for m in rx.finditer(b):hits.setdefault(m.group().decode(),[]).append(str(p));reserved.add(m.group().decode())
assert not errors,errors
save(R/'HISTORY_CATALOG.json',catalog);save(R/'HISTORY_AUDIT.json',dict(status='PASS_ACCESSIBLE_ID_AUDIT',utc=now(),roots=list(map(str,roots)),files=len(catalog),unique_hashes=len(seen),hits=hits,excluded_ids=sorted(reserved),confirmation_selection='NOT_PERFORMED',RTX_remote_head='3733912e51f5e5543da019f28a0ac15178f111f3',limitations=['Not a global unseen or training-data claim. Exact description audit remains required at F0B before any held-out selection. No held-out cohort selected/read by experiment selector.']))
print('Design remote16 blobs, inherited307 source files and engineering12 binding PASS',flush=True)
