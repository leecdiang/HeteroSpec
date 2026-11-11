"""Decode every original PREFILL descriptor; exact fields, no numerical oracle."""
from pathlib import Path
import hashlib,json,struct
def decode(info):
 if info is None:return [],dict(records=0,unique=0)
 p=Path(info['path']);assert p.stat().st_size==info['bytes'];h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(4*1024**2),b''):h.update(b)
 assert h.hexdigest()==info['sha256'];unique={};count=0
 with p.open('rb')as f:
  assert f.read(8)==b'HSOPV1LE'
  while True:
   raw=f.read(4)
   if not raw:break
   assert len(raw)==4;n=struct.unpack('<I',raw)[0];assert 0<n<65536;payload=f.read(n);assert len(payload)==n;count+=1;key=payload[4:]
   if key in unique:unique[key]['observed_occurrences']+=1;continue
   offset=0
   def rd(fmt):
    nonlocal offset
    size=struct.calcsize('<'+fmt);assert offset+size<=len(payload);value=struct.unpack_from('<'+fmt,payload,offset);offset+=size;return value[0]if len(value)==1 else list(value)
   def text():
    nonlocal offset
    n=rd('I');assert n<=256 and offset+n<=len(payload);s=payload[offset:offset+n].decode('utf8');offset+=n;return s
   def tensor():return dict(name=text(),type=text(),ne=rd('4q'),nb=rd('4Q'),device=text())
   base,caller=rd('i'),rd('i');assert 0<=base<1024 and 0<caller<=1024 and base+caller<=1024;op=text();node=tensor();sources=rd('I');assert sources<=16;node.update(phase='PREFILL',op=op,sources=[tensor()for _ in range(sources)],caller_rows=caller,first_position=base,observed_occurrences=1,visible_keys_by_causal_row=list(range(base+1,base+caller+1)),visible_keys_basis='First exact descriptor instance; all instances remain in original bound journal and physical executions')
   assert offset==len(payload)and node['device']=='NVIDIA RTX A5000';unique[key]=node
 assert count==info['records'];return list(unique.values()),dict(records=count,unique=len(unique),raw_sha256=info['sha256'],all_original_fields_reconstructed=True,scope='Metadata reconstruction only; full vectors/active KV remain independently checked')
