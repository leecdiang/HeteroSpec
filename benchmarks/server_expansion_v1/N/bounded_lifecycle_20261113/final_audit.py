"""Read original captures, frontiers, dispatch and all inherited charges; no GPU."""
import argparse,hashlib,json,math,struct,subprocess,time
from pathlib import Path
def load(p):return json.loads(Path(p).read_text())
def equal(a,b):
 count=0
 with Path(a).open('rb') as x,Path(b).open('rb') as y:
  while True:
   l=x.read(65536);r=y.read(65536)
   if l!=r:raise RuntimeError('raw byte difference '+str(a)+' '+str(b)+' offset='+str(count))
   if not l:break
   count+=len(l)
 return count
def main(first,retry,prior,out):
 first=Path(first);retry=Path(retry);prior=Path(prior);out=Path(out)
 if out.exists():raise RuntimeError('fresh audit report')
 m=load(first/'MANIFEST.json');parent=load(first/'STATE.json');state=load(retry/'STATE.json');p4=load(prior/'STATE.json')
 if state['passed_roles']!=['R','REPEAT','COLD','STRONG','LOCAL'] or state['active_worker'] is not None:raise RuntimeError('partial qualification; no complete result')
 if (p4['requests'],p4['rows'],p4['model_loads'])!=(4,732,1):raise RuntimeError('immutable initial pilot budget')
 if hashlib.sha256((first/'STATE.json').read_bytes()).hexdigest()!=state['parent_STATE_sha256']:raise RuntimeError('failed parent STATE changed')
 for k,v in parent['requests'].items():
  if state['requests'][k]!=v:raise RuntimeError('historical charge changed '+k)
 stages=[(first,'R'),(first,'REPEAT'),(first,'COLD'),(first,'STRONG'),(retry,'STRONG'),(retry,'LOCAL')];numerical=[];traces=[];peaks=[];totalraw=0;vectors=0;snapshots=0;stage_rows=0;placements=1;elapsed=0
 reference=first/'R'
 for base,role in stages:
  root=base/role;ops=[load(p) for p in root.glob('*.op.json')]+[load(p) for p in root.glob('*.caller.json')];byreq={}
  for x in ops:byreq.setdefault(x['request'],[]).append(x)
  for ident,ls in sorted(byreq.items()):
   ls.sort(key=lambda x:x['position']);ids=sum((x['input_ids'] for x in ls),[]);rows=sum(x['rows'] for x in ls)
   if rows!=len(ids) or state['requests'][ident]['rows']!=rows or state['requests'][ident]['status']!='COMPLETED':raise RuntimeError('actual ordered row/ledger mismatch '+ident)
   traces.append(dict(stage=('initial/' if base==first else 'retry01/')+role,request=ident,rows=rows,caller_calls=len(ls)));stage_rows+=rows
  vals=sorted(root.glob('*.f32'));kvs=sorted(root.glob('*.kv'));vectors+=len(vals);snapshots+=len(kvs);totalraw+=sum(x.stat().st_size for x in vals+kvs)
  for p in vals:
   a=p.read_bytes()
   if len(a)!=151936*4 or any(not math.isfinite(x[0]) for x in struct.iter_unpack('<f',a)):raise RuntimeError('full vector/finite failure')
  if role in ['REPEAT','STRONG','LOCAL']:
   for p in vals+kvs:numerical.append(dict(stage=('initial/' if base==first else 'retry01/')+role,capture=p.name,bytes=equal(reference/p.name,p)))
  elif role=='COLD':
   for cs in m['cases']:
    n=cs['id'];names=[x.name for x in reference.glob(n+'-q-*.f32')]+[x.name for x in reference.glob(n+'-f-*.f32')]+[n+'-'+s+'.kv' for s in ['trimmed-state','Q-state']+['F-state-'+str(i) for i in range(8)]]
    for name in names:numerical.append(dict(stage='initial/COLD',capture=name,bytes=equal(reference/name,root/name)))
  for cs in m['cases']:
   n=cs['id'];rec=load(root/(n+'-reconcile.json'));final=load(root/(n+'-final-frontier.json'));reset=load(root/(n+'-reset.json'));k=cs['predicted_retained_head'];q=len(cs['canonical_next_ids'])
   if rec['pending'] is not None or rec['frontier_valid'] or rec['retained_head']!=k or rec['native_head']!=k:raise RuntimeError('pending/frontier/trim alignment')
   if final['pending'] is not None or not final['frontier_valid'] or final['materialized_head']!=q+8 or final['last_owned_output']!=n+'-f-7.f32' or reset['head']!=0 or reset['pending'] is not None or reset['frontier_valid']:raise RuntimeError('ownership/final/reset alignment')
   if role!='COLD':
    old=load(root/(n+'-old-frontier.json'))
    if old['pending']!=cs['pending'] or old['logical_ids']!=cs['old_logical_ids'] or old['materialized_head']!=len(cs['old_materialized_ids']) or not old['frontier_valid'] or rec['discarded_pending']!=old['pending']:raise RuntimeError('supplied producer pending contract')
    with (root/(n+'-old-state.kv')).open('rb') as x,(root/(n+'-trimmed-state.kv')).open('rb') as y:
     for i in range(72*8):
      x.seek(i*old['materialized_head']*256)
      if x.read(k*256)!=y.read(k*256):raise RuntimeError('strided retained-prefix raw KV changed')
  exit=load(root/'UNIT_EXIT.json')
  if 'ExecMainStatus=0' not in exit['stdout'] or 'Result=success' not in exit['stdout']:raise RuntimeError('native exit incomplete')
  elapsed+=exit.get('elapsed_seconds',0);placements+=1
  samples=[json.loads(x) for x in (root/'RESOURCE_TRACE.jsonl').read_text().splitlines()]
  peaks.append(dict(stage=('initial/' if base==first else 'retry01/')+role,worker_elapsed_s=exit.get('elapsed_seconds'),samples=len(samples),maximum_free_drop_from_idle_MiB=24111-min(x['free_MiB'] for x in samples),minimum_free_GPU_MiB=min(x['free_MiB'] for x in samples),max_memory_current=max(int(x['memory.current']) for x in samples if str(x.get('memory.current','')).isdigit()),minimum_RAM_available=min(x['RAM_available'] for x in samples),minimum_disk_available=min(x['disk_available'] for x in samples)))
 expected=dict(requests=4+len(traces),rows=732+stage_rows,deployments=placements)
 if expected!=state['consumed'] or totalraw!=state['raw_bytes'] or any(expected[k]>v for k,v in dict(requests=76,rows=85738,deployments=10).items()):raise RuntimeError('global inherited durable budget differs')
 result=dict(status='PASS_ORIGINAL_GPU_RAW_LIFECYCLE_AND_COMPLETE_BUDGET_RECOUNT',consumed_including_previous_pilot=expected,new_since_expanded_authorization=dict(requests=expected['requests']-4,rows=expected['rows']-732,deployments=placements-1),raw_bytes_new_chain=totalraw,raw_bytes_with_previous_pilot=totalraw+p4['bytes'],full_vectors_new_chain=vectors,KV_snapshots_new_chain=snapshots,raw_comparison_pairs=len(numerical),pairs=numerical,requests=traces,resources=peaks,total_new_native_unit_elapsed_s=elapsed,failed_stage='initial STRONG: complete numeric raw equality but callback observations absent under counts mode; no qualification/performance PASS',retry='one authorized engineering successor; heavy observation fixed, all prior charges retained; parent STATE byte-identical',performance='NOT_RUN',original261='NOT_RUN as complete original suite',models_invoked_for_audit=0)
 out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','consumed_including_previous_pilot','new_since_expanded_authorization','raw_bytes_new_chain','full_vectors_new_chain','KV_snapshots_new_chain','raw_comparison_pairs','total_new_native_unit_elapsed_s']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--first',required=True);p.add_argument('--retry',required=True);p.add_argument('--prior',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.first,a.retry,a.prior,a.out)
