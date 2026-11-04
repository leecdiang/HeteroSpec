#!/usr/bin/env python3
"""Independent fixed-layout serializer sentinels and corruption checks."""
import argparse,pathlib,sys,importlib.util,struct,hashlib,json
p=argparse.ArgumentParser();p.add_argument('--parser',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--native-blob',type=pathlib.Path);a=p.parse_args();sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('reviewed_parser',a.parser);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def need(x,msg):
 if not x:raise ValueError(msg)
def bit(t,l,kv,d):
 # Row identifiers are unique over the admitted 128-token geometry.
 # Other components cover arbitrary raw bits and explicit nonfinite patterns.
 if d==0:return t*4+l*2+kv
 if d in (1,2,3,4,5):return (0x7c00,0xfc00,0x7e01,0x8000,0x0000)[d-1]
 return int.from_bytes(hashlib.sha256(f'{t}/{l}/{kv}/{d}'.encode()).digest()[:2],'little')
def synth(n,trans):
 b=bytearray(struct.pack('<IiII',0xaf143cd8,0,1,n));offsets={}
 for t in range(n):offsets['pos'+str(t)]=len(b);b+=struct.pack('<iIi',t,1,0)
 offsets['v_trans']=len(b);b+=struct.pack('<II',trans,2)
 for l in range(2):
  offsets['K'+str(l)]=len(b);b+=struct.pack('<iQ',1,512)
  for t in range(n):
   for d in range(256):b+=struct.pack('<H',bit(t,l,0,d))
 for l in range(2):
  offsets['V'+str(l)]=len(b);b+=struct.pack('<iII',1,2,256) if trans else struct.pack('<iQ',1,512)
  order=((t,d) for d in range(256) for t in range(n)) if trans else ((t,d) for t in range(n) for d in range(256))
  for t,d in order:b+=struct.pack('<H',bit(t,l,1,d))
 expected=b''.join(struct.pack('<H',bit(t,l,kv,d)) for t in range(n) for l in range(2) for kv in range(2) for d in range(256))
 return bytes(b),expected,offsets
need(len({struct.pack('<256H',*(bit(t,l,kv,d) for d in range(256))) for t in range(128) for l in range(2) for kv in range(2)})==512,'sentinel row collision')
valid=[]
for n in (1,2,3,7,17,128):
 for trans in (0,1):
  raw,want,offsets=synth(n,trans);out,meta=m.parse(raw,list(range(n)))
  need(out==want,'wrong canonical token/layer/K/V mapping');need(len(raw)==72+2060*n,'independent raw length arithmetic');need(len(out)==2048*n,'active size')
  valid.append({'tokens':n,'transposed_v':trans,'raw_sha256':hashlib.sha256(raw).hexdigest(),'canonical_sha256':hashlib.sha256(out).hexdigest()})
raw,want,o=synth(3,1)
mutations={
 'magic':(0,'I',0), 'wrong_outer_seq':(4,'i',1),'wrong_stream_count':(8,'I',2),'wrong_cell_count':(12,'I',4),
 'negative_position':(o['pos0'],'i',-1),'duplicate_position':(o['pos1'],'i',0),'reordered_position':(o['pos0'],'i',2),
 'multi_seq_cell':(o['pos0']+4,'I',2),'wrong_cell_seq':(o['pos0']+8,'i',1),
 'unknown_v_trans':(o['v_trans'],'I',7),'wrong_layers':(o['v_trans']+4,'I',1),
 'K_dtype':(o['K0'],'i',0),'K_stride':(o['K0']+4,'Q',256),'K_huge_stride':(o['K0']+4,'Q',2**63),
 'V_dtype':(o['V0'],'i',0),'V_elsize':(o['V0']+4,'I',4),'V_dims':(o['V0']+8,'I',128),
}
rejected={}
for label,(off,fmt,value) in mutations.items():
 b=bytearray(raw);struct.pack_into('<'+fmt,b,off,value)
 try:m.parse(bytes(b),[1,2,3])
 except m.StateError as e:rejected[label]=str(e)
 else:raise ValueError('corruption accepted: '+label)
extra={'truncate_last':raw[:-1],'trailing_byte':raw+b'x','short_header':raw[:15],'big_endian_magic':struct.pack('>I',0xaf143cd8)+raw[4:]}
for label,b in extra.items():
 try:m.parse(b,[1,2,3])
 except m.StateError as e:rejected[label]=str(e)
 else:raise ValueError('corruption accepted: '+label)
# Payload content is opaque, so a byte mutation must survive extraction exactly,
# rather than being treated as metadata or rounded through float conversion.
b=bytearray(raw);b[o['K0']+12+13]^=1;out,_=m.parse(bytes(b),[1,2,3]);need(out!=want,'payload mutation hidden')
same_ids,_=m.parse(raw,[127,127,127]);need(same_ids==want,'raw format unexpectedly carries token IDs')
result={'same_length_different_ids_not_detected_by_raw_parser':True,'scope':'Fixed serializer structural/extraction tests, not KV mathematical correctness or model/GPU qualification','parser_sha256':hashlib.sha256(a.parser.read_bytes()).hexdigest(),'valid_sentinel_cases':valid,'corruptions_rejected':rejected,'raw_payload_bit_mutation_visible':True,'token_id_content_not_present_in_serializer':True}
if a.native_blob:
 b=a.native_blob.read_bytes();out,meta=m.parse(b,list(range(7)));result['supplied_native_blob']={'raw_sha256':hashlib.sha256(b).hexdigest(),'canonical_sha256':hashlib.sha256(out).hexdigest(),'meta':meta,'provenance':'Supplied native blob parsing only. Completion and role provenance must be read from its separate capture receipt.'}
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'sentinels':len(valid),'rejected':len(rejected),'parser_sha256':result['parser_sha256']}))
