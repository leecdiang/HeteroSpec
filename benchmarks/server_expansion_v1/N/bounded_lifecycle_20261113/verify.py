"""Independent original raw-byte replay; no model or CUDA imports."""
import argparse,hashlib,json,math,struct
from pathlib import Path
def verify(ledger,role,out):
 ledger=Path(ledger);out=Path(out);root=ledger/role;manifest=json.loads((ledger/'MANIFEST.json').read_text());state=json.loads((ledger/'STATE.json').read_text());result=json.loads((root/'RESULT.json').read_text())
 if out.exists():raise RuntimeError('fresh replay required')
 if result['role']!=role or result['status']!='CAPTURE_COMPLETE_REQUIRES_INDEPENDENT_STRICT_COMPARISON':raise RuntimeError('incomplete native result')
 checks=[];files=[];reconstructed=[]
 def equal(a,b):
  size=0
  with a.open('rb') as x,b.open('rb') as y:
   while True:
    l=x.read(65536);r=y.read(65536)
    if l!=r:
     k=next((i for i,(u,v) in enumerate(zip(l,r)) if u!=v),min(len(l),len(r)))
     raise RuntimeError('STRICT_FIRST_DIFFERENCE '+str(a.relative_to(ledger))+' '+str(b.relative_to(ledger))+' byte='+str(size+k))
    if not l:break
    size+=len(l)
  checks.append(dict(left=str(a.relative_to(ledger)),right=str(b.relative_to(ledger)),bytes=size))
 for p in sorted(root.glob('*.f32')):
  data=p.read_bytes()
  if len(data)!=151936*4 or any(not math.isfinite(x[0]) for x in struct.iter_unpack('<f',data)):raise RuntimeError('incomplete/nonfinite full output '+p.name)
 for p in sorted(root.glob('*.kv')):
  m=json.loads(p.with_suffix('.json').read_text());h=m['head']
  if p.stat().st_size!=h*147456 or m['active_bytes']!=h*147456 or len(m['tensors'])!=72 or sorted(c[1] for c in m['cells'])!=list(range(h)) or any(c[2]!=0 for c in m['cells']) or [(t['kind'],t['layer']) for t in m['tensors']]!=[(k,i) for k in ('K','V') for i in range(36)]:raise RuntimeError('active KV shape/coverage '+p.name)
 if role=='REPEAT':
  original=ledger/'R'
  a=sorted(x.name for x in original.iterdir() if x.suffix in ('.f32','.kv'));b=sorted(x.name for x in root.iterdir() if x.suffix in ('.f32','.kv'))
  if a!=b:raise RuntimeError('independent trajectory capture denominators differ')
  for n in a:equal(original/n,root/n)
 elif role=='COLD':
  for c in manifest['cases']:
   n=c['id'];k=c['predicted_retained_head']
   for p in sorted((ledger/'R').glob(n+'-q-*.f32')):equal(p,root/p.name)
   for p in sorted((ledger/'R').glob(n+'-f-*.f32')):equal(p,root/p.name)
   for suffix in ['trimmed-state','Q-state']+['F-state-'+str(i) for i in range(8)]:equal(ledger/'R'/(n+'-'+suffix+'.kv'),root/(n+'-'+suffix+'.kv'))
 for c in manifest['cases']:
  n=c['id'];k=c['predicted_retained_head'];initial=role!='COLD'
  if initial:
   old=root/(n+'-old-state.kv');trim=root/(n+'-trimmed-state.kv');m=len(c['old_materialized_ids'])
   with old.open('rb') as x,trim.open('rb') as y:
    for i in range(72*8):
     x.seek(i*m*256);left=x.read(k*256);right=y.read(k*256)
     if left!=right:raise RuntimeError('retained prefix KV changed '+n+' tensor-head='+str(i))
   checks.append(dict(left=old.name,right=trim.name,kind='strided retained prefix',bytes=k*147456))
  for kind in (['INITIAL','APPEND'] if initial else ['APPEND']):
   ident=role+'/'+n+'/'+kind;ops=sorted([json.loads(p.read_text()) for p in root.glob('*.op.json') if json.loads(p.read_text())['request']==ident],key=lambda x:x['position']);ids=sum((v['input_ids'] for v in ops),[])
   expected=c['old_materialized_ids'] if kind=='INITIAL' else (c['canonical_next_ids'] if role=='COLD' else c['canonical_next_ids'][k:])+c['fixed_continuation_ids']
   if ids!=expected or any(v['physical_ubatch']!=1 or v['requested_vectors']!=1 or v['actual_head']!=v['position']+v['rows'] for v in ops):raise RuntimeError('ordered physical input trace '+ident)
   if state['requests'][ident]['status']!='COMPLETED' or state['requests'][ident]['rows']!=len(expected):raise RuntimeError('durable request charge '+ident)
   reconstructed.append(dict(id=ident,rows=len(ids),decode_calls=len(ops),requested_vectors=len(ops)))
  reset=json.loads((root/(n+'-reset.json')).read_text())
  if reset['head']!=0 or reset['pending'] is not None:raise RuntimeError('episode reset missing')
 raw=sum(p.stat().st_size for p in root.iterdir() if p.suffix in ('.f32','.kv'))
 if raw!=sum(state['requests'][v['id']]['raw_bytes'] for v in reconstructed):raise RuntimeError('raw charge differs')
 for p in sorted(root.iterdir()):
  if p.is_file():
   h=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''):h.update(b)
   files.append(dict(file=p.name,bytes=p.stat().st_size,sha256=h.hexdigest()))
 report=dict(status='PASS_INDEPENDENT_RAW_'+role,role=role,requests=reconstructed,full_vectors=len(list(root.glob('*.f32'))),KV_snapshots=len(list(root.glob('*.kv'))),raw_bytes=raw,pairs=checks,files=files,models_invoked_for_replay=0,rule='STRICT_FINITE_RAW_BITS',scope='supplied-history two cases; complete requested vectors; all36layers K/V; repeated full resident trajectory or cold suffix bridge, as applicable')
 out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ledger',required=True);p.add_argument('--role',choices=['R','REPEAT','COLD'],required=True);p.add_argument('--out',required=True);a=p.parse_args()
 try:r=verify(a.ledger,a.role,a.out);print(json.dumps({k:r[k] for k in ['status','full_vectors','KV_snapshots','raw_bytes','requests']}))
 except Exception as e:
  failure=Path(a.out+'.FAILED.json')
  if not failure.exists():failure.write_text(json.dumps(dict(status='FAIL_CLOSED',reason=str(e)))+'\n')
  raise
