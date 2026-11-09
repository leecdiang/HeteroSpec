"""Data-only closed-run cost/statistical replay; never starts native work.

Use a fresh destination after terminal export. Excludes unrelated host records
and private numerical/model payloads. A public hash replay is not a fresh GPU
numerical qualification. Failed requests retain their full reservations.
"""
from pathlib import Path
from collections import Counter,defaultdict
import argparse,hashlib,json,math,re,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);p.add_argument('--export',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--epoch',choices=['07','08'],required=True);a=p.parse_args();r,w=a.root,a.work
 assert read(w/f'PIPELINE_COORDINATOR_CLOSED{a.epoch}.private.json')['no_more_native_admissions']
 assert read(a.export/'EXPORT_COMPLETE.json')['passed']and read(a.export/'LOCAL_READBACK.json')['passed']
 before=sha(w/'ledger.jsonl');a.out.mkdir();began=time.monotonic()
 def public(x):
  s=json.dumps(x,ensure_ascii=False);s=s.replace(str(r),'$HS_ROOT').replace(str(Path.home()),'$HOME')
  s=re.sub(r'/home/[A-Za-z0-9_.-]+','$HOME_USER',s);s=re.sub(r'GPU-[a-fA-F0-9-]{8,}','<allocated-or-redacted-GPU>',s);s=re.sub(r'\b192\.168(?:\.\d{1,3}){1,2}\b','<private-network>',s)
  assert not re.search(r'/home/[a-z]|GPU-[a-fA-F0-9]{8}|192\.168\.\d',s)
  return json.loads(s)
 def save(name,x):(a.out/name).write_text(json.dumps(public(x),indent=2,ensure_ascii=False)+'\n')
 ledger=[json.loads(s)for s in(w/'ledger.jsonl').read_text().splitlines()];reserved=[x for x in ledger if x['event']=='RESERVE'];inherited=read(w/'INHERITED_ACCOUNTING.json')
 counters=dict(requests=inherited['requests']+sum(x['requests']for x in reserved),reserved_rows=inherited['rows']+sum(x['rows']for x in reserved));assert counters['requests']<=512 and counters['reserved_rows']<=2000000
 costs=[];by_epoch=defaultdict(lambda:dict(requests=0,reserved_rows=0,complete=0,failed_or_incomplete=0,known_native_worker_wall_s=0.0,known_host_wrapper_wall_s=0.0))
 for x in reserved:
  out=Path(x['out']);epoch=str(out.relative_to(w)).split('/')[0];entry=by_epoch[epoch];entry['requests']+=x['requests'];entry['reserved_rows']+=x['rows'];host=read(out/'HOST.json')if(out/'HOST.json').exists()else{}
  entry['complete'if host.get('status')=='COMPLETE'else'failed_or_incomplete']+=1
  for k in ('worker_wall_s','wrapper_wall_s'):
   if host.get(k)is not None:entry['known_native_worker_wall_s'if k=='worker_wall_s'else'known_host_wrapper_wall_s']+=host[k]
  native=read(out/'native/result.json')if(out/'native/result.json').exists()else{}
  receipts=[]
  for request in native.get('requests',[]):
   q=out/'native'/request['record']
   if q.exists():
    v=read(q);receipts.append(dict(name=request['name'],capture=v['capture'],service_s=v['service_seconds'],setup_s=v.get('setup_seconds'),request_s=v.get('request_seconds'),teardown_s=v.get('teardown_seconds'),target_physical_width_hist=v['target_physical_width_hist'],draft_physical_width_hist=v['draft_physical_width_hist'],receipt_sha256=sha(q)))
  gpu_free=[]
  if(out/'resources.jsonl').exists():
   for line in(out/'resources.jsonl').read_text().splitlines():
    sample=json.loads(line);gpu_free.append(float(sample['gpu']['memory.free']))
  costs.append(dict(out=str(out.relative_to(w)),phase=x['phase'],requests=x['requests'],reserved_rows=x['rows'],host=host,model_load_s=native.get('model_load_s'),pool_setup_s=native.get('pool_setup_s'),actual_native_token_rows=native.get('token_rows'),minimum_sampled_free_GPU_MiB=min(gpu_free)if gpu_free else None,receipts=receipts))
 commands=[]
 for d in sorted(r.glob('q32-q4-full-build-*'))+sorted(r.glob('q32-q4-full-operands-build-*')):
  if not d.is_dir():continue
  for q in d.rglob('command.json'):
   x=read(q);commands.append(dict(path=str(q.relative_to(r)),sha256=sha(q),record=x))
 save('FULL_COSTS.json',dict(cumulative=counters,request_ceiling=512,row_ceiling=2000000,inherited=inherited,by_epoch=dict(by_epoch),worker_records=costs,build_command_records=commands,build_cost_note='Command walls may overlap across the two allowed build tasks; not CPU core-seconds or GPU kernel time',sampling_note='Native worker wall includes native SHA/load/context, warmups, requests, serialization and exit; host wrapper starts after host SHA admission. Caller-cost records in the full text archive include earlier host SHA. Two-second samples cannot exclude all brief interference.',known_cooperative_GPU_lock_wrapper_wall_s=sum(x['host'].get('wrapper_wall_s')or 0 for x in costs),known_native_worker_wall_s=sum(x['host'].get('worker_wall_s')or 0 for x in costs),not_measured=['GPU kernel/energy grand total','CPU core-seconds','missing or pre-inheritance wall times'],no_refunds=True,prior_8B_ledger_unchanged=True))
 failures=[]
 for q in sorted(p for p in w.rglob('*.json')if 'failure'in p.name.lower()):
  if any(z.startswith(('export-','delivery-'))for z in q.relative_to(w).parts):continue
  control=w/q.relative_to(w).parts[0]/'control/PAUSE.json';status=read(control).get('status','')if control.exists()else'';failures.append(dict(path=str(q.relative_to(w)),sha256=sha(q),classification='CONTROLLED_HANDOFF'if status.startswith('CONTROLLED_HANDOFF')else'RETAINED_FAILURE_OR_EXPECTED_NATIVE_REJECTION',record=read(q)))
 save('FAILURE_INVENTORY.json',dict(records=failures,expected_negative_native_probes_are_separately_retained=True,no_selective_deletion=True))
 checks=[]
 for epoch in ('qualification-'+a.epoch,'closure-'+a.epoch):
  for directory in ('comparisons','geometry-checks'):
   for q in sorted((w/epoch/directory).glob('*.json')):
    x=read(q);assert x['passed'];checks.append(dict(path=str(q.relative_to(w)),sha256=sha(q),passed=True))
 save('QUALIFICATION_INVENTORY.json',dict(records=checks,finite_only=True,unchanged_R_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),public_byte_replay_is_not_independent_numerical_rerun=True))
 panel=w/'panel-01';stats=dict(complete=False,performance_claim=False,reason='No complete qualified frozen panel')
 if(panel/'COMPLETE.json').exists():
  assert read(panel/'COMPLETE.json')['passed'];plan=read(panel/'PLAN.json');freeze=read(panel/'FROZEN.json');assert sha(panel/'PLAN.json')==freeze['plan']['sha256'];assert len(plan['workers'])==24 and plan['measured']==plan['primers']==96
  rows=[];warm=[];observed=[];caller_totals=defaultdict(float);native_totals=defaultdict(float)
  for worker in plan['workers']:
   run=panel/'runs'/worker['id'];job=read(panel/worker['job']);assert sha(panel/worker['job'])==worker['job_sha256'];assert read(run/'HOST.json')['status']=='COMPLETE';assert len(job['inputs'])==8
   for i in range(0,8,2):
    a0,a1=job['inputs'][i:i+2];assert a0['name']=='warm-'+a1['name']and a1['name'].startswith('root-')and a0['input']==a1['input']and not a0['capture']and not a1['capture']
    pair=[]
    for x in(a0,a1):
     q=run/'native'/x['name']/'receipt.json';v=read(q);assert v['target_output_reserve']==32 and v['k']==3 and v['capture']is False;assert all(n==0 for n in v['observed_API_calls_within_service'].values());assert v['ids']==plan['expected_endpoints'][x['input']['id']]['ids']
     item=dict(round=worker['round'],position=worker['position'],arm=worker['arm'],root=x['input']['id'],service_s=float(v['service_seconds']),receipt_sha256=sha(q));pair.append(v);(warm if x['name'].startswith('warm-')else rows).append(item)
    assert pair[0]['ids']==pair[1]['ids']and pair[0]['target_physical_width_hist']==pair[1]['target_physical_width_hist']and pair[0]['draft_physical_width_hist']==pair[1]['draft_physical_width_hist']
   caller=read(run/'CALLER_COST.json');caller_totals[worker['arm']]+=caller['caller_inclusive_wall_s'];native_totals[worker['arm']]+=read(run/'HOST.json')['worker_wall_s'];observed.append(dict(worker=worker['id'],arm=worker['arm'],clock_sha256=sha(run/'CLOCKS.json'),caller_cost=caller))
  assert len(rows)==len(warm)==96
  totals=defaultdict(float);warm_total=defaultdict(float)
  for x in rows:totals[x['arm']]+=x['service_s']
  for x in warm:warm_total[x['arm']]+=x['service_s']
  old=read(a.export/'ANALYSIS.json');assert old['complete']and len(old['rows'])==96
  first={(z['round'],z['arm'],z['root']):z for z in old['rows']};assert len(first)==96
  for z in rows:
   previous=first[(z['round'],z['arm'],z['root'])];assert z['service_s']==previous['service_s']and z['receipt_sha256']==previous['receipt_sha256']
  contrasts=[]
  for baseline in plan['orders'][0]:
   if baseline=='L_REF1G_D4':continue
   ratios=[]
   for z in rows:
    if z['arm']=='L_REF1G_D4':ratios.append(z['service_s']/first[(z['round'],baseline,z['root'])]['service_s'])
   assert len(ratios)==16;contrasts.append(dict(candidate='L_REF1G_D4',baseline=baseline,aggregate_time_ratio=totals['L_REF1G_D4']/totals[baseline],time_reduction_fraction=1-totals['L_REF1G_D4']/totals[baseline],paired_geomean_ratio=math.exp(sum(math.log(x)for x in ratios)/len(ratios)),paired_ratios=ratios,complete_caller_ratio_including_all_warmups_and_startup=caller_totals['L_REF1G_D4']/caller_totals[baseline],native_worker_ratio_including_all_warmups_and_startup=native_totals['L_REF1G_D4']/native_totals[baseline]))
  stats=dict(complete=True,independent_recalculation_passed=True,plan_sha256=sha(panel/'PLAN.json'),freeze_sha256=sha(panel/'FROZEN.json'),measured=96,warmups=96,rows=rows,warmup_service_s=dict(warm_total),measured_service_s=dict(totals),contrasts=contrasts,complete_caller_total_s=dict(caller_totals),native_worker_total_s=dict(native_totals),full_caller_costs=observed,limitations=['Four exposed roots, four repeated rounds; descriptive deployment, not new blind or population confirmation','Six-arm order has complementary reversals and equal mean positions, but not full six-round Williams balance','D4 W-loop versus L-group changes both lowering and projection; its difference cannot be attributed solely to LOCAL','Different model size and mixed-Q4 recipe from prior8B Q8 experiments; not a size-only effect','Timing endpoints checked for every request; heavy full internal-state checks are finite qualification, not repeated inside clean timing','Measured service is resident request time; complete caller/worker totals additionally include all warmups, native SHA/load and startup, with host SHA added in caller totals'])
 save('STATISTICAL_REPLAY.json',stats);assert sha(w/'ledger.jsonl')==before,'Closed ledger changed during audit'
 save('COMPLETE.json',dict(passed=True,closed_ledger_sha256=before,native_requests_started=0,performance_complete=stats['complete'],audit_wall_s=time.monotonic()-began,files=[dict(file=q.name,bytes=q.stat().st_size,sha256=sha(q))for q in sorted(a.out.iterdir())if q.is_file()]))
 print(json.dumps(dict(passed=True,performance_complete=stats['complete'],cumulative=counters)))
if __name__=='__main__':main()
