"""Lossless offline Smol serialization; never used by a native model worker."""
import base64,hashlib,time
import numpy as np

def encode(a,m):
 assert a.dtype==np.dtype('<u2') and a.ndim==3 and a.shape[1:]==(24,4096)
 out=bytearray(base64.b64decode(m['header']))
 for layer in range(24):out+=base64.b64decode(m['kmeta'][layer]);out+=a[:,layer,:2048].tobytes()
 for layer in range(24):
  out+=base64.b64decode(m['vmeta'][layer]);v=a[:,layer,2048:]
  if m['trans']:
   # Bound the working set while transposing capacity-strided token rows. This
   # copies uint16 bit patterns, including all signs/payloads, without arithmetic.
   ordered=np.empty((2048,len(a)),dtype='<u2')
   for start in range(0,len(a),32):ordered[:,start:start+32]=v[start:start+32].T
   out+=ordered.tobytes()
  else:out+=v.tobytes()
 return bytes(out)

def validate():
 from evidence_host import ROOT,OSMOL,codec,read,write,sha,native_path
 assert not (ROOT/'ENCODER_VALIDATION.json').exists() and codec.encode is not encode
 started=time.monotonic();tests=[]
 old=read(OSMOL/'campaign02/runs/test-1-forced-0/0.json')
 state=next(x for x in reversed(old['prefixes']) if 'sequence' in x)
 path=native_path(state['sequence']);m=read(str(path)+'.pack.json')
 a=np.stack([np.frombuffer(codec.chunk(h),dtype='<u2').reshape(24,4096) for h in m['tokens']])
 for trans in (m['framing']['trans'],):
  t=time.monotonic();legacy=codec.encode(a,m['framing']);legacy_s=time.monotonic()-t
  t=time.monotonic();new=encode(a,m['framing']);fast_s=time.monotonic()-t
  assert new==legacy and len(new)==m['raw_bytes'] and hashlib.sha256(new).hexdigest()==m['raw_sha256']
  decoded,_=codec.decode(new);assert np.array_equal(decoded,a)
  tests.append(dict(tokens=len(a),trans=trans,legacy_seconds=legacy_s,blocked_seconds=fast_s,exact_saved_reference_bytes=True))
 # A second block with tail3, all uint16 bit patterns, and both writer layouts.
 meta=m['framing'];n=35;sentinel=(np.arange(n*24*4096,dtype=np.uint32)*17%65536).astype('<u2').reshape(n,24,4096)
 for trans in (0,1):
  frame=dict(meta,trans=trans)
  # All layer metadata is 12 bytes; adapt only the documented transposed tag.
  import struct
  frame['vmeta']=[base64.b64encode(struct.pack('<iII',1,2,2048) if trans else struct.pack('<iQ',1,4096)).decode()]*24
  raw_header=struct.pack('<IiII',0xaf143cd8,0,1,n)+b''.join(struct.pack('<iIi',j,1,0) for j in range(n))+struct.pack('<II',trans,24);frame['header']=base64.b64encode(raw_header).decode()
  assert encode(sentinel,frame)==codec.encode(sentinel,frame)
  got,_=codec.decode(encode(sentinel,frame));assert np.array_equal(got,sentinel)
  tests.append(dict(tokens=n,trans=trans,all_uint16_bit_patterns=True,legacy_bytes_equal=True))
 write(ROOT/'ENCODER_VALIDATION.json',dict(status='BYTE_EXACT_OFFLINE_STORAGE_ONLY',tests=tests,wall_seconds=time.monotonic()-started,model_requests=0,encode_source_sha256=sha(__file__),native_worker_or_reference_changed=False))
 print('OFFLINE_ENCODER_BYTE_EXACT',tests,flush=True)

if __name__=='__main__':validate()
