"""FP64 same-prefix four-cell score analysis. Never executes a model."""
from __future__ import annotations
import argparse,collections,csv,json
from pathlib import Path
import numpy as np
from contracts import *
from plan_frontier import old_index

def rank(z,token):return int(np.count_nonzero(z>z[token])+np.count_nonzero((z==z[token])&(np.arange(z.size)<token))+1)
def four_cell(vectors,r,u):
 require(len(vectors)==4 and all(z.shape==(V,) and np.isfinite(z).all() for z in vectors),'four complete finite vocabulary vectors required')
 zz=[z.astype(np.float64) for z in vectors];de,dk,dv,db=[float(z[u]-z[r]) for z in zz];res=zz[3]-zz[1]-zz[2]+zz[0]
 return {'d_EMPTY':de,'d_first':dk,'d_second':dv,'d_joint':db,'delta_first':dk-de,'delta_second':dv-de,'I':db-dk-dv+de,'I_from_vector_pair':float(res[u]-res[r]),'vector_I_Linf':float(np.max(np.abs(res))),'vector_I_RMS':float(np.sqrt(np.mean(res*res,dtype=np.float64))),'vector_I_L2':float(np.linalg.norm(res)),'vector_I_exact_nonzero_elements':int(np.count_nonzero(res))},res

def same_prefix(proofs,prefix,t):
 require(len(proofs)==4 and all(p['prefix']==prefix[:t] for p in proofs),'different token prefixes; no four-cell comparison allowed')
def analyze(plan,old_audit,fresh,new_run,outdir):
 idx=old_index(old_audit);oldres=Resolver(fresh,old_audit['resolver_original_prefix']);source='NEW_INDEPENDENT_FRONTIER_BATCH' if new_run is not None else 'PR103_HISTORICAL_BATCH';records={};errors=[]
 if new_run is not None:
  res=Resolver(new_run,new_run);receipts=[];validate_new_plan(plan);planned={s['slot']:s for s in plan['requests']};f0=read(new_run/'F0.json');commit=read(new_run/'F0_AUTHENTICATED.json')['commit']
  for path in sorted((new_run/'receipts').glob('*.json')):
   r=read(path);receipts.append(r)
   if r['status']!='COMPLETED':errors.append({'slot':r['slot']['slot'],'error':r.get('error'),'status':r['status']});continue
   require(r['slot']['slot'] in planned,'unknown attempted slot');s=planned[r['slot']['slot']];key=(s['task'],s['recipient'],s['state'],s['mode'],s['repeat']);require(key not in records,'duplicate new slot');records[key]=validate_new_receipt(r,s,new_run,f0,commit)
 else:
  res=oldres
  for c in plan['cells']:
   for old in idx[(c['task'],c['recipient'],c['state'])]:records[(c['task'],c['recipient'],c['state'],'heavy',old['repeat'])]=(oldres.record_file(old['raw_path'],old['raw_sha256']),old,c)
 rows=[];drift=[];missing=[];outdir.mkdir(parents=True,exist_ok=True);vector_dir=outdir/'vectors';vector_dir.mkdir(exist_ok=True)
 for p in plan['panels']:
  arms=p['arms'];task,recipient=p['task'],p['recipient'];pair_rules={}
  for t in p['positions']:
   if p['t_star'] is not None:pair_rules[t]=(p['r'],p['u'])
   else:
    item=records.get((task,recipient,'EMPTY','heavy',0))
    if item is None:missing.append({'task':task,'recipient':recipient,'panel':p['panel'],'t':t,'reason':'EMPTY_REPEAT0_NOT_AVAILABLE'});continue
    x,rec,c=item;initial=dict(c['initial_logits_spec'])
    z,proof=logits_at(x,t,res,initial)
    if z is None:missing.append({'task':task,'recipient':recipient,'panel':p['panel'],'t':t,'reason':'EMPTY_REPEAT0_MISSING_FULL_LOGITS'});continue
    r,u=top2(z);pair_rules[t]=(r,u)
   zr_by_rep=[]
   for repeat in (0,1):
    vectors=[];proofs=[];ok=True
    for arm in arms:
     item=records.get((task,recipient,arm,'heavy',repeat))
     if item is None:missing.append({'task':task,'recipient':recipient,'panel':p['panel'],'state':arm,'repeat':repeat,'t':t,'reason':'NEW_REPEAT_NOT_COMPLETED' if new_run else 'OLD_REPEAT_NOT_AVAILABLE'});ok=False;continue
     x,rec,c=item;initial=c['initial_logits_spec'];z,proof=logits_at(x,t,res,initial)
     if z is None:missing.append({'task':task,'recipient':recipient,'panel':p['panel'],'state':arm,'repeat':repeat,'t':t,'reason':'MISSING_FULL_LOGITS'});ok=False;continue
     vectors.append(z);proofs.append(proof)
    if not ok:continue
    same_prefix(proofs,p['common_prefix_ids'],t);r,u=pair_rules[t];numbers,residual=four_cell(vectors,r,u);empty=vectors[0].astype(np.float64);a,b=top2(vectors[0]);margin=float(empty[a]-empty[b]);per_arm=[]
    for arm,z,proof in zip(arms,vectors,proofs):
     zz=z.astype(np.float64);aa,bb=top2(z);eps=float(np.max(np.abs(zz-empty)));per_arm.append({'state':arm,'FP32_sha256':proof['sha256'],'r_score':float(zz[r]),'u_score':float(zz[u]),'d':float(zz[u]-zz[r]),'true_argmax':aa,'true_top2':bb,'argmax_is_third_candidate':aa not in (r,u),'r_rank':rank(zz,r),'u_rank':rank(zz,u),'epsilon_Linf_vs_EMPTY':eps,'RMS_vs_EMPTY':float(np.sqrt(np.mean((zz-empty)**2,dtype=np.float64))),'EMPTY_m_gt_2epsilon':margin>2*eps,'observed_top1_unchanged':aa==a,'source_proof':proof})
    name=task.replace('/','_')+'-'+recipient+'-'+p['panel']+'-t'+str(t)+'-r'+str(repeat)+'.residual.f64';vp=vector_dir/name;residual.astype('<f8').tofile(vp)
    row={'task':task,'recipient':recipient,'direction':('B' if recipient=='A' else 'A')+'->'+recipient,'panel':p['panel'],'panel_status':p['status'],'t':t,'t_star':p['t_star'],'repeat':repeat,'same_prefix_verified':True,'prefix_ids':proofs[0]['prefix'],'r':r,'u':u,'token_pair_rule':p['token_pair_rule'],'EMPTY_true_top1':a,'EMPTY_true_top2':b,'EMPTY_top1_margin':margin,'arithmetic':'FP64 over complete FP32 source vectors','source_batch':source,'arms':per_arm,**numbers,'vector_residual':{'path':'vectors/'+name,'bytes':vp.stat().st_size,'sha256':sha(vp),'dtype':'little-endian float64','vocabulary':V}}
    if p['panel']=='L0':row.update(delta_K=numbers['delta_first'],delta_V=numbers['delta_second'],I_KV=numbers['I'])
    else:row.update(delta_prefix=numbers['delta_first'],delta_tail=numbers['delta_second'],I_pos=numbers['I'])
    rows.append(row);zr_by_rep.append((repeat,vectors,numbers))
   if len(zr_by_rep)==2:
    first,second=zr_by_rep
    drift.append({'task':task,'recipient':recipient,'panel':p['panel'],'t':t,'r':pair_rules[t][0],'u':pair_rules[t][1],'all_FP32_vectors_bitwise_equal':all(np.array_equal(a.view(np.uint32),b.view(np.uint32)) for a,b in zip(first[1],second[1])),'arm_vector_Linf_drift':{s:float(np.max(np.abs(b.astype(np.float64)-a.astype(np.float64)))) for s,a,b in zip(arms,first[1],second[1])},'I_repeat1_minus_repeat0':second[2]['I']-first[2]['I']})
 accounting={'native_request_starts':0,'native_process_starts':0,'attempted_slots':0,'owned_native_process_seconds':0.,'target_forward_decode_calls':0,'target_successful_micrographs':0,'target_micrograph_rows':0}
 if new_run:
  led=[json.loads(s) for s in (new_run/'LEDGER.jsonl').read_text().splitlines()] if (new_run/'LEDGER.jsonl').exists() else [];accounting.update(native_request_starts=sum(x['event']=='REQUEST_STARTED' for x in led),native_process_starts=sum(x['event']=='OWNED_PID' for x in led),attempted_slots=sum(x['event']=='ATTEMPT_STARTED' for x in led),owned_native_process_seconds=sum(x['owned_seconds'] for x in led if x['event']=='WORKER_CLOSED'))
  emitted={}
  for q in (new_run/'raw').rglob('stdout.jsonl'):
   for line in q.read_text(encoding='utf8').splitlines():
    x=json.loads(line)
    if x.get('event')=='RESULT':emitted[(x['pid'],x['request_id'])]=x
  for q in (new_run/'raw').rglob('*.RESULT.json'):
   x=read(q);key=(x['pid'],x['request_id']);require(key not in emitted or emitted[key]==x,'persisted raw differs from emitted native RESULT');emitted[key]=x
  for x in emitted.values():
   accounting['target_forward_decode_calls']+=x['target_decode_calls'];accounting['target_successful_micrographs']+=x['workload']['target_micrographs'];accounting['target_micrograph_rows']+=x['workload']['target_micrograph_rows']
  request_pids={x['pid'] for x in led if x['event']=='REQUEST_PID'};result_pids={key[0] for key in emitted};accounting['processes_with_started_request_but_no_complete_RESULT']=sorted(request_pids-result_pids);accounting['partial_forward_counts_scope']='UNKNOWN_IF_REQUEST_PROCESS_HAS_NO_COMPLETE_RESULT; no zero imputation'
  accounting['native_process_create_attempts']=sum(x['event']=='NATIVE_PROCESS_START_ATTEMPT' for x in led)
  accounting['load_attempts_without_request_start']=accounting['attempted_slots']-accounting['native_request_starts']
 expected_count=sum(len(p['positions'])*2 for p in plan['panels']);complete=len(rows)==expected_count and not errors and not missing and (new_run is None or len(records)==len(plan['requests']))
 result={'schema':1,'status':'COMPLETE' if complete else 'INCOMPLETE','scope':'exposed fixed inputs; position selection retrospective; no population success rate/CI','source_batch':source,'source_FP32_precision':'complete native FP32 vector; FP64 analysis; no arbitrary epsilon','old_audit_counts':old_audit['counts'],'old_audit_quartet_1248_B_to_A':old_audit['quartet_1248_B_to_A'],'accounting':accounting,'panels':[{k:v for k,v in p.items() if k!='old_availability'} for p in plan['panels']],'rows':rows,'repeat_drift':drift,'failures':errors,'missing':missing,'expected_four_cell_comparisons':expected_count,'projection_complete_mediation':'NOT_ESTABLISHED','state_natural_reachability':'NOT_ESTABLISHED','unique_kernel':'NOT_ESTABLISHED','independent_machine_recomputation':'NOT_PERFORMED','remote_raw_availability':'REMOTE_PENDING','paid_latency_or_speedup':'NOT_MEASURED'}
 write(outdir/'FRONTIER_ANALYSIS.json',result)
 fields=['task','recipient','direction','panel','t','t_star','repeat','r','u','EMPTY_top1_margin','delta_first','delta_second','I','vector_I_Linf','vector_I_RMS','vector_I_exact_nonzero_elements','same_prefix_verified','source_batch']
 with (outdir/'FRONTIER_ANALYSIS.csv').open('w',newline='',encoding='utf8') as f:w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
 return result
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--audit',type=Path,required=True);ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--new-run',type=Path);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();r=analyze(read(a.plan),read(a.audit),a.fresh,a.new_run,a.out);print(json.dumps({'status':r['status'],'comparisons':len(r['rows']),'missing':len(r['missing']),'failures':r['failures'],'accounting':r['accounting']},indent=2))
