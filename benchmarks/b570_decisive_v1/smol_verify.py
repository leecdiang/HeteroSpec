"""Independent old-R jobs and value comparisons for the fixed Smol cohort."""
from smol_campaign import *

def input_row(group,index):
 p=read(SROOT/'cohort/PANEL.json')[group][index]
 return read(SROOT/'cohort/INPUTS.json')[p['id']]

def captures(group,index,arm,mode):
 prefix='dev' if group=='development' else 'test'
 return SROOT/EPOCH/'runs'/f'{prefix}-{index}-{arm}-{mode}'

def pack_states(folder):
 for p in sorted(folder.glob('*.json.states/*.bin')):pack(p)

def state_equal(x,y):
 if x['prefix']!=y['prefix']:return False
 return canonical_verified(x['sequence'])==canonical_verified(y['sequence']) and native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes()

def old_reference(group,index):
 r=input_row(group,index);name=('dev' if group=='development' else 'test')+'-'+str(index)+'-oldR'
 return execute(name,'M',[r,r],heavy=True,original=True)

def plan(group,index):
 r=input_row(group,index);prompt=r['prompt_ids'];vectors=set();states=set()
 for arm in ARMS:
  a=read(captures(group,index,arm,'heavy')/'1.json');b=read(captures(group,index,arm,'off')/'1.json')
  assert a['ids']==b['ids'] and a['eog']==b['eog']
  assert state_equal(a['committed_states'][-1],b['committed_states'][-1]),(group,index,arm,'heavy/OFF state')
  vectors.update(tuple(x['prefix']) for x in a['full_target_vectors']);states.update(tuple(x['prefix']) for x in a['committed_states'])
 maximum=[]
 for p in sorted(vectors|states,key=lambda x:(-len(x),x)):
  assert p[:len(prompt)]==tuple(prompt)
  if not any(q[:len(p)]==p for q in maximum):maximum.append(p)
 # Greedy canonical path first, then other branches. Each state is requested once.
 m=read(captures(group,index,'M','heavy')/'1.json');canonical=tuple(prompt+m['ids'][:-1]);maximum.sort(key=lambda p:(-sum(p[:j]==canonical[:j] for j in range(len(prompt),min(len(p),len(canonical))+1)),-len(p),p))
 covered=set();jobs=[];prefix='dev' if group=='development' else 'test'
 for j,p in enumerate(maximum):
  wanted=sorted(s for s in states-covered if p[:len(s)]==s);covered.update(wanted)
  jobs.append(dict(prompt_ids=prompt,forced_suffix=list(p[len(prompt):]),state_prefixes=[list(x) for x in wanted]))
 assert covered==states
 path=SROOT/EPOCH/f'{prefix}-{index}-FORCED_PLAN.json'
 write(path,dict(input_id=r['id'],root_id=r['root_id'],independent_token_only_jobs=jobs,conditional_prefixes=len(vectors),state_prefixes=len(states),candidate_values_received=False));return path

def forced_run(group,index):
 prefix='dev' if group=='development' else 'test';p=read(SROOT/EPOCH/f'{prefix}-{index}-FORCED_PLAN.json')
 for j,r in enumerate(p['independent_token_only_jobs']):
  execute(f'{prefix}-{index}-forced-{j}','M',[r],heavy=True,forced=True)

def check(group,index,save=True):
 from smol_boundaries import verify as verify_boundaries
 prefix='dev' if group=='development' else 'test';r=input_row(group,index)
 oldfolder=SROOT/EPOCH/'runs'/f'{prefix}-{index}-oldR';old=read(oldfolder/'0.json');repeat=read(oldfolder/'1.json')
 assert old==repeat,'natural original R stability'
 m=read(captures(group,index,'M','heavy')/'1.json')
 assert (old['prompt_ids'],old['ids'],old['eog'],old['commits'])==(m['prompt_ids'],m['ids'],m['eog'],m['commits']),'old R/observer bridge'
 bank={};duplicates=0
 jobs=read(SROOT/EPOCH/f'{prefix}-{index}-FORCED_PLAN.json')['independent_token_only_jobs']
 for j in range(len(jobs)):
  data=read(SROOT/EPOCH/'runs'/f'{prefix}-{index}-forced-{j}'/'0.json')
  assert data['candidate_values_received'] is False
  for x in data['prefixes']:
   k=tuple(x['prefix'])
   if k in bank:
    assert native_path(x['frontier']).read_bytes()==native_path(bank[k]['frontier']).read_bytes(),'original forced instability';duplicates+=1
   if k not in bank or 'sequence' in x:bank[k]=x
 results=[]
 for arm in ARMS:
  a=read(captures(group,index,arm,'heavy')/'1.json');b=read(captures(group,index,arm,'off')/'1.json')
  verify_boundaries(a,old,arm)
  endpoint=(a['ids'],a['eog'])==(old['ids'],old['eog'])==(b['ids'],b['eog'])
  vals=[];states=[]
  for x in a['full_target_vectors']:
   raw=native_path(x['path']).read_bytes();assert len(raw)==49152*4 and np.isfinite(np.frombuffer(raw,dtype='<f4')).all()
   vals.append(raw==native_path(bank[tuple(x['prefix'])]['frontier']).read_bytes())
  for x in a['committed_states']:states.append(state_equal(x,bank[tuple(x['prefix'])]))
  bridge=state_equal(a['committed_states'][-1],b['committed_states'][-1])
  hist={}
  for t in a['trace']:
   if t['event']=='decode' and t['phase']=='prefill' and t['role']=='draft':
    key=str(t['caller_batch_length']);hist[key]=hist.get(key,0)+1
    assert t['ub_capacity']==(1 if arm=='H1' else int(arm[3]))
  if arm!='M':
   traces=[t for t in a['trace'] if t['event']=='decode' and t['phase']=='prefill' and t['role']=='draft']
   assert sum(t['caller_batch_length'] for t in traces)==len(r['prompt_ids'])
   assert sum(sum(t['logits_requested']) for t in traces)==1
   assert all(t['caller_batch_length'] in (1,2,4) for t in traces) if arm!='H1' else max(t['caller_batch_length'] for t in traces)<=512
  results.append(dict(arm=arm,endpoint_equal=endpoint,conditional_vectors=len(vals),vectors_equal=sum(vals),committed_states=len(states),states_equal=sum(states),heavy_off_final_equal=bridge,draft_caller_histogram=hist,natural_stop='EOG' if old['eog'][-1] else 'CAP128',raw_suffix=len(a['ids'])-len(old['ids']),accepted=sum(x['accepted'] for x in a['commits']),natural_corrections=sum(x['relationship']=='correct' for x in a['commits'])))
 good=all(x['endpoint_equal'] and x['conditional_vectors']==x['vectors_equal'] and x['committed_states']==x['states_equal'] and x['heavy_off_final_equal'] for x in results)
 report=dict(status='FINITE_NATIVE_CAPTURE_MATCH' if good else 'NUMERICAL_MISMATCH',input_id=r['id'],root_id=r['root_id'],original_R_repeated_and_stable=True,old_R_full_vectors_available=False,autonomous_R_never_received_candidate_tapes=True,independent_forced_paths=len(jobs),duplicate_reference_prefixes_checked=duplicates,arms=results)
 if save:write(SROOT/EPOCH/f'{prefix}-{index}-QUALIFICATION.json',report);print(prefix,index,report['status'],flush=True)
 assert good,report
 return report

if __name__=='__main__':
 action,group,index=sys.argv[1],sys.argv[2],int(sys.argv[3]);{'old':old_reference,'plan':plan,'forced':forced_run,'check':check}[action](group,index)
