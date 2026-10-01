#!/usr/bin/env python3
"""Deterministic manuscript projection from retained arrays and native paired records."""
import argparse,collections,csv,hashlib,json,math,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];E=ROOT/'paper/mlsys2027/evidence';H=ROOT/'paper/mlsys2027/manuscript'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def array_sha(a):return hashlib.sha256(json.dumps(a,separators=(',',':')).encode()).hexdigest()
def diff(a,b):return next((i for i in range(max(len(a),len(b))) if i>=len(a) or i>=len(b) or a[i]!=b[i]),None)
def endpoint(ids,eog):
 n=min(128,next((i+1 for i,v in enumerate(eog) if v),len(ids)));assert n==128 or eog[n-1];return ids[:n]
def quantile(v,q):
 v=sorted(v);pos=(len(v)-1)*q;lo=int(pos);hi=math.ceil(pos);return v[lo]+(v[hi]-v[lo])*(pos-lo)
def project(work):
 projection={};source_inputs={}
 def source(p):
  source_inputs[p]={'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size};return read(ROOT/p)
 b=work/'b570-fork/artifacts/b570_partition_intervention_v1/raw/reserved';rows=[]
 for p in sorted(b.glob('*/capture.json')):
  c=read(p);record=read(p.parent/'record.json');a=endpoint(c['primary_ids'],c['primary_eog']);z=endpoint(c['alternate_ids'],c['alternate_eog']);cp=c['checkpoint'];idx=cp['output_index']
  alt=[d for d in c['alternate_decisions'] if d['fork_first_block']];native={d['output_index']:d for d in c['decisions']};paired=[]
  for j,t in enumerate(alt):
   n=native[idx+j]
   if n['batch_index']!=j:break
   assert n['proposal_id']==t['proposal_id'];paired.append({'native':n,'alternate':t})
   if n['committed_id']!=t['committed_id'] or n['accepted_proposal']!=t['accepted_proposal'] or not n['accepted_proposal'] or n['eog']:break
  rows.append({'task_id':record['task_id'],'repetition':record['repetition'],'checkpoint_output_index':idx,'primary_ids':a,'alternate_ids':z,'primary_array_sha256':array_sha(a),'alternate_array_sha256':array_sha(z),'primary_scores':c['primary_scores'],'alternate_scores':c['alternate_scores'],'paired_decisions':paired,'first_trajectory_divergence':diff(a,z),'state':{k:cp[k] for k in ['position','source_ubatch','alternate_ubatch','n_batch','state_bytes','consumed_bytes','serialized_kv_equal','source_unchanged','sampler_chain','clone_chain','sampler_seed','clone_seed','sampler_history','clone_history']}})
 counts={}
 predicates={'score':lambda x:x['primary_scores']!=x['alternate_scores'],'raw_top1':lambda x:any(a['raw_top1_id']!=b['raw_top1_id'] for a,b in zip(x['primary_scores'],x['alternate_scores'])),'immediate':lambda x:any(y['native']['committed_id']!=y['alternate']['committed_id'] or y['native']['accepted_proposal']!=y['alternate']['accepted_proposal'] for y in x['paired_decisions']),'continuation':lambda x:x['primary_ids']!=x['alternate_ids']}
 for n,f in predicates.items():counts[n]={'executions':sum(f(x) for x in rows),'prompts':len({x['task_id'] for x in rows if f(x)})}
 counts['paired_decision_events']=sum(len(x['paired_decisions']) for x in rows)
 published=source('benchmarks/b570_partition_intervention_v1/ENDPOINT_ANALYSIS.json');v=source('benchmarks/b570_partition_intervention_v1/INDEPENDENT_VALIDATION.json')
 for ours,theirs in [('score','score_record_difference'),('raw_top1','raw_top1_difference'),('immediate','immediate_decision_difference'),('continuation','downstream_trajectory_difference')]:assert counts[ours]==published['counts'][theirs]
 assert counts['paired_decision_events']==v['paired_decision_event_count'];assert len(rows)==72
 projection['B570_live_intervention']={'rows':rows,'counts':counts,'endpoint_lengths':dict(collections.Counter(len(x['primary_ids']) for x in rows)),'distinct_prompts':24,'repetitions':3}
 h2=work/'rtx-h2/evidence';records=read(h2/'pre-live/records.json')['runs']+read(h2/'live/records.json')['runs'];by={(r['task_id'],r['repetition'],r['condition']):r for r in records};pred=source('benchmarks/rtx_independent_proposal_replay_v2/RESERVED_PREDICTIONS.json');rows=[]
 for p in pred['rows']:
  t,rep=p['task_id'],p['repetition'];conditions=['REFERENCE_UB1','H2_P_R','R_ONLY','RTX_BATCHED_K2'];arrays={c:by[t,rep,c]['generated_ids'] for c in conditions}
  for c in conditions[:3]:assert arrays[c]==p['runs'][c]['generated_ids'] and array_sha(arrays[c])==p['runs'][c]['array_sha256']
  rows.append({'task_id':t,'repetition':rep,'arrays':arrays,'array_sha256':{c:array_sha(a) for c,a in arrays.items()},'termination':{c:by[t,rep,c]['termination'] for c in conditions},'reference_first_divergence':diff(arrays['REFERENCE_UB1'],arrays['RTX_BATCHED_K2'])})
 pairs={name:sum(x['arrays'][a]==x['arrays'][b] for x in rows) for name,a,b in [('H2_live','H2_P_R','RTX_BATCHED_K2'),('R_ONLY_live','R_ONLY','RTX_BATCHED_K2'),('H2_R_ONLY','H2_P_R','R_ONLY'),('reference_live','REFERENCE_UB1','RTX_BATCHED_K2')]};report=source('benchmarks/rtx_independent_proposal_replay_v2/FORMAL_REPORT.json')
 assert all(n==report['pairs'][k]['exact_pairs'] for k,n in pairs.items())
 endpoints={c:{'earlier_EOG_runs':sum(x['termination'][c]=='EOS' for x in rows),'cap_runs':sum(x['termination'][c]=='limit' for x in rows),'distinct_EOG_prompts':len({x['task_id'] for x in rows if x['termination'][c]=='EOS'}),'distinct_cap_prompts':len({x['task_id'] for x in rows if x['termination'][c]=='limit'})} for c in conditions}
 divergences=[{'task_id':x['task_id'],'index':x['reference_first_divergence'],'reference_id':x['arrays']['REFERENCE_UB1'][x['reference_first_divergence']],'live_id':x['arrays']['RTX_BATCHED_K2'][x['reference_first_divergence']]} for x in rows if x['repetition']==1 and x['reference_first_divergence'] is not None]
 projection['RTX_H2']={'rows':rows,'pairs':pairs,'endpoints':endpoints,'divergent_prompts':divergences,'distinct_prompts':24,'repetitions':3,'formal_executions':288}
 records=read(work/'rtx-latency/formal/records.json')['runs'];published=source('benchmarks/rtx_transfer_latency_v1/latency/REPORT.json');p=source('benchmarks/rtx_transfer_latency_v1/protocol.json');by={(r['task_id'],r['repetition'],r['condition']):r for r in records};prompt_rows=[];run_rows=[]
 for t in p['latency']['task_ids']:
  a=statistics.median(by[t,r,'TARGET_REFERENCE']['timer']['milliseconds'] for r in (1,2,3));b=statistics.median(by[t,r,'RTX_SERIALIZED_K2']['timer']['milliseconds'] for r in (1,2,3));prompt_rows.append({'task_id':t,'reference_median_ms':a,'serialized_median_ms':b,'ratio':a/b})
  for rep in (1,2,3):
   assert by[t,rep,'TARGET_REFERENCE']['generated_ids']==by[t,rep,'RTX_SERIALIZED_K2']['generated_ids']
   for c in ('TARGET_REFERENCE','RTX_SERIALIZED_K2'):
    r=by[t,rep,c];run_rows.append({'task_id':t,'repetition':rep,'condition':c,'milliseconds':r['timer']['milliseconds'],'generated_ids':r['generated_ids'],'termination':r['termination']})
 assert prompt_rows==published['per_prompt'];csv_rows=list(csv.DictReader((ROOT/'benchmarks/rtx_transfer_latency_v1/latency/PROMPT_MEDIANS.csv').open()))
 for a,b in zip(prompt_rows,csv_rows):assert a['task_id']==b['task_id'] and all(float(b[k])==a[k] for k in ('reference_median_ms','serialized_median_ms','ratio'))
 logs=[math.log(x['ratio']) for x in prompt_rows];gm=math.exp(math.fsum(logs)/30);rng=random.Random(2026093002);boot=[math.exp(math.fsum(logs[rng.randrange(30)] for _ in range(30))/30) for _ in range(10000)];ci=[quantile(boot,q) for q in (.025,.975)];assert abs(gm-published['speedup'])<1e-14 and all(abs(a-b)<1e-14 for a,b in zip(ci,published['bootstrap_95_ci']))
 projection['RTX_matched_latency']={'prompt_rows':prompt_rows,'run_rows':run_rows,'ratio':published['speedup'],'ci95':published['bootstrap_95_ci'],'independent_ratio':gm,'independent_ci95':ci,'absolute_tolerance':1e-14,'exact_pairs':90,'formal_executions':180,'distinct_prompts':30,'repetitions':3,'faster_prompts':sum(x['ratio']>1 for x in prompt_rows),'bootstrap_seed':2026093002,'bootstrap_resamples':10000}
 records=read(work/'rtx-prediction/discovery_H1/records.json')['runs'];by={(r['task_id'],r['repetition'],r['condition']):r for r in records};conditions=sorted({r['condition'] for r in records});rows=[]
 for t,rep in sorted({(r['task_id'],r['repetition']) for r in records}):rows.append({'task_id':t,'repetition':rep,'arrays':{c:by[t,rep,c]['generated_ids'] for c in conditions}})
 source('benchmarks/rtx_transfer_latency_v1/prediction/REPORT.json');projection['RTX_H1_discovery']={'rows':rows,'conditions':conditions,'exact_pairs':sum(x['arrays'][conditions[0]]==x['arrays'][conditions[1]] for x in rows),'total_pairs':36,'distinct_prompts':12,'reserved_executions':0,'selected_hypothesis':None}
 source('benchmarks/b570_partition_intervention_v1/FORMAL_FREEZE.json');source('benchmarks/rtx_independent_proposal_replay_v2/protocol.json')
 for folder,names in [('b570_partition_intervention_v1',['BUILD_IDENTITY.json','EXPOSURE_AUDIT.json','RESERVED_SET.json']),('rtx_independent_proposal_replay_v2',['BUILD_IDENTITY.json','EFFECTIVE_CONFIGURATION.json','EXPOSURE_AUDIT.json','RESERVED_SET.json','F0_MANIFEST.json','F1_MANIFEST.json','F2_MANIFEST.json','F0_REMOTE_RECEIPT.json','F1_REMOTE_RECEIPT.json','F2_REMOTE_RECEIPT.json']),('rtx_transfer_latency_v1',['runtime_freeze.json','timer_build_manifest.json','asset_identity.json','environment.json'])]:
  for n in names:source('benchmarks/'+folder+'/'+n)
 out={'schema':'evidence_projection_v085','studies':projection,'canonical_inputs':source_inputs,'archive_replay_report_sha256':sha(E/'ARCHIVE_REPLAY_V085_QA.json')};(E/'FOLLOWUP_PROJECTION_V085.json').write_text(json.dumps(out,indent=2)+'\n')
 macros={'FUCost':f'{gm:.3f}','FUCostLo':f'{ci[0]:.3f}','FUCostHi':f'{ci[1]:.3f}','FUForkScores':str(counts['score']['executions']),'FUForkImmediate':str(counts['immediate']['executions']),'FUForkLater':str(counts['continuation']['executions']),'FUForkLaterPrompts':str(counts['continuation']['prompts']),'FUForkEvents':str(counts['paired_decision_events'])}
 (H/'tables/followup_values_v085.tex').write_text('% New campaign projection; historical macros remain unchanged.\n'+''.join('\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in macros.items()))
 print(json.dumps({'status':'RERUN_PASS','B570':counts,'RTX_H2':pairs,'RTX_latency':{'ratio':gm,'ci':ci},'RTX_H1':projection['RTX_H1_discovery']['exact_pairs']}))
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);a=p.parse_args();project(a.work.resolve())
