"""Independent exact raw replay and actual native dispatch recount."""
import argparse,hashlib,json,math,struct
from pathlib import Path
def main(ledger,role,out):
 ledger=Path(ledger);root=ledger/role;out=Path(out);m=json.loads((ledger/'MANIFEST.json').read_text());state=json.loads((ledger/'STATE.json').read_text());r=json.loads((root/'RESULT.json').read_text())
 if out.exists() or r['role']!=role:raise RuntimeError('fresh report / role identity')
 a=sorted(p.name for p in (ledger/'R').iterdir() if p.suffix in ('.f32','.kv'));b=sorted(p.name for p in root.iterdir() if p.suffix in ('.f32','.kv'))
 if a!=b:raise RuntimeError('complete reference/candidate capture denominators differ')
 checks=[];files=[]
 for n in a:
  offset=0
  with (ledger/'R'/n).open('rb') as x,(root/n).open('rb') as y:
   while True:
    l=x.read(65536);rr=y.read(65536)
    if l!=rr:
     i=next((i for i,(u,v) in enumerate(zip(l,rr)) if u!=v),min(len(l),len(rr)));raise RuntimeError('STRICT_FIRST_DIFFERENCE '+n+' byte='+str(offset+i))
    if not l:break
    offset+=len(l)
  checks.append(dict(capture=n,bytes=offset))
  if n.endswith('.f32'):
   raw=(root/n).read_bytes()
   if len(raw)!=151936*4 or any(not math.isfinite(v[0]) for v in struct.iter_unpack('<f',raw)):raise RuntimeError('full finite F32 vector missing')
  else:
   meta=json.loads((root/Path(n).with_suffix('.json')).read_text());h=meta['head']
   if offset!=h*147456 or meta['active_bytes']!=offset or len(meta['tensors'])!=72 or sorted(x[1] for x in meta['cells'])!=list(range(h)):raise RuntimeError('KV shape/coverage')
 dispatch=json.loads((root/'DISPATCH.json').read_text());physical=dispatch['physical'];rows=sum(x['API_width'] for x in physical)
 if rows!=989 or sum(x['physical_rows'] for x in physical)!=989 or any(x['API_width']!=x['physical_rows'] or x['physical_calls']!=1 or x['returncode'] for x in physical):raise RuntimeError('actual physical decode mismatch')
 callers=[json.loads(p.read_text()) for p in root.glob('*.caller.json')];hist={}
 for x in physical:hist[str(x['API_width'])]=hist.get(str(x['API_width']),0)+1
 requests=[]
 for cs in m['cases']:
  for kind in ['INITIAL','APPEND']:
   ident=role+'/'+cs['id']+'/'+kind;ops=sorted((x for x in callers if x['request']==ident),key=lambda x:x['position']);ids=sum((x['input_ids'] for x in ops),[]);expect=cs['old_materialized_ids'] if kind=='INITIAL' else cs['canonical_next_ids'][cs['predicted_retained_head']:]+cs['fixed_continuation_ids']
   if ids!=expect or sum(x['API_width'] for x in physical if x['request']==ident)!=len(expect) or state['requests'][ident]['status']!='COMPLETED' or state['requests'][ident]['rows']!=len(expect):raise RuntimeError('caller/physical/durable request mismatch '+ident)
   requests.append(dict(id=ident,rows=len(expect),caller_calls=len(ops),physical_calls=sum(x['request']==ident for x in physical)))
 if dispatch['loop4_marked_nodes']<=0 or dispatch['GPU_nodes']<=0:raise RuntimeError('no actual loop4 graph or placement observation')
 rawbytes=sum((root/n).stat().st_size for n in a)
 if rawbytes!=sum(state['requests'][v['id']]['raw_bytes'] for v in requests):raise RuntimeError('raw durable charge')
 for p in sorted(root.iterdir()):
  if p.is_file():
   h=hashlib.sha256()
   with p.open('rb') as f:
    for raw in iter(lambda:f.read(1048576),b''):h.update(raw)
   files.append(dict(file=p.name,bytes=p.stat().st_size,sha256=h.hexdigest()))
 report=dict(status='PASS_INDEPENDENT_STRICT_'+role,role=role,pairs=checks,requests=requests,raw_bytes=rawbytes,full_vectors=sum(n.endswith('.f32') for n in a),KV_snapshots=sum(n.endswith('.kv') for n in a),physical_width_histogram=hist,loop4_marked_graph_nodes=dispatch['loop4_marked_nodes'],GPU_observed_nodes=dispatch['GPU_nodes'],files=files,performance=False,models_invoked_for_replay=0)
 out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','requests','physical_width_histogram','loop4_marked_graph_nodes']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--ledger',required=True);p.add_argument('--role',choices=['STRONG','LOCAL'],required=True);p.add_argument('--out',required=True);a=p.parse_args()
 try:main(a.ledger,a.role,a.out)
 except Exception as e:
  p=Path(a.out+'.FAILED.json')
  if not p.exists():p.write_text(json.dumps(dict(status='FAIL_CLOSED',reason=str(e)))+'\n')
  raise
