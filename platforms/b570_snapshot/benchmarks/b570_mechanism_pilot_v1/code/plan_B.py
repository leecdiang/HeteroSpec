from pathlib import Path
import json,hashlib,subprocess
from datetime import datetime,timezone
R=Path(__file__).parent;G='C:/Users/DIANG/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert load(R/'A_VERIFICATION.json')['status']=='PASS'
records=[load(p) for p in (R/'raw').glob('*/RESULT.json') if load(p)['unit_id'].startswith('A/') and not load(p)['warm']]
hist=load(R/'HISTORICAL_PARENTS.json');cases=[]
for task in ['HumanEval/145','HumanEval/42','MBPP/72']:
 labels=['N1_repaired','N0_ordinary' if task=='MBPP/72' else 'E_k1_ub2']
 for rep in [1,2]:
  parents=[next(r for r in records if r['task']==task and r['config']['label']==label and r['config']['round']==rep) for label in labels]
  cps=[]
  for parent in parents:
   cps.append([(f,load(R/f)) for f in parent['files'] if f.endswith('.json') and '.cp-' in f])
  bad=parents[0] if task=='MBPP/72' else parents[1];ref=hist[task+'/R_reference']['endpoint']['ids'];out=bad['endpoint']['ids']
  divergence=next((i for i,(a,b) in enumerate(zip(ref,out)) if a!=b),min(len(ref),len(out)))
  aligned=[]
  for f,a in cps[0]:
   for g,b in cps[1]:
    keys=['prompt_ids','ids','eog','pending','n_predict','n_past_tgt','n_past_dft','target_position','has_eos']
    if all(a[k]==b[k] for k in keys) and a['n_predict']<=divergence and a['ids']==ref[:a['n_predict']] and a['pending']==-1 and not a['has_eos']:aligned.append((a['n_predict'],f,g,a,b))
  if not aligned:cases.append(dict(task=task,round=rep,status='UNALIGNED',retained_divergence=divergence));continue
  selected=sorted(aligned,key=lambda x:(-x[0],x[1],x[2]))[0];n,f,g,a,b=selected
  # Frozen second donor's already-generated online caller, never a future tape.
  batch=b['batch_target'];recipes=[dict(label=label,ub=j['ub'],outputs_max=j['outputs_max'],outputs_max_per_seq=j['outputs_max_per_seq']) for label,j in zip(labels,[a,b])]
  focus=min(divergence-n,len(batch)-1);batch_prefix_reference_aligned=all(row['id']==ref[n-1+i] for i,row in enumerate(batch[:focus+1]))
  donors=[dict(label=label,checkpoint=p,checkpoint_sha256=sha(R/p),parent_unit=r['unit_id'],parent_raw=next(x for x in r['files'] if x.endswith('/capture.json')),config=r['config'],all_checkpoint_files={x:h for x,h in r['files'].items() if x.startswith(p[:-5]+'.')}) for label,p,r in zip(labels,[f,g],parents)]
  cases.append(dict(task=task,round=rep,status='ALIGNED',retained_divergence=divergence,committed_length=n,common_prefix=a['ids'],pending=-1,logical_position=a['n_past_tgt'],target_position=a['target_position'],batch=batch,batch_source=g,primary_row=focus,primary_batch_prefix_reference_aligned=batch_prefix_reference_aligned,primary_row_rule='closest to retained divergence within the actual frozen common batch; all rows reported; parent-trajectory correspondence is not assumed',donors=donors,recipes=recipes,intervention='complete current recipe including reservation; /72 identical continuation recipes control',selection='nearest pre-divergent genuinely recoverable aligned boundary; no logit/margin/speed selection',sampler_scope='actual accepted-history effective greedy restore then real clone; opaque bytes/RNG cursor unavailable'))
manifest=dict(utc=datetime.now(timezone.utc).isoformat(),cases=cases,shams_max=12,forwards_max=24,extra_warm_sham_max=12,cross_warm_forwards=0,classification='score factors: exact full-row equality; argmax factors separately; both independent task shams needed; /72 identical current recipe reported as state contrast only',stop='ordinary scientific sham failure blocks causal validity, no rerun; continue other frozen cases within budget')
(R/'B_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
freeze=dict(utc=manifest['utc'],sources={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in list((R/'src').glob('*'))+[R/'plan_B.py',R/'run_B.py',R/'B_MANIFEST.json',R/'validate_A.py',R/'validate_B.py']},binaries={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in (R/'build/Release').glob('*') if p.suffix in ['.exe','.dll']},A_freeze_sha256=sha(R/'A_FREEZE.json'),A_verification_sha256=sha(R/'A_VERIFICATION.json'),native_target_unchanged=True,cross_only_observation_change='sample every saved current row with actual effective greedy sampler clones; zero added forwards; before B outputs')
(R/'B_FREEZE.json').write_text(json.dumps(freeze,indent=2)+'\n',encoding='utf8')
subprocess.run([G,'add','.'],cwd=R,check=True);subprocess.run([G,'commit','-m','Freeze natural donor alignment and whole current recipe cross/sham units'],cwd=R,check=True)
print([(c['task'],c['round'],c['status'],c.get('committed_length')) for c in cases],flush=True)
