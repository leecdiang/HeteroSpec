#!/usr/bin/env python3
"""Independent synthetic trace, path-coverage, typed-mutation and byte-read checks."""
import argparse,pathlib,sys,tempfile,copy,json,hashlib,collections
p=argparse.ArgumentParser();p.add_argument('--audit-dir',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();sys.dont_write_bytecode=True;sys.path.insert(0,str(a.audit_dir.resolve()))
import replay_audit as A, test_replay_audit as T

def need(x,m):
 if not x:raise RuntimeError(m)
BASE=copy.deepcopy(T.ID);P=[1,2,3]

def trace(cap,pattern,eog):
 h=P.copy();pending=T.pick(h);out=[pending];cycles=[];query_tokens={tuple(h)};states=[tuple(h)]
 def done():return len(out)==cap or out[-1] in eog
 while not done():
  base=len(h);seed=pending;v=[seed];props=[];r=pattern[len(cycles)%len(pattern)]
  for j in range(3):
   t=T.pick(h+v)
   if j==r:t=(t+1)%16
   props.append(t);v.append(t)
  dec=[T.pick(h+v[:j+1]) for j in range(4)]
  query_tokens.update(tuple(h+v[:j+1]) for j in range(4))
  accepted=0;last=None
  for j in range(3):
   if done():break
   if props[j]==dec[j]:accepted+=1;t=props[j];last='accepted'
   else:t=dec[j];pending=t;last='correction'
   out.append(t)
   if last=='correction':break
  if accepted==3 and not done():pending=dec[3];out.append(pending);last='bonus'
  h+=v[:accepted+1];states.append(tuple(h))
  cycles.append({'base':base,'seed':seed,'proposals':props,'decisions':dec,'accepted':accepted,'last':last,'keep':len(h),'pending':None if done() else pending})
 return {'ids':out,'cycles':cycles,'cap':cap,'target_ubatch':1,'capture_schema':'native-target-v1','forced_reject_index':-1,'stop_after_output_index':0},query_tokens,states

def check_paths(plan,query_tokens,states):
 qs={q['query_id']:q for q in plan['queries']}
 need({tuple(q['tokens']) for q in qs.values()}==query_tokens,'missing actual/off-greedy prefix')
 need([tuple(x['tokens']) for x in plan['commits']]==states,'wrong per-commit path')
 owned=[k for j in plan['fresh_replay_jobs'] for k in j['query_ids']]
 need(len(owned)==len(set(owned))==len(qs) and set(owned)==set(qs),'ownership not exact once')
 for j in plan['fresh_replay_jobs']:
  path=tuple(j['tokens']);need(path in query_tokens,'job is not a query leaf')
  need(not any(len(x)>len(path) and x[:len(path)]==path for x in query_tokens),'nonmaximal leaf')
  closure={key for key,q in qs.items() if path[:len(q['tokens'])]==tuple(q['tokens'])}
  need(set(j['available_query_ids'])==closure,'wrong ancestor closure')
  need(set(j['query_ids'])<=closure,'owner does not contain query')

def evidence(root,c,identity):
 T.ID=identity
 plan,e=T.bundle(root,c)
 for q in plan['queries']:
  e['reference_queries'][q['query_id']].update(A.reference_metadata(q['tokens'],len(P),identity))
 for j in plan['fresh_replay_jobs']:
  e['reference_jobs'][j['job_id']]['execution']=A.reference_metadata(j['tokens'],len(P),identity)
  e['reference_jobs'][j['job_id']]['observations']={qid:copy.deepcopy(e['reference_queries'][qid]) for qid in j['query_ids']}
 f=e['free_scalar_run'];md=A.reference_metadata(f['decoded_tokens'],len(P),identity)
 for key in ('caller_widths','physical_ubatches','logits_masks'):f[key]=md[key]
 f['eog_flags']=[t in identity['eog_ids'] for t in c['ids']];f['stop_contract']['eog_ids']=identity['eog_ids'];f['stop_reason']='EOG' if f['eog_flags'][-1] else 'CAP'
 return plan,e

root=pathlib.Path(tempfile.mkdtemp(prefix='independent-replay-check-'))
patterns=[(0,),(1,),(2,),(3,),(0,3,1,2),(3,2,1,0)];passed=0;eog_cases=0;branches=collections.Counter()
for recipe in ('tokenwise_all','historical_prefill_then_scalar'):
 for pattern in patterns:
  for cap in range(1,18):
   for eog in ([],[0,5]):
    identity=copy.deepcopy(BASE);identity.update(reference_recipe=recipe,eog_ids=eog)
    identity['tokenizer_sha256']=A.digest({'artificial_vocab':16,'eog':eog})
    c,queries,states=trace(cap,pattern,eog);plan,e=evidence(root,c,identity);check_paths(plan,queries,states)
    report=A.audit(plan,e,root,identity);need(report['status']=='RECORDED_EVIDENCE_MATCH' and report['gpu_qualification_established'] is False,'wrong scope/status')
    passed+=1;eog_cases+=int(c['ids'][-1] in eog);branches.update(x['last'] for x in c['cycles'])
T.ID=copy.deepcopy(BASE);plan,e=T.bundle(root,T.case(0,5));identity=BASE
first_job=lambda x:next(iter(x['reference_jobs'].values()))
obs=lambda x:next(iter(first_job(x)['observations'].values()))
mutations={
 'observation_wrong_tokens':lambda x:obs(x).__setitem__('decoded_tokens',[15]),
 'observation_wrong_positions':lambda x:obs(x).__setitem__('positions',[99]),
 'observation_not_fresh':lambda x:obs(x).__setitem__('fresh_context',False),
 'observation_wrong_sequence':lambda x:obs(x).__setitem__('sequence_id',9),
 'observation_wrong_callers':lambda x:obs(x).__setitem__('caller_widths',[64]),
 'observation_wrong_physical':lambda x:obs(x).__setitem__('physical_ubatches',[4]),
 'job_wrong_mask':lambda x:first_job(x)['execution'].__setitem__('logits_masks',[[False]]),
 'job_not_empty':lambda x:first_job(x).__setitem__('start_empty',False),
 'candidate_wrong_mask':lambda x:x['candidate_rows']['initial']['producer'].__setitem__('logits_mask',[False]*3),
 'candidate_wrong_row':lambda x:x['candidate_rows']['cycle-0-row-0']['producer'].__setitem__('captured_batch_row',3),
 'candidate_wrong_output_index':lambda x:x['candidate_rows']['cycle-0-row-0']['producer'].__setitem__('captured_output_index',3),
 'candidate_wrong_positions':lambda x:x['candidate_rows']['initial']['producer'].__setitem__('positions',[9,10,11]),
 'candidate_wrong_tokens':lambda x:x['candidate_rows']['initial']['producer'].__setitem__('tokens',[9,10,11]),
 'numeric_mask':lambda x:x['candidate_rows']['initial']['producer'].__setitem__('logits_mask',[0,0,1]),
 'boolean_widths':lambda x:next(iter(x['reference_queries'].values())).__setitem__('physical_ubatches',[True]*3),
 'float_commit_positions':lambda x:x['candidate_commits']['initial'].__setitem__('positions',[0.,1.,2.]),
 'integer_commit_done':lambda x:x['candidate_commits']['cycle-3'].__setitem__('done',1),
 'erased_pending_output':lambda x:x['candidate_commits']['cycle-3'].__setitem__('unmaterialized_output',[]),
 'free_wrong_mask':lambda x:x['free_scalar_run'].__setitem__('logits_masks',[[False]]),
 'free_teacher_forced':lambda x:x['free_scalar_run'].__setitem__('forced_tokens_used',True),
 'missing_unexamined_row':lambda x:x['candidate_rows'].pop('cycle-0-row-3'),
 'missing_reference_job':lambda x:x['reference_jobs'].pop(next(iter(x['reference_jobs']))),
 'missing_required_observation':lambda x:first_job(x)['observations'].pop(next(iter(first_job(x)['observations']))),
 'path_escape':lambda x:x['candidate_rows']['initial']['logits'].__setitem__('path','../outside.bin'),
}
rejected={}
for name,mutate in mutations.items():
 bad=copy.deepcopy(e);mutate(bad)
 try:A.audit(plan,bad,root,identity)
 except A.EvidenceError as ex:rejected[name]=str(ex)
 else:raise RuntimeError('invalid evidence admitted: '+name)
actual=[];old=A.blob
try:
 def counted(*args):
  b=old(*args);actual.append(len(b));return b
 A.blob=counted;report=A.audit(plan,e,root,identity)
finally:A.blob=old
need(report['payload_bytes_read']==sum(actual) and report['payload_read_calls']==len(actual),'byte accounting differs')
# Check concrete budget trajectories independently using token identities with a large vocabulary.
resources=[]
for mode in ('all_accept','reject_j0'):
 prompt=list(range(512));history=prompt.copy();queries={tuple(history)};commits=[len(history)];out=1;cycles=0
 while out<128:
  seed=1000+cycles;props=[2000+cycles*3+j for j in range(3)];v=[seed]+props
  queries.update(tuple(history+v[:j+1]) for j in range(4))
  accepted=min(3,128-out) if mode=='all_accept' else 0
  out+=accepted if mode=='all_accept' and 128-out<=3 else accepted+1
  history+=v[:1+accepted];commits.append(len(history));cycles+=1
 leaves=[q for q in queries if not any(len(r)>len(q) and r[:len(q)]==q for r in queries)]
 resources.append({'mode':mode,'queries':len(queries),'cycles':cycles,'naive_token_evaluations':sum(map(len,queries)),'fresh_maximal_jobs':len(leaves),'maximal_path_token_evaluations':sum(map(len,leaves)),'independent_free_run_token_evaluations':639,'sum_committed_prefix_lengths':sum(commits)})
result={'scope':'Synthetic offline consistency checks, not native runtime/GPU qualification','auditor_sha256':hashlib.sha256(pathlib.Path(A.__file__).read_bytes()).hexdigest(),'valid_mixed_branch_recipe_eog_cases':passed,'cases_terminated_by_eog':eog_cases,'observed_cycle_branches':dict(branches),'mutation_rejections':rejected,'byte_accounting':{'reported':report['payload_bytes_read'],'observed':sum(actual),'calls':len(actual)},'resources':resources,'status':'PASS'}
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in result.items() if k!='mutation_rejections'},indent=2))
