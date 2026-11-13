"""Public text/index integrity + accounting/dispatch replay, never raw/GPU proof."""
import argparse,hashlib,io,json,tarfile
from pathlib import Path
def main(evidence,out):
 e=Path(evidence);out=Path(out)
 if out.exists():raise RuntimeError('fresh replay report')
 index=json.loads((e/'PUBLIC_TEXT_INDEX.json').read_text());packet=(e/'PUBLIC_TEXT_PACKET.tar.gz').read_bytes()
 if len(packet)!=index['packet_bytes'] or hashlib.sha256(packet).hexdigest()!=index['packet_sha256']:raise RuntimeError('anonymous packet bytes differ')
 expected={x['file']:x for x in index['members']};texts={}
 with tarfile.open(fileobj=io.BytesIO(packet),mode='r:gz') as tar:
  for m in tar:
   if not m.isfile() or m.name not in expected or m.name in texts or '..' in Path(m.name).parts or Path(m.name).is_absolute():raise RuntimeError('unexpected public member')
   b=tar.extractfile(m).read();x=expected[m.name]
   if len(b)!=x['published_bytes'] or hashlib.sha256(b).hexdigest()!=x['published_sha256']:raise RuntimeError('public text member differs')
   texts[m.name]=b
 if set(texts)!=set(expected):raise RuntimeError('missing public members')
 def load(n):return json.loads(texts[n])
 first=load('initial/root/STATE.json');state=load('retry01/root/STATE.json');manifest=load('initial/root/MANIFEST.json');charged=state['consumed']
 if charged!=dict(requests=26,rows=6448,deployments=7) or len(state['requests'])+4!=charged['requests'] or sum(x['rows'] for x in state['requests'].values())+732!=charged['rows']:raise RuntimeError('global inherited debit')
 if any(state['requests'][k]!=v for k,v in first['requests'].items()):raise RuntimeError('failed predecessor debit rewritten')
 geometry=[]
 for c in manifest['cases']:
  old=c['old_materialized_ids'];q=c['canonical_next_ids'];k=next((i for i,(a,b) in enumerate(zip(old,q)) if a!=b),min(len(old),len(q)))
  if k!=c['predicted_retained_head'] or c['initial_rows']!=len(old) or c['append_rows']!=len(q)-k+8 or c['cold_rows']!=len(q)+8 or c['old_logical_ids']!=old+[c['pending']]:raise RuntimeError('saved-token contract arithmetic')
  geometry.append(dict(case=c['id'],LCP=k,initial=c['initial_rows'],append=c['append_rows'],cold=c['cold_rows']))
 dispatch={};ops={}
 for n,b in texts.items():
  if n.endswith(('.op.json','.caller.json')):
   j=json.loads(b);ops.setdefault(j['request'],[]).append(j)
 for req,ls in ops.items():
  case=next(c for c in manifest['cases'] if '/'+c['id']+'/' in req);ls.sort(key=lambda x:x['position']);ids=sum((x['input_ids'] for x in ls),[]);wanted=case['old_materialized_ids'] if req.endswith('/INITIAL') else (case['canonical_next_ids'] if req.startswith('COLD/') else case['canonical_next_ids'][case['predicted_retained_head']:])+case['fixed_continuation_ids']
  if ids!=wanted or sum(x['rows'] for x in ls)!=state['requests'][req]['rows'] or state['requests'][req]['status']!='COMPLETED':raise RuntimeError('recorded complete inputs/rows differ '+req)
 for role in ['STRONG','LOCAL']:
  d=load('retry01/'+role+'/DISPATCH.json');hist={}
  for x in d['physical']:
   if x['API_width']!=x['physical_rows'] or x['physical_calls']!=1 or x['returncode']!=0:raise RuntimeError('recorded native physical width')
   key=str(x['API_width']);hist[key]=hist.get(key,0)+1
  if d['physical_rows']!=989 or d['physical_calls']!=251 or d['loop4_marked_nodes']<=0 or d['GPU_nodes']<=0:raise RuntimeError('recorded dispatch incomplete')
  dispatch[role]=dict(calls=251,rows=989,width_histogram=hist,loop4_marked_graph_nodes=d['loop4_marked_nodes'])
 fail=load('initial/root/STRONG-INDEPENDENT.json.FAILED.json')
 if fail['status']!='FAIL_CLOSED' or 'observation' not in fail['reason']:raise RuntimeError('preserved failure gate missing')
 original=json.loads((e/'RAW_ARCHIVE_INDEX.json').read_text());raw=[x for x in original['members'] if x['member'].endswith(('.f32','.kv'))]
 if sum(x['bytes'] for x in raw)!=state['raw_bytes']:raise RuntimeError('recorded private raw bytes')
 report=dict(status='PASS_PUBLIC_TEXT_INTEGRITY_SAVED_TOKEN_ACCOUNTING_AND_RECORDED_DISPATCH',members=len(texts),packet_sha256=index['packet_sha256'],geometry=geometry,consumed=charged,request_receipts=len(ops),actual_recorded_dispatch=dispatch,raw_index_bytes=sum(x['bytes'] for x in raw),raw_tensor_bytes_read=0,new_GPU_or_model_calls=0,limitation='public replay checks text/index and recorded inputs/work; unavailable original raw tensors, private process identities and actual GPU qualification are not independently revalidated')
 out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','members','consumed','actual_recorded_dispatch']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);a=p.parse_args();main(a.evidence,a.out)
