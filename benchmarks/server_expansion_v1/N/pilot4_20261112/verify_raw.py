"""Independent raw byte/shape/trace recount; does not load a model or invoke CUDA."""
import argparse,hashlib,json,math,struct,time
from pathlib import Path

def verify(root,case,out):
 root=Path(root);out=Path(out)
 if out.exists():raise RuntimeError('fresh independent report required')
 c=json.loads(Path(case).read_text());state=json.loads((root/'STATE.json').read_text());r=json.loads((root/'RESULT.json').read_text())
 if r['status']!='PASS_ONE_SUPPLIED_HISTORY_NUMERICAL_BRIDGE' or state['requests']!=4 or state['rows']!=732 or state['model_loads']!=1 or state['contexts']!=2 or len(state['completed'])!=4:raise RuntimeError('terminal/budget mismatch')
 checks=[]
 def equal(a,b):
  with (root/a).open('rb') as x,(root/b).open('rb') as y:
   offset=0
   while True:
    left=x.read(65536);right=y.read(65536)
    if left!=right:
     first=next((i for i,(l,r) in enumerate(zip(left,right)) if l!=r),min(len(left),len(right)))
     raise RuntimeError('raw first difference '+a+' '+b+' byte='+str(offset+first))
    if not left:break
    offset+=len(left)
  checks.append(dict(left=a,right=b,compared_bytes=offset,status='STRICT_BYTES_EQUAL'))
 # Check complete requested logits, not argmax or matching hashes.
 vectors=sorted(root.glob('*.f32'))
 for p in vectors:
  data=p.read_bytes()
  if len(data)!=151936*4 or any(not math.isfinite(x[0]) for x in struct.iter_unpack('<f',data)):raise RuntimeError('incomplete/nonfinite vector')
 equal('R1-old-output.f32','R2-old-output.f32')
 for i in range(88,216):equal('R3-q-'+str(i)+'.f32','R4-q-'+str(i)+'.f32')
 for i in range(8):equal('R3-f-'+str(i)+'.f32','R4-f-'+str(i)+'.f32')
 kvfiles=sorted(root.glob('*.kv'))
 for p in kvfiles:
  m=json.loads(p.with_suffix('.json').read_text());h=m['head']
  if p.stat().st_size!=h*147456 or m['active_bytes']!=p.stat().st_size or len(m['tensors'])!=72 or sorted(x[1] for x in m['cells'])!=list(range(h)) or any(x[2]!=0 for x in m['cells']):raise RuntimeError('active state coverage missing')
  if [(x['kind'],x['layer']) for x in m['tensors']]!=[(k,i) for k in ('K','V') for i in range(36)]:raise RuntimeError('tensor order changed')
 equal('R1-old-state.kv','R2-old-state.kv')
 equal('R3-prefix-state.kv','R4-trimmed-state.kv')
 equal('R3-Q-state.kv','R4-Q-state.kv')
 for i in range(8):equal('R3-F-state-'+str(i)+'.kv','R4-F-state-'+str(i)+'.kv')
 # Separate retained-prefix validation, with old/new per-head strides.
 old=(root/'R1-old-state.kv').read_bytes();retained=(root/'R4-trimmed-state.kv').read_bytes()
 for tensor in range(72):
  for head in range(8):
   begin_old=(tensor*8+head)*186*128*2;begin_new=(tensor*8+head)*88*128*2
   if old[begin_old:begin_old+88*128*2]!=retained[begin_new:begin_new+88*128*2]:raise RuntimeError('retained KV prefix changed')
 traces={i:[] for i in range(1,5)}
 for p in root.glob('*.op.json'):
  x=json.loads(p.read_text());traces[x['request_ordinal']].append(x)
 nominal=[186,186,224,136]
 reconstructed=[]
 for i in range(1,5):
  xs=sorted(traces[i],key=lambda x:x['position']);ids=sum((x['input_ids'] for x in xs),[])
  expected=c['old_materialized_ids'] if i<3 else (c['canonical_next_ids'] if i==3 else c['canonical_next_ids'][88:])+c['fixed_continuation_ids']
  if ids!=expected or len(ids)!=nominal[i-1] or any(not x['complete_decode'] or x['physical_ubatch']!=1 for x in xs):raise RuntimeError('actual ordered input/row trace differs')
  reconstructed.append(dict(request=i,decode_calls=len(xs),rows=len(ids),requested_vectors=sum(x['requested_output_rows'] for x in xs)))
 if len(vectors)!=275 or len(kvfiles)!=22:raise RuntimeError('capture denominator changed')
 rawbytes=sum(p.stat().st_size for p in vectors+kvfiles)
 if rawbytes!=state['bytes']:raise RuntimeError('capture byte charge differs')
 files=[]
 for p in sorted(root.iterdir()):
  if p.is_file():
   digest=hashlib.sha256()
   with p.open('rb') as f:
    for b in iter(lambda:f.read(1048576),b''):digest.update(b)
   files.append(dict(file=p.name,bytes=p.stat().st_size,sha256=digest.hexdigest()))
 report=dict(status='PASS_INDEPENDENT_ORIGINAL_GPU_RAW_BYTE_RECOUNT',requests=reconstructed,
     full_vectors=len(vectors),active_KV_snapshots=len(kvfiles),raw_bytes=rawbytes,
     raw_comparison_pairs=len(checks),pairs=checks,retained_prefix_bytes=len(retained),
     tensor_layout_checks='all72 tensors,all36layers,8heads,F16,canonical positions,seq0',
     finite_vectors='all275 complete151936-element F32 rows',
     finite_KV='source-bound native capture validates every F16 scalar; independent replay checks all bytes and shape',
     new_model_calls=0,old_pending=c['pending'],trim_disposition='discard old pending; frontier invalid until suffix decode',
     source_kind='supplied history and fixed token continuation; not free generation',
     limitation='initial reference repeated; whole resident transition not independently repeated; no LOCAL candidate or performance',files=files)
 out.write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['status','full_vectors','active_KV_snapshots','raw_bytes','raw_comparison_pairs','requests']}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--case',required=True);p.add_argument('--out',required=True)
 a=p.parse_args();verify(a.root,a.case,a.out)
