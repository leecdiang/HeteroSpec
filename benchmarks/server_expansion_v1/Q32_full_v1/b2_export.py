"""Closed B2 data-only archive and separate receipt recalculation, no GPU work."""
from pathlib import Path
from collections import defaultdict
import argparse,gzip,hashlib,json,math,re,time
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);p.add_argument('--source',type=Path,required=True);p.add_argument('--root',type=Path,required=True);a=p.parse_args();w=a.work;assert(w/'NATIVE_CONTROLLER_TERMINAL.private.json').exists();out=w/'export-01';out.mkdir();began=time.monotonic()
 def clean(s):
  s=s.replace(str(a.root),'$HS_ROOT').replace(str(Path.home()),'$HOME');s=re.sub(r'/home/[A-Za-z0-9_.-]+','$HOME_USER',s);s=re.sub(r'GPU-[a-fA-F0-9-]{8,}','<redacted-GPU>',s);s=re.sub(r'\b192\.168(?:\.\d{1,3}){1,2}\b','<private-network>',s);assert not re.search(r'/home/[a-z]|GPU-[a-fA-F0-9]{8}|192\.168\.\d',s);return s
 def save(name,x):(out/name).write_text(clean(json.dumps(x,indent=2))+'\n')
 plan=read(w/'PLAN.json');inherited=read(w/'INHERITED_ACCOUNTING.json');ledger=[json.loads(x)for x in(w/'ledger.jsonl').read_text().splitlines()]if(w/'ledger.jsonl').exists()else[];reserved=[x for x in ledger if x['event']=='RESERVE'];counter=dict(requests=inherited['requests']+sum(x['requests']for x in reserved),reserved_rows=inherited['rows']+sum(x['rows']for x in reserved));assert counter['requests']<=2048 and counter['reserved_rows']<=8000000
 stats=dict(complete=False,performance_claim=False,reason='Full16-worker controlled B2 did not complete; retain all partial/failure costs')
 if(w/'COMPLETE.json').exists():
  rows=[];warm=[];workers=[]
  for worker in plan['workers']:
   run=w/'runs'/worker['id'];job=read(w/worker['job']);assert sha(w/worker['job'])==worker['job_sha256'];assert read(run/'HOST.json')['status']=='COMPLETE';assert len(job['diagnostics'])==8
   clocks=read(run/'CLOCKS.json')['markers'];assert[len(clocks),[x['name']for x in clocks]]==[8,[x['name']for x in job['diagnostics']]]
   for i,x in enumerate(job['diagnostics']):
    q=run/'native'/x['name']/'receipt.json';v=read(q);expected_width=8 if x['execution']=='q8'else 4;assert v['physical_width_histogram']=={str(expected_width):8//expected_width};assert v['output_vectors']==8 and v['output_floats']==8*151936 and not v['capture'];assert v['online_state_imports']==v['online_state_exports']==v['online_heavy_captures']==0
    oracle=Path(plan['reuse']['oracle']);assert v['output_sha256']==[sha(oracle/str(x['position']+j+1)/'frontier.f32')for j in range(8)]
    row=dict(worker=worker['id'],core=worker['core'],boundary=worker['boundary'],round=worker['round'],name=x['name'],execution=x['execution'],operation_s=v['operation_s'],external_complete_span_s=clocks[i]['seconds_after_launch']-(clocks[i-1]['seconds_after_launch']if i else 0),first_span_contains_startup=(i==0),disk_s=v['snapshot_disk_read_s'],restore_frontier_s=v['restore_and_frontier_copy_s'],phase_seconds=v['phase_seconds'],graph_built=v['graph_built'],graph_reused=v['graph_reused'],receipt_sha256=sha(q))
    (warm if x['name'].startswith('warm-')else rows).append(row)
   workers.append(dict(id=worker['id'],host=read(run/'HOST.json'),caller=read(w/'checked'/(worker['id']+'.json'))['caller_inclusive_wall_s']))
  assert len(rows)==len(warm)==64;contrasts=[]
  for core,pos in plan['cells']:
   ratios=[];spans=[]
   for rnd in range(4):
    xs=[x for x in rows if(x['core'],x['boundary'],x['round'])==(core,pos,rnd)];assert len(xs)==4
    total=lambda field,e:sum(x[field]for x in xs if x['execution']==e)
    ratios.append(total('operation_s','q8')/total('operation_s','q4pair'));spans.append(total('external_complete_span_s','q8')/total('external_complete_span_s','q4pair'))
   contrasts.append(dict(core=core,boundary=pos,independent_processes=4,paired_process_geomean_ratio=math.exp(sum(math.log(x)for x in ratios)/4),process_ratios=ratios,range=[min(ratios),max(ratios)],external_complete_span_ratios=spans,external_span_limitation='Includes operand disk/SHA/restore/output-SHA/serialization and pipe-observation jitter; mechanism time remains separately native-timed'))
  original=read(w/'RESULTS.json');assert original['passed']and original['measurements']==len(rows)
  for x in contrasts:
   old=next(z for z in original['contrasts']if(z['core'],z['boundary'])==(x['core'],x['boundary']));assert x['process_ratios']==old['process_ratios']and x['paired_process_geomean_ratio']==old['paired_process_geomean_ratio']
  stats=dict(complete=True,independent_recalculation_passed=True,descriptive_only=True,measurements=64,warmups=64,rows=rows,warmup_rows=warm,contrasts=contrasts,workers=workers,limitations=original['limitations'],end_to_end_live_speculative_service=False)
 save('ANALYSIS.json',stats);save('COSTS.json',dict(cumulative_old8B=counter,request_ceiling=2048,row_ceiling=8000000,Q32_ledger_untouched=True,new_reserved_requests=sum(x['requests']for x in reserved),new_reserved_rows=sum(x['rows']for x in reserved),worker_statuses=[dict(out=str(Path(x['out']).relative_to(w)),host=read(Path(x['out'])/'HOST.json')if(Path(x['out'])/'HOST.json').exists()else None)for x in reserved],no_refunds=True))
 index=[];private=[];resources=[];payload=out/'TEXT_RECORDS.jsonl.gz'
 with gzip.open(payload,'xt',encoding='utf8')as f:
  for alias,folder in [('work',w),('source',a.source)]:
   for p in sorted(folder.rglob('*')):
    if not p.is_file()or'__pycache__'in p.parts or any(x.startswith('export-')for x in p.relative_to(folder).parts):continue
    relative=str(p.relative_to(folder));name=alias+'/'+relative
    if 'RESOURCE_GUARD'in p.name or 'GUARD_BASELINE'in p.name or p.name=='PAUSE.json':
     if p.name=='RESOURCE_GUARD.private.jsonl':
      cfg=read(w/'config.private.json');samples=[]
      for line in p.read_text().splitlines():
       v=json.loads(line);selected=[g for g in v['gpu']if g['device']==cfg['gpu_uuid']];samples.append(dict(epoch=v['epoch'],selected_foreign_processes=sum(not g['own']for g in selected),foreign_cpu_on_assigned_cores=v['foreign_cpu_on_assigned_cores'],event_kinds=[z['kind']for z in v['events']]))
      resources.append(dict(path=name,raw_sha256=sha(p),samples=samples))
     else:private.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p),scope='Private host/allocation record retained; not public'))
     continue
    if p.suffix in('.json','.jsonl','.log','.py','.md','.txt')and p.stat().st_size<8*1024**2:
     raw=p.read_bytes()
     try:text=clean(raw.decode('utf8'))
     except UnicodeDecodeError:private.append(dict(path=name,bytes=len(raw),sha256=sha(p)));continue
     item=dict(path=name,raw_bytes=len(raw),raw_sha256=sha(p),public_bytes=len(text.encode()),public_sha256=hashlib.sha256(text.encode()).hexdigest());index.append(item);f.write(json.dumps(dict(path=name,text=text),ensure_ascii=False)+'\n')
    else:private.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
 save('TEXT_INDEX.json',dict(files=index,record_count=len(index)));save('PRIVATE_INDEX.json',dict(files=private));save('RESOURCE_CHECKED.json',dict(files=resources));parts=[]
 with payload.open('rb')as f:
  for i in range(10000):
   b=f.read(384*1024)
   if not b:break
   p=out/f'TEXT_RECORDS.part-{i:04d}.gz';p.write_bytes(b);parts.append(dict(file=p.name,bytes=len(b),sha256=sha(p)))
 save('BUNDLE.json',dict(file=payload.name,bytes=payload.stat().st_size,sha256=sha(payload),ordered_parts=parts,records=len(index)))
 with gzip.open(payload,'rt',encoding='utf8')as f:
  count=0
  for i,line in enumerate(f):
   x=json.loads(line);expected=index[i];assert x['path']==expected['path']and hashlib.sha256(x['text'].encode()).hexdigest()==expected['public_sha256'];count+=1
 assert count==len(index);save('LOCAL_READBACK.json',dict(passed=True,records=count,new_native_requests=0,public_remote_readback='PENDING_UPLOAD'));save('EXPORT_COMPLETE.json',dict(passed=True,performance_complete=stats['complete'],archive_wall_s=time.monotonic()-began,parts=len(parts),zero_native_requests=True))
 print('B2_EXPORT_COMPLETE',stats['complete'],len(index),len(parts))
if __name__=='__main__':main()
