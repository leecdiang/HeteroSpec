from pathlib import Path
import json,shutil,hashlib,subprocess
R=Path(__file__).parent
O=Path('C:/hs/b570-closeout-v1')
W=Path('C:/Users/DIANG/.codex/worktrees/b570-mechanism-pilot-v1/HeteroSpec')
G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def save(n,x):
 p=R/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def sha(p):return hashlib.file_digest(Path(p).open('rb'),'sha256').hexdigest()
for n in ['src','raw','sessions','dependencies','derived','archive','build']: (R/n).mkdir(exist_ok=True)
shutil.copyfile('C:/Users/DIANG/Downloads/HeteroSpec_B570_Mechanism_Pilot_Prompt_v1.md',R/'EXECUTION_PROMPT.md')
for n in ['native.cpp','target.cpp','observer.h','CMakeLists.txt']:shutil.copyfile(O/'src'/n,R/'src'/n)
for n in ['INPUTS.json','TOKENIZATION_PROOF.json','EXPOSURE_AUDIT.json']:shutil.copyfile(O/n,R/'dependencies'/n)
shutil.copyfile(O/'dependencies/B570/HISTORICAL_EXPECTED.json',R/'dependencies/HISTORICAL_EXPECTED.json')
cfg=R/'src/CMakeLists.txt';t=cfg.read_text().replace('b570-closeout','b570-pilot');cfg.write_text(t,encoding='utf8')
shutil.copyfile(O/'runner.py',R/'runner.py')
t=(R/'runner.py').read_text();t=t.replace('b570-closeout','b570-pilot')
t=t.replace("def stopped():\n", "def legacy_stopped_unused():\n")
pos=t.index('class Session:')
t=t[:pos]+"def stopped():return (ROOT/'STOP').exists()\n"+t[pos:]
t=t.replace("req={'request_id':unit,'prompt_ids':inp['prompt_ids'],'output':str(attempt/'capture.json')}","req={'request_id':unit,'prompt_ids':inp['prompt_ids'],'output':str(attempt/'capture.json'),'task':inp['id']}\n  if not warm and inp.get('checkpoint_window'):req['checkpoint_window']=inp['checkpoint_window']\n  if inp.get('resume'):req['resume']=inp['resume']")
t=t.replace("for p in attempt.iterdir() if p.is_file()","for p in attempt.rglob('*') if p.is_file()")
t=t.replace("stopped():raise RuntimeError('Cutoff", "stopped():raise RuntimeError('Manual STOP")
t=t.replace("datetime.now(timezone.utc)>=datetime.fromisoformat(s['new_experiment_stop_utc'])", "False")
t=t.replace("def acquire():", "def acquire():")
# No expired cutoff, no execution-state or other machine-policy changes.
t=t.replace(" ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)", "")
t=t.replace(" ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)", "")
# Count attempts BEFORE send including warm, failed and interrupted units.
t=t.replace("  event('REQUEST_START',unit_id=unit,session=self.name,warm=warm)","  events=[json.loads(s) for s in (ROOT/'LEDGER.jsonl').read_text().splitlines()] if (ROOT/'LEDGER.jsonl').exists() else []\n  count=sum(e.get('event')=='REQUEST_START' and e.get('warm')==warm for e in events)\n  if count>=(48 if warm else 312):raise RuntimeError('Request budget exhausted')\n  event('REQUEST_START',unit_id=unit,session=self.name,warm=warm)")
t=t.replace("  observed=(self.dir/'stderr.log').read_text", "  observed=(self.dir/'stderr.log').read_text")
t=t.replace("  self.load_seconds=time.monotonic()-start", "  if 'offloaded 37/37 layers to GPU' not in observed or (native and 'offloaded 29/29 layers to GPU' not in observed):\n   self.close();raise RuntimeError('Incomplete actual GPU offload')\n  self.load_seconds=time.monotonic()-start")
(R/'runner.py').write_text(t,encoding='utf8')
inputs=json.loads((O/'INPUTS.json').read_text());pref=json.loads(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json').read_text())
ids=['HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/134','HumanEval/58','MBPP/72']
dev=[]
for id in ids:
 if id in pref:
  i=pref[id];x={'id':id,'prompt_ids':json.loads(Path(i['ids']).read_text()),'formatted_prompt':Path(i['text']).read_text(encoding='utf8')}
 else:x=next(t for v in inputs.values() for t in v if t['id']==id)
 x=dict(x,exposure='previously exposed',cap=128)
 dev.append(x)
save('DEV_INPUTS.json',dev)
base=[dict(label='R_reference',native=False,prefill=128,ub=128,plain=True),dict(label='N1_repaired',native=True,k=2,prefill=128,ub=1),dict(label='E_k1_ub2',native=True,k=1,prefill=128,ub=2),dict(label='ordinary',native=True,k=1,prefill=2,ub=2,plain=True)]
schedule=[]
for rep in [0,1]:
 for b in base:
  # ordinary MBPP/72 is a separate session with the authentic N0 sham framework.
  groups=[dev] if b['label']!='ordinary' else [dev[:5],dev[5:]]
  for group in groups:
   c=dict(b,capture=rep==0,cap=128,round=rep+1)
   if b['label']=='ordinary':
    if group[0]['id']=='MBPP/72':c.update(label='N0_ordinary',k=2,prefill=1,ub=1);c.pop('plain')
    else:c['label']='M_ordinary_same_k1_ub2'
   ts=[]
   for d in group:
    d=dict(d)
    if c['label'] in ['N1_repaired','E_k1_ub2','N0_ordinary'] and d['id'] in ['HumanEval/42','HumanEval/145','MBPP/72']:
     boundary={'HumanEval/42':73,'HumanEval/145':56,'MBPP/72':41}[d['id']]
     # Up to 17 genuine pre-forward boundaries; no outcome-dependent capture selection.
     d['checkpoint_window']=[boundary-16,boundary]
    ts.append(d)
   schedule.append({'config':c,'inputs':ts})
save('A_SCHEDULE.json',schedule)
save('PROTOCOL.json',dict(schema='heterospec.b570.mechanism.pilot.v1',prior_head='66594b349955e66146702325559c26019ea16485',main='e87291d26df32f2cb9571e005ab173b1c7a6830b',hardware='Intel Arc B570',contract=dict(ctx=1024,batch=512,threads=10,batch_threads=10,flash_attention='off',seed=123,temp=0,cap=128,sequence=0),limits=dict(generation=312,auxiliary_target_forward=24,warm=48),gates=dict(A='all available historical complete endpoints and raw arrays plus capture switch stable; retain failures',B='nearest common true pre-divergent checkpoint; both own-path full raw shams; 2 tasks minimum',C='one evidence-derived task-independent family; six-task complete R arrays including MBPP72',D='112/112 complete endpoints',E='all complete qualification; R/candidate gen GM>=1.05 whole>=1.03 both rounds faster'),checkpoint_window='retained divergence minus16 through divergence inclusive; natural target preverification only',cross_batch_donor='E for HumanEval; N0 for MBPP; already-online original batch',no_hidden_forwards=True,no_scientific_retries=True))
save('SOURCE_BINDINGS.json',dict(main='e87291d26df32f2cb9571e005ab173b1c7a6830b',PR63='66594b349955e66146702325559c26019ea16485',pinned_source='C:/hs/b570-direct-id-v1-src',pinned_build='C:/hs/b570-direct-id-v1-build',prior_source={n:sha(O/'src'/n) for n in ['native.cpp','target.cpp','observer.h','CMakeLists.txt']},prompt_sha256=sha(R/'EXECUTION_PROMPT.md')))
save('UNIT_MANIFEST.json',dict(A=[f'A/{si}/{ri}/{i["id"]}' for si,s in enumerate(schedule) for ri,i in enumerate(s['inputs'])],B=dict(cases=['HumanEval/145','HumanEval/42','MBPP/72'],rounds=2,shams_max=12,aux_forwards_max=24),C=12,D=112,E=128))
save('BUDGET.json',dict(generation_max=312,target_forward_max=24,warm_max=48,started_generation=0,started_forward=0,started_warm=0,policy='count all sent requests, including infrastructure failure and interruption; at most one explicit infrastructure recovery'))
save('STATUS.json',dict(stage='STAGE0_AND_BUILD',generation_complete=0,ETA='CPU verification/build about 10-20min; StageA approx15-30min, conditional later stages 1-3h, update from actual timing; no arbitrary cutoff'))
(R/'LEDGER.jsonl').touch()
(R/'.gitattributes').write_text('* -text\n',encoding='utf8')
(R/'.gitignore').write_text('build/\nraw/\nsessions/\narchive/\n__pycache__/\nLOCK*\nSTOP\n*.tmp\n',encoding='utf8')
(R/'RUNBOOK.md').write_text('# B570 finite pilot\n\nRun `python resume.py`. Manual STOP: create `STOP` in this private study root. Existing complete hashed units are read, never regenerated. Only owned PID plus creation identity may be managed. No time cutoff. One GPU process at a time. Stage0 and freeze must pass before A. B and subsequent stages require documented gates and separate source/input commits. New study only; do not merge any PR. Bulk state stays in content-addressed local archive with external runtime hashes.\n',encoding='utf8')
subprocess.run([G,'init'],cwd=R,check=True)
for key in ['user.name','user.email']:
 v=subprocess.check_output([G,'config',key],cwd=O,text=True).strip();subprocess.run([G,'config',key,v],cwd=R,check=True)
subprocess.run([G,'config','core.autocrlf','false'],cwd=R,check=True)
subprocess.run([G,'switch','-c','codex/b570-mechanism-pilot-v1'],cwd=W,check=True)
print('BOOTSTRAP COMPLETE',flush=True)
