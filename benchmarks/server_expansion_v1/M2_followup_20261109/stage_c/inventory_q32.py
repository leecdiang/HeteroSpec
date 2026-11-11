"""GGUF header/type inventory only: no tensor payload read, model or CUDA."""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,math,re,struct
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',type=Path,required=True);p.add_argument('--enum-header',type=Path,required=True);p.add_argument('--verified-receipt',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 header=a.enum_header.read_text();start=header.index('enum ggml_type');end=header.index('};',start)
 names={int(n):s for s,n in re.findall(r'GGML_TYPE_([A-Z0-9_]+)\s*=\s*(\d+)',header[start:end])}
 with a.model.open('rb')as f:
  def rd(fmt):
   n=struct.calcsize('<'+fmt);b=f.read(n);assert len(b)==n;return struct.unpack('<'+fmt,b)[0]
  def string(keep=True):
   n=rd('Q');assert n<64*1024**2
   if not keep:f.seek(n,1);return None
   return f.read(n).decode('utf8')
  formats={0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}
  def value(t,keep=False):
   if t in formats:return rd(formats[t])
   if t==8:return string(keep)
   assert t==9;sub=rd('I');count=rd('Q');assert count<2000000
   if sub in formats:f.seek(count*struct.calcsize('<'+formats[sub]),1)
   else:
    for _ in range(count):value(sub,False)
   return dict(array_type=sub,length=count)
  assert f.read(4)==b'GGUF';version=rd('I');assert version in(2,3);nt=rd('Q');nk=rd('Q');assert nk<10000 and nt<100000
  meta={}
  for _ in range(nk):
   key=string();t=rd('I');v=value(t,key in('general.architecture','general.file_type','general.quantization_version','general.license'));meta[key]=v
  types=Counter();elements=Counter();samples={}
  for _ in range(nt):
   name=string();dims=rd('I');assert 0<dims<=4;shape=[rd('Q')for _ in range(dims)];kind=rd('I');offset=rd('Q');assert kind in names
   label=names[kind];types[label]+=1;elements[label]+=math.prod(shape)
   samples.setdefault(label,[])
   if len(samples[label])<3:samples[label].append(dict(name=name,shape=shape))
  header_end=f.tell()
 arch=meta['general.architecture'];out=dict(schema='heterospec.q32.cpu-type-inventory.v1',status='METADATA_ONLY_NO_GPU',file=a.model.name,bytes=a.model.stat().st_size,GGUF_version=version,architecture=arch,
  tensors=nt,tensor_counts=dict(types),logical_tensor_elements=dict(elements),tensor_examples=samples,layers=meta.get(arch+'.block_count'),declared_file_type=meta.get('general.file_type'),quantization_version=meta.get('general.quantization_version'),declared_license=meta.get('general.license'),
  header_bytes_read_or_skipped=header_end,payload_bytes_read=0,enum_header_sha256=hashlib.sha256(a.enum_header.read_bytes()).hexdigest(),prior_full_verification_receipt_sha256=hashlib.sha256(a.verified_receipt.read_bytes()).hexdigest(),
  full_GGUF_SHA256_recomputed_in_this_inventory=False,prior_pinned_model_sha256='efd971561896866f0e910cce52761ca77b1b138090c7f15fe284676d57d1f689',
  qualification='No arithmetic/reference/state/forward/performance work. B/C qualify only the original8B Q8_0 target. Mixed types/model size need their own independent32B scalar R and full eligibility.',new_GPU_requests=0)
 assert out['bytes']==19762149024,'Different file, do not substitute'
 with a.out.open('x')as f:json.dump(out,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps(out))
if __name__=='__main__':main()
