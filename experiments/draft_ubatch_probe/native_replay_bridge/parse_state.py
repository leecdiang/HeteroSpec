"""Strict decoder for the pinned tiny-Llama seq0 active-state serialization.
Not a general llama format reader; raw state and this header are retained.
"""
import struct
MAGIC=0xaf143cd8
BYTES_PER_TOKEN=2048
class StateError(ValueError):pass

def parse(raw, expected_tokens):
 n=len(expected_tokens)
 if not 0<n<=128:raise StateError('unsupported active token count')
 offset=0
 def read(fmt):
  nonlocal offset
  size=struct.calcsize('<'+fmt)
  if offset+size>len(raw):raise StateError('truncated header')
  result=struct.unpack_from('<'+fmt,raw,offset);offset+=size
  return result[0] if len(result)==1 else result
 def take(size):
  nonlocal offset
  if offset+size>len(raw):raise StateError('truncated payload')
  out=raw[offset:offset+size];offset+=size;return out
 def require(x,m):
  if not x:raise StateError(m)
 require(read('I')==MAGIC,'wrong magic/endianness');require(read('i')==0,'wrong sequence')
 require(read('I')==1,'unsupported stream count');require(read('I')==n,'active count differs')
 for pos in range(n):
  require(read('i')==pos,'noncontiguous/reordered positions unsupported');require(read('I')==1,'multiple/missing sequence IDs');require(read('i')==0,'wrong cell sequence')
 v_trans=read('I');require(v_trans in (0,1),'unknown V layout');require(read('I')==2,'unsupported layer count')
 keys=[];values=[]
 for layer in range(2):
  require(read('i')==1,'K is not F16');require(read('Q')==512,'unsupported K row bytes');keys.append(take(n*512))
 for layer in range(2):
  require(read('i')==1,'V is not F16')
  if not v_trans:
   require(read('Q')==512,'unsupported V row bytes');values.append(take(n*512))
  else:
   require(read('I')==2,'unsupported V element size');require(read('I')==256,'unsupported V embedding')
   transposed=take(n*512)
   values.append(b''.join(transposed[(dim*n+t)*2:(dim*n+t)*2+2] for t in range(n) for dim in range(256)))
 require(offset==len(raw),'trailing bytes/unknown state layout')
 canonical=b''.join(keys[layer][t*512:(t+1)*512]+values[layer][t*512:(t+1)*512] for t in range(n) for layer in range(2))
 require(len(canonical)==n*BYTES_PER_TOKEN,'canonical length')
 return canonical,{'format':'tiny-llama-seq0-f16-active-v1','v_trans':v_trans,'layers':2,'positions':list(range(n)),'sequence_id':0,'bytes_per_token':BYTES_PER_TOKEN,'canonical_order':'token/layer/K-then-V/component/raw-little-endian-F16','raw_bytes':len(raw),'excluded':'inactive padding, allocator/graph state, logits; tokens established by separate execution trace'}
