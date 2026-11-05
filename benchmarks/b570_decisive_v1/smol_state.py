"""Pinned dense F16 state decoding and lossless token-chunk storage."""
from smol import *
import base64,struct,numpy as np
from collections import OrderedDict
_chunks=OrderedDict();_verified_states=set()

def chunk(h):
 assert len(h)==64 and set(h)<=set('0123456789abcdef')
 p=SROOT/'state-token-cas'/h[:2]/h;st=p.stat();assert st.st_size==196608
 if h in _chunks:
  stamp,data=_chunks.pop(h)
  if stamp!=(st.st_size,st.st_mtime_ns):data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==h
 else:data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==h
 _chunks[h]=((st.st_size,st.st_mtime_ns),data)
 if len(_chunks)>2048:_chunks.popitem(last=False)
 return data

def manifest_key(m):
 return hashlib.sha256(json.dumps({k:m[k] for k in ('raw_bytes','raw_sha256','tokens','framing')},sort_keys=True).encode()).hexdigest()

def canonical_verified(path):
 p=native_path(path)
 if p.exists():a,_=decode(load(path));return tuple(hashlib.sha256(x.tobytes()).hexdigest() for x in a)
 m=read(str(p)+'.pack.json');key=manifest_key(m)
 if key not in _verified_states:
  # Verify an actual reconstruction and parser once per distinct state mapping.
  # Subsequent equality compares canonical chunks whose bytes were authenticated.
  raw=load(path);a,_=decode(raw);assert len(a)==len(m['tokens']);_verified_states.add(key)
 for h in m['tokens']:chunk(h)
 return tuple(m['tokens'])
def profile():
 return dict(format='dense_seq_f16_v1',writer_sha256=sha(Path('C:/hs/b570-direct-id-v1-src/src/llama-kv-cache.cpp')),target_model_sha256=read(SROOT/'AUTHENTICATION.json')['models'][0]['sha256'],layer_map_source_sha256=sha(Path('C:/hs/b570-direct-id-v1-src/src/llama-hparams.h')),host_writer_reviewed=True,capacity=1024,layers=[dict(id=i,k_elements=2048,v_elements=2048) for i in range(24)])
def decode(raw):
 i=0
 def rd(f):
  nonlocal i
  n=struct.calcsize('<'+f);assert i+n<=len(raw);v=struct.unpack_from('<'+f,raw,i);i+=n;return v[0] if len(v)==1 else v
 assert rd('I')==0xaf143cd8 and rd('i')==0 and rd('I')==1;n=rd('I');assert 0<n<=1024
 for pos in range(n):assert rd('i')==pos and rd('I')==1 and rd('i')==0
 trans=rd('I');assert trans in (0,1) and rd('I')==24;head=raw[:i];ks=[];vs=[];kmeta=[];vmeta=[]
 for layer in range(24):
  at=i;assert rd('i')==1 and rd('Q')==4096;kmeta.append(raw[at:i]);count=n*4096
  assert i+count<=len(raw);ks.append(np.frombuffer(raw,dtype='<u2',count=n*2048,offset=i).reshape(n,2048));i+=count
 for layer in range(24):
  at=i;assert rd('i')==1
  if trans:assert rd('I')==2 and rd('I')==2048
  else:assert rd('Q')==4096
  vmeta.append(raw[at:i]);count=n*4096;assert i+count<=len(raw)
  v=np.frombuffer(raw,dtype='<u2',count=n*2048,offset=i);vs.append(v.reshape(2048,n).T if trans else v.reshape(n,2048));i+=count
 assert i==len(raw)
 a=np.empty((n,24,4096),dtype='<u2')
 for layer in range(24):a[:,layer,:2048]=ks[layer];a[:,layer,2048:]=vs[layer]
 return a,dict(header=base64.b64encode(head).decode(),kmeta=[base64.b64encode(x).decode() for x in kmeta],vmeta=[base64.b64encode(x).decode() for x in vmeta],trans=trans)
def encode(a,m):
 out=bytearray(base64.b64decode(m['header']))
 for layer in range(24):out+=base64.b64decode(m['kmeta'][layer]);out+=a[:,layer,:2048].tobytes()
 for layer in range(24):
  out+=base64.b64decode(m['vmeta'][layer]);v=a[:,layer,2048:];out+=(v.T if m['trans'] else v).tobytes()
 return bytes(out)
def load(path):
 path=native_path(path)
 if path.exists():return path.read_bytes()
 m=read(str(path)+'.pack.json');assert m['format']=='smol-state-token-pack-v1'
 pieces=[]
 for h in m['tokens']:
  pieces.append(chunk(h))
 a=np.frombuffer(b''.join(pieces),dtype='<u2').reshape(len(pieces),24,4096);raw=encode(a,m['framing']);assert len(raw)==m['raw_bytes'] and hashlib.sha256(raw).hexdigest()==m['raw_sha256'];return raw
def pack(path):
 path=native_path(path);assert SROOT.resolve() in path.resolve().parents
 raw=path.read_bytes();a,m=decode(raw);assert encode(a,m)==raw;hs=[]
 for row in a:
  b=row.tobytes();h=hashlib.sha256(b).hexdigest();p=SROOT/'state-token-cas'/h[:2]/h;p.parent.mkdir(parents=True,exist_ok=True)
  if p.exists():assert chunk(h)==b
  else:p.write_bytes(b)
  hs.append(h)
 write(str(path)+'.pack.json',dict(format='smol-state-token-pack-v1',raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),tokens=hs,framing=m,source_path=path.name))
 # Verify the retained encoding independently before removing the redundant flat copy.
 b=np.stack([np.frombuffer(chunk(h),dtype='<u2').reshape(24,4096) for h in hs])
 assert hashlib.sha256(encode(b,m)).hexdigest()==sha(path)
 path.unlink()
def validate():
 sys.path.insert(0,str(TOOLKIT));from active_kv import parse
 p=SROOT/'observer-R-0-capture.json.states/0.bin';raw=load(p);a,m=decode(raw);canonical,scope=parse(raw,list(range(len(a))),profile());assert canonical==a.tobytes() and encode(a,m)==raw
 # Distinct uint16 sentinel values across token, layer, K/V and transposed V.
 n=3;sent=(np.arange(n*24*4096,dtype=np.uint32)*17%65536).astype('<u2').reshape(n,24,4096)
 for trans in (0,1):
  head=struct.pack('<IiII',0xaf143cd8,0,1,n)+b''.join(struct.pack('<iIi',j,1,0) for j in range(n))+struct.pack('<II',trans,24)
  meta=dict(header=base64.b64encode(head).decode(),trans=trans,kmeta=[base64.b64encode(struct.pack('<iQ',1,4096)).decode()]*24,vmeta=[base64.b64encode(struct.pack('<iII',1,2,2048) if trans else struct.pack('<iQ',1,4096)).decode()]*24)
  rb=encode(sent,meta);got,_=decode(rb);other,_=parse(rb,list(range(n)),profile());assert np.array_equal(got,sent) and other==sent.tobytes()
 write(SROOT/'STATE_PROFILE.json',profile());write(SROOT/'STATE_CODEC_VALIDATION.json',dict(trained_state_sha256=hashlib.sha256(raw).hexdigest(),trained_tokens=len(a),source_writer_and_layer_map_pinned=True,independent_protocol_parser_equal=True,transposed_and_row_major_sentinels_pass=True,raw_byte_exact_inverse=True,scope='Dense seq0 F16 Smol profile only; active canonical ordering token/layer/K,V'))
def compare():
 a=read(SROOT/'qual02-0-heavy-capture.json');r=read(SROOT/'observer-R-0-capture.json');off=read(SROOT/'qual02-0-off-capture.json')
 bank={len(r['prompt_ids'])+i:x for i,x in enumerate(r['state_snapshots'])}
 states=[]
 for x in a['committed_states']:
  n=len(x['prefix']);ref=bank[n];assert x['prefix']==r['prompt_ids']+r['ids'][:n-len(r['prompt_ids'])]
  ar,_=decode(load(x['sequence']));br,_=decode(load(ref['sequence']));equal=np.array_equal(ar,br) and native_path(x['frontier']).read_bytes()==native_path(ref['frontier']).read_bytes();states.append(dict(prefix_tokens=n,active_kv_and_frontier_equal=equal))
 x=a['committed_states'][-1];y=off['committed_states'][-1];av,_=decode(load(x['sequence']));bv,_=decode(load(y['sequence']));assert np.array_equal(av,bv) and native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes()
 write(SROOT/'COMMITTED_STATE_CHECK-0.json',dict(states=states,all_equal=all(x['active_kv_and_frontier_equal'] for x in states),heavy_off_final_equal=True,full_conditional_vector_qualification_pending=True))
 print('Committed state matches:',sum(x['active_kv_and_frontier_equal'] for x in states),'/',len(states))
if __name__=='__main__':
 if sys.argv[1]=='validate':validate()
 elif sys.argv[1]=='compare':compare()
 else:
  for d in ('observer-R-0-capture.json.states','qual02-0-heavy-capture.json.states','qual02-0-off-capture.json.states'):
   for p in sorted((SROOT/d).glob('*.bin')):pack(p)
