"""Independent normative audit. No imports from the executor/verifier comparison code."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,statistics,math,csv,zipfile,subprocess,collections
ROOT=Path(__file__).parent;BASE=Path('C:/hs/b570-closeout-v1');WORK=Path('C:/Users/DIANG/.codex/worktrees/b570-closeout-v1/HeteroSpec');DEST=WORK/'benchmarks/b570_closeout_overnight_v1'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def save(p,x):Path(p).write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
checks=0;errors=[]
def check(x,msg):
 global checks;checks+=1
 if not x:errors.append(msg)
def eq(a,b):return all(a[k]==b[k] for k in ['ids','eog','reason'])
freeze=load(BASE/'EXECUTION_FREEZE.json');protocol=load(BASE/'PROTOCOL.json');inputs=load(BASE/'INPUTS.json');eog=set(load(BASE/'TOKENIZATION_PROOF.json')['runtime_eog_ids']);byid={t['id']:t for v in inputs.values() for t in v}
check(sha(BASE/'PROTOCOL.json')==freeze['protocol_sha256'],'immutable protocol')
check(sha(BASE/'INPUTS.json')==freeze['inputs_sha256'],'immutable inputs')
for n,h in freeze['numerical_assets'].items():check(sha(BASE/n)==h,'numeric asset '+n)
git=lambda *args:subprocess.check_output(['git',*args],cwd=WORK,text=True).strip()
check(git('hash-object',str(DEST/'EXECUTION_PROMPT.md'))==git('rev-parse','aaa18acd2619dc8c0f91482b3308885d53bbf02e:benchmarks/b570_closeout_overnight_v1/EXECUTION_PROMPT.md'),'prompt original blob')
changed=git('diff','--name-only','e87291d26df32f2cb9571e005ab173b1c7a6830b','HEAD').splitlines();check(all(n.startswith('benchmarks/b570_closeout_overnight_v1/') for n in changed),'PR-only scoped changes')
ex=load(BASE/'EXPOSURE_AUDIT.json');ranked=sorted([r for r in ex['rows'] if not r['exclusions']],key=lambda r:(hashlib.sha256((r['id']+'HeteroSpec-B570-Closeout-Unused-v1').encode()).hexdigest(),r['id']))
check([r['id'] for r in ranked[:8]]==[r['id'] for r in inputs['unused']],'unused deterministic ranking')
check(not ({r['id'] for r in inputs['shared']} & {r['id'] for r in inputs['unused']}),'cohorts disjoint')
check([t['id'] for t in inputs['shared']]==['MBPP/'+n for n in '439,415,124,234,441,229,12,458,299,443,18,93,437,230,253,436,115,133,448,274,454,393,242,397'.split(',')],'shared frozen ordering')
records=[];seen=set();counts=collections.Counter();warm=collections.Counter();scientific_retries=[]
cutoff=datetime.fromisoformat(load(BASE/'CONTINUATION_AMENDMENT.json')['new_experiment_stop_utc'])
for p in (BASE/'raw').glob('*/RESULT.json'):
 r=load(p);u=r['unit_id'];stage=u.split('/')[0];check(u not in seen,'unique '+u);seen.add(u);records.append(r)
 (warm if r['warm'] else counts)[stage]+=1
 paths=r['files'];caps=[BASE/f for f in paths if f.endswith('/capture.json')];check(len(caps)==1,'one capture '+u)
 if len(caps)!=1:continue
 raw=load(caps[0]);ids=raw['ids'];flags=raw['eog'];cap=r['config'].get('cap',128)
 for name,h in paths.items():check(sha(BASE/name)==h,'raw SHA '+name)
 check(ids and len(ids)==len(flags) and all(type(t)==int and 0<=t<151936 for t in ids),'complete vocab '+u)
 check(flags==[t in eog for t in ids],'runtime EOG '+u)
 n=min(cap,next((i+1 for i,t in enumerate(ids) if t in eog),len(ids)))
 independently=dict(ids=ids[:n],eog=flags[:n],reason='EOG' if ids[n-1] in eog else 'CAP',raw_suffix=len(ids)-n)
 check(independently==r['endpoint'],'full endpoint '+u)
 m=load(str(caps[0])+'.metrics.json');check(m==r['metrics'] and m['request_id']==u and m['raw_count']==len(ids),'authentic metrics '+u)
 check(m['whole_request_ms']>=m['generation_ms']>0,'nested timers '+u)
 check(m['reset_target']['min']==m['reset_target']['max']==-1,'reset target '+u)
 if r['config']['native']:check(m['reset_draft']['min']==m['reset_draft']['max']==-1,'reset draft '+u)
 starts=[BASE/f for f in paths if f.endswith('/START.json')];st=load(starts[0]);check(st['unit_id']==u and st['config']==r['config'],'request frozen config '+u)
 check(datetime.fromisoformat(st['utc'])<cutoff,'within numerical cutoff '+u)
 if stage in ['B','C','C_ANCHOR_LONG','D_RESET','D_TIMING','E_CAPTURE','E_PILOT']:
  check(datetime.fromisoformat(st['utc'])>datetime.fromisoformat(freeze['utc']),'new input follows freeze '+u)
  check(raw['prompt_ids']==byid[r['task']]['prompt_ids'],'exact prompt '+u)
  check(r['source_commit'] in ['66b07015a83f4c0d772fce408da0ff3e34139065','64aa7a54ffc5668faf487342ffa6772a216619e3','cae1528f48b9fc46c1a3944a7f8a510bd0633c4f'],'approved inference epoch '+u)
  log=(BASE/'sessions'/r['session']/'stderr.log').read_text(encoding='utf-8',errors='replace');check('Intel(R) Arc(TM) B570 Graphics' in log and 'offloaded 37/37 layers to GPU' in log,'actual target GPU '+u)
  if r['config']['native']:check('offloaded 29/29 layers to GPU' in log,'actual draft GPU '+u)
 if raw['transfer']:
  t=raw['transfer'];check(t['source_unchanged'] and t['kv_equal'] and t['consumed_bytes']==t['state_bytes'] and t['before']==t['after']==t['source_after'],'actual state transfer '+u)
  check(t['pending_id']==ids[0] and t['seed']==t['clone_seed']==123 and t['sampler_chain']==t['clone_chain'] and t['sampler_history']==t['clone_history'],'post-sample pending clone '+u)
 valid_attempts=[]
 for a in p.parent.glob('attempt-*'):
  if (a/'INFRA_REJECTION.json').exists():continue
  if (a/'capture.json').exists() and (a/'capture.json.metrics.json').exists():valid_attempts.append(a)
 if len(valid_attempts)>1:scientific_retries.append(u)
check(not scientific_retries,'zero automatic reruns of complete valid science')
expected={'G0':144,'G0_BRIDGE':20,'B':512,'C':504,'C_ANCHOR_LONG':84,'D_RESET':96,'D_TIMING':96,'E_CAPTURE':6,'E_PILOT':144}
for stage,num in expected.items():
 check(counts[stage]==num,'complete count '+stage)
 schedule=load(BASE/(stage+'_SCHEDULE.json'))
 for si,s in enumerate(schedule):
  for ri,t in enumerate(s['inputs']):
   u=f'{stage}/{si}/{ri}/{t["id"]}';r=next((r for r in records if r['unit_id']==u),None)
   check(r is not None and r['config']==s['config'] and r['task']==t['id'] and not r['warm'],'exact scheduled unit '+u)
check(sum(counts[s] for s in ['G0','G0_BRIDGE','B','C','C_ANCHOR_LONG','D_RESET','D_TIMING'])==1456,'all finite core')
check(len(records)==1961 and sum(warm.values())==187,'all records and warm count')
# Independent reference qualification, retaining intentional N0 negatives.
b=[r for r in records if r['unit_id'].startswith('B/') and not r['warm']];bfails=[]
for task in inputs['shared']+inputs['unused']:
 rr=[r for r in b if r['task']==task['id'] and r['config']['label']=='R_reference'];check(len(rr)==4 and all(eq(r['endpoint'],rr[0]['endpoint']) for r in rr),'paid stable R '+task['id'])
 for label in ['T_matched','N0_ordinary','N1_repaired']:
  obs=[r for r in b if r['task']==task['id'] and r['config']['label']==label]
  check(len(obs)==4,'four repeats '+task['id']+label)
  for r in obs:
   if not eq(r['endpoint'],rr[0]['endpoint']):bfails.append(dict(task=task['id'],label=label,unit_id=r['unit_id']))
check(len(bfails)==8 and {x['task'] for x in bfails}=={'MBPP/72'} and {x['label'] for x in bfails}=={'T_matched','N1_repaired'},'authentic B boundary all repetitions')
for stage in ['C','C_ANCHOR_LONG']:
 rr=[r for r in records if r['unit_id'].startswith(stage+'/') and not r['warm']]
 for r in rr:
  refs=[q for q in rr if q['task']==r['task'] and q['config']['cap']==r['config']['cap'] and q['config']['label']=='R_reference'];check(refs and all(eq(r['endpoint'],q['endpoint']) for q in refs),'C/reference cross-width qualification '+r['unit_id'])
for stage in ['D_RESET','D_TIMING']:
 for r in [q for q in records if q['unit_id'].startswith(stage+'/') and not q['warm']]:
  ref=next(q for q in b if q['task']==r['task'] and q['config']['label']=='R_reference');check(eq(ref['endpoint'],r['endpoint']),'D shared reference '+r['unit_id']);check(r['config']['capture']==(stage=='D_RESET'),'capture/timing split '+r['unit_id'])
check(load(BASE/'E_DECISION.json')['status']=='NO_GO_PILOT','efficiency no-go')
check(load(BASE/'E_PLAN.json')['selected_fixed_ub']==2,'minimum C-qualified UB choice')
core=[r for r in records if not r['warm']]
# Every existing public cost row is independently recomputed from authentic metrics.
derived=0
for file in (BASE/'derived').glob('*.csv'):
 with file.open(encoding='utf-8-sig',newline='') as f:
  for row in csv.DictReader(f):
   group=[r for r in core if r['unit_id'].split('/')[0]==row['stage'] and r['task']==row['task'] and r['config'].get('cap',128)==int(row['cap']) and (not int(row['k']) or r['config'].get('width_k',0)==int(row['k']))]
   a=[r['metrics'][row['timer']] for r in group if r['config']['label']==row['baseline']];c=[r['metrics'][row['timer']] for r in group if r['config']['label']==row['candidate']]
   check(a and c,'cost denominator '+str(file.name)+row['task'])
   if a and c:
    av=statistics.median(a);cv=statistics.median(c);check(math.isclose(av,float(row['baseline_median_ms']),rel_tol=1e-12) and math.isclose(cv,float(row['candidate_median_ms']),rel_tol=1e-12) and math.isclose(av/cv,float(row['speed_ratio']),rel_tol=1e-12),'all raw cost fields '+str(file.name)+row['task'])
   derived+=1
shared={t['id'] for t in inputs['shared']}
def ratio(stage,a,c,timer):
 rr=[r for r in core if r['unit_id'].split('/')[0]==stage and r['task'] in shared];vals=[]
 for t in sorted(shared):vals.append(statistics.median(r['metrics'][timer] for r in rr if r['task']==t and r['config']['label']==a)/statistics.median(r['metrics'][timer] for r in rr if r['task']==t and r['config']['label']==c))
 return math.exp(statistics.mean(math.log(v) for v in vals))
costs={f'{stage}:{a}/{c}':{m:ratio(stage,a,c,m) for m in ['generation_ms','whole_request_ms']} for stage,a,c in [('B','N0_ordinary','N1_repaired'),('B','T_matched','N1_repaired'),('B','R_reference','N1_repaired'),('D_TIMING','T_matched','N1_repaired')]}
receipt=load(BASE/'ARCHIVE_RESTORE.json');check(sha(receipt['archive'])==receipt['archive_sha256'],'original immutable archive SHA')
with zipfile.ZipFile(receipt['archive']) as z:
 check(z.testzip() is None,'archive full CRC');index=json.loads(z.read('INDEX.json'));check(len(index['files'])==12906 and len(index['objects'])==9057,'archive denominators')
 for h,m in index['objects'].items():check(hashlib.sha256(z.read('objects/'+h)).hexdigest()==h,'archive object '+h)
 for name,m in index['files'].items():check(sha(Path(receipt['restore'])/name)==m['sha256'],'clean restored file '+name)
remote=load(BASE/'DELIVERY_VERIFIED.json');check(remote['head']=='bd5e3963757857f7ce5cd6a7a87bb04d6eb48d8d' and len(remote['files'])==179,'prior remote receipt')
for item in remote['files']:check(sha(WORK/item['path'])==item['sha256'],'179 prior delivered files still bound '+item['path'])
result=dict(status='PASS_WITH_REQUIRED_SUPPLEMENT' if not errors else 'FAIL',utc=datetime.now(timezone.utc).isoformat(),checks=checks,errors=errors,raw_records=len(records),core_nonwarm=1456,all_nonwarm=sum(counts.values()),warm=sum(warm.values()),counts=dict(counts),warm_counts=dict(warm),B_failures=bfails,derived_cost_rows_recomputed=derived,costs=costs,original_archive_reverified=receipt['archive_sha256'],original_prompt_blob='d99dae9d78282c44de4900fdf18947a57f4ef7eb',findings=[dict(id='A1',severity='REQUIRED_SUPPLEMENT',finding='C-only mechanism selector does not cover available B/E scientific failures; existing GATED_BY_QUALIFICATION only describes C.',remedy='Timestamped post-outcome bounded natural parent supplement, fixed two E failure pairs by original width/cap/task ordering. Preserve original selection receipt and negatives.'),dict(id='A2',severity='LIMITATION',finding='No mid-trajectory crossed target/draft/sampler donors; observer cannot certify opaque sampler bytes or unique kernel cause.',remedy='Prompt expressly permits NOT_CAUSALLY_IDENTIFIED with authentic traces/logits; no causal claim.'),dict(id='A3',severity='LIMITATION',finding='Exact internal runtime synchronization count and B570 board power unavailable; graph count is not dispatch count.',remedy='Keep missing fields and do not claim energy/kernel causality. Final real synchronization is inside timers.'),dict(id='A4',severity='DISCLOSED_DEVIATION',finding='Original budget missed owing to interruptions; user authorized continuation, pause/resume and CPU finalization. Warm counts exceed planned where sessions restarted.',remedy='Original deadlines preserved, no failure-driven task trimming, actual warm/infrastructure denominators retained.')])
save(ROOT/'CORE_REVIEW.json',result);print({k:result[k] for k in ['status','checks','errors','derived_cost_rows_recomputed','costs']},flush=True)
assert not errors,errors[:20]
