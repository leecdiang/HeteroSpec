"""Independent actual-architecture KV/F32 binary reader; zero model forwards."""
import sys,json,struct,hashlib,math
from pathlib import Path
import numpy as np
R=Path(sys.argv[1]) if len(sys.argv)>1 else Path('C:/hs/jsa-b570-run-v1')
def load(p):return json.loads(Path(p).read_text(encoding='utf8'))
def metadata(p):
 with Path(p).open('rb') as f:
  def get(fmt):return struct.unpack('<'+fmt,f.read(struct.calcsize('<'+fmt)))[0]
  def string(keep):
   n=get('Q')
   if keep:return f.read(n).decode('utf8')
   f.seek(n,1)
  def value(t,keep):
   if t==8:return string(keep)
   if t==9:
    kind=get('I');count=get('Q')
    if not keep and kind!=8 and kind!=9:f.seek(struct.calcsize({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}[kind])*count,1);return
    result=[]
    for _ in range(count):
     x=value(kind,keep)
     if keep:result.append(x)
    return result if keep else None
   x=get({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}[t]);return x if keep else None
  assert f.read(4)==b'GGUF';version=get('I');tensors=get('Q');n=get('Q');out={}
  for _ in range(n):k=string(True);v=value(get('I'),not k.startswith('tokenizer.'));out[k]=v if not k.startswith('tokenizer.') else None
 return out
schemas={}
for family,name in [('Qwen','QWEN_MODELS.json'),('Smol','MODEL_CHOICE.json')]:
 m=metadata(load(R/name)['models']['target']['path']);a=m['general.architecture'];emb=m[a+'.embedding_length'];heads=m[a+'.attention.head_count'];kh=m.get(a+'.attention.head_count_kv',heads)
 schemas[family]=dict(architecture=a,layers=m[a+'.block_count'],key_elements=kh*m.get(a+'.attention.key_length',emb//heads),value_elements=kh*m.get(a+'.attention.value_length',emb//heads),source='actual hash-bound target GGUF metadata, no Qwen width reinterpretation')
checks=0;rows=[];seen={};floatrows=[]
def ck(ok,msg):
 global checks;checks+=1
 assert ok,msg
def kv(path,schema,prompt_len):
 b=path.read_bytes();h=hashlib.sha256(b).hexdigest()
 if h in seen:
  ck(seen[h]['schema']==schema and seen[h]['prompt_len']==prompt_len,'deduplicated state schema');return dict(path=str(path.relative_to(R)),sha256=h,duplicate_of=seen[h]['path'])
 off=0
 def get(fmt):
  nonlocal off
  st=struct.Struct('<'+fmt);v=st.unpack_from(b,off);off+=st.size;return v
 n,=get('I');arch=b[off:off+n].decode();off+=n;streams,=get('I');ck(arch==schema['architecture'] and streams==1,'actual KV architecture/stream '+str(path));nc,=get('I');positions=[]
 for _ in range(nc):
  pos,ns=get('iI');seqs=get('i'*ns);ck(seqs==(0,),'sequence0 ownership');positions.append(pos)
 ck(sorted(positions)==list(range(prompt_len)) and len(set(positions))==len(positions),'actual prompt positions')
 vt,nl=get('II');ck(vt==1 and nl==schema['layers'],'actual KV layer/layout');elements=0
 for role in ['key','value']:
  for layer in range(nl):
   if role=='key':dtype,row=get('iQ');ck(dtype==1 and row==schema['key_elements']*2,'key fp16 actual shape');size=row*nc
   else:dtype,element,emb=get('iII');ck(dtype==1 and element==2 and emb==schema['value_elements'],'value fp16 actual shape');size=element*emb*nc
   ck(off+size<=len(b),'complete KV tensor bytes');v=np.frombuffer(b,dtype='<f2',count=size//2,offset=off);ck(bool(np.isfinite(v).all()),'all KV values finite');elements+=v.size;off+=size
 ck(off==len(b),'entire serialized state consumed')
 row=dict(path=str(path.relative_to(R)),sha256=h,bytes=len(b),architecture=arch,layers=nl,positions=nc,fp16_elements=elements,prompt_len=prompt_len,schema=schema);seen[h]=row;return row
for p in sorted((R/'raw').glob('*/RESULT.json')):
 r=load(p);folder=p.parent;raw=load(folder/'capture.json');schema=schemas[r['family']];prompt_len=len(raw['prompt_ids'])
 for file in r['files']:
  if file.endswith('.kv'):rows.append(kv(R/file,schema,prompt_len))
  if file.endswith('.pending_logits.f32'):
   v=np.fromfile(R/file,dtype='<f4');width=load(R/('QWEN_RUNTIME.json' if r['family']=='Qwen' else 'TOKENIZATION_BINDINGS.json'))['vocab_tokens'];ck(v.size==width and bool(np.isfinite(v).all()),'full actual vocab finite logits')
   first=int(np.argmax(v));ck(first==raw['ids'][0]==raw['transfer']['pending_id'],'greedy pending from actual full row')
   floatrows.append(dict(unit=r['unit'],path=file,vocab_width=width,argmax=first,full_row=True))
out=dict(status='PASS',checks=checks,actual_gguf_schemas=schemas,serialized_states=rows,unique_serialized_states=len(seen),full_vocab_f32_rows=floatrows,all_state_bytes_and_all_float_values_read=True,natural_cross='NO_TRIGGER; no counterfactual arrays generated or claimed',model_forward_calls=0)
(R/'STATE_FLOAT_VERIFICATION.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print('STATE/FLOAT PASS',checks,len(rows),len(floatrows),flush=True)
