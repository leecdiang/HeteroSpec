#!/usr/bin/env python3
"""Read old captured bytes; never execute CUDA or claim frozen quantizer identity.
Requires Python 3 and NumPy. Input files must be the fixed PR171 evidence files.
Outputs are CPU parsing/comparisons and explicitly counterfactual RN quantization.
"""
import argparse,base64,binascii,ctypes,gzip,hashlib,json,pathlib,platform,sys
import numpy as np

FIXED171='371223b696bb805030c29f04e39eb17b57fb2ebb'
FIXED181='44625c8d53b8a7cc694d9c25a197858424d63197'
EXPECTED={
 'operands.json.gz':('bff60fbaac437421ad4ded651cc7b94d7ddaa1245fa279e7cb7fc8b40845aed5','07f27b38b4ac219c7665cabc6f76e22a1dd848ae',17925),
 'operand-sample.json.gz':('d1a7686e44cc85eb074e01b6471c44a20e81a72c1fbff7ab001c72286486c2a8','9fcced0000546b1d377c47de2c7b0b7af040be02',5502833)}
def sha(b):return hashlib.sha256(b).hexdigest()
class ValidationError(ValueError):
 """Input validation remains active under python -O and -OO."""
def require(condition,message):
 if not condition:raise ValidationError(message)
def require_rounding_mode(mode):
 require(mode==0,'Require FE_TONEAREST')
def validate_compressed(name,b):
 require(name in EXPECTED,f'Unknown evidence file: {name}')
 digest,blobsha,size=EXPECTED[name]
 require(len(b)==size,f'{name}: compressed byte length mismatch')
 require(sha(b)==digest,f'{name}: compressed SHA256 mismatch')
 gitsha=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 require(gitsha==blobsha,f'{name}: Git blob SHA1 mismatch')
 raw=gzip.decompress(b)
 return json.loads(raw),dict(bytes=len(b),sha256=sha(b),git_blob_sha1=gitsha,decompressed_bytes=len(raw),decompressed_sha256=sha(raw))
def decode_blob(b64,digest,size,label):
 try:b=base64.b64decode(b64,validate=True)
 except (binascii.Error,ValueError,TypeError) as exc:raise ValidationError(f'{label}: invalid base64') from exc
 require(len(b)==size,f'{label}: decoded byte length mismatch')
 require(sha(b)==digest,f'{label}: decoded SHA256 mismatch')
 return b
def one(items,label):
 require(len(items)==1,f'{label}: expected exactly one matching record')
 return items[0]
def validate_descriptor(e):
 w=e['descriptor']['weight'];i=e['descriptor']['input'];o=e['descriptor']['output'];K,M=w['ne'][:2];N=i['ne'][1]
 require(all(type(n) is int and n>0 for n in (K,M,N)) and K%32==0,'Invalid descriptor dimensions')
 require(w['type']==8 and i['type']==o['type']==0,'Descriptor tensor type mismatch')
 require(w['ne']==[K,M,1,1] and i['ne']==[K,N,1,1] and o['ne']==[M,N,1,1],'Descriptor tensor shape mismatch')
 require(w['bytes']==K*M//32*34 and i['bytes']==K*N*4 and o['bytes']==M*N*4,'Descriptor byte size mismatch')
 require(w['nb']==[34,K//32*34,w['bytes'],w['bytes']] and i['nb']==[4,K*4,i['bytes'],i['bytes']] and o['nb']==[4,M*4,o['bytes'],o['bytes']],'Descriptor stride mismatch')
 return w,i,o,K,M,N
def stats(a):
 u=a.view('<u4'); tiny=np.finfo(np.float32).tiny
 return dict(count=a.size,finite=int(np.isfinite(a).sum()),nan=int(np.isnan(a).sum()),inf=int(np.isinf(a).sum()),positive_zero=int((u==0).sum()),negative_zero=int((u==0x80000000).sum()),subnormal=int(((abs(a)<tiny)&(a!=0)).sum()),min=float(a.min()),max=float(a.max()))
def compare(a,b,M):
 require(a.ndim==b.ndim==1 and a.dtype==b.dtype==np.dtype('<f4'),'Comparison requires 1D little-endian F32 arrays')
 require(type(M) is int and M>0 and a.size>0 and a.size==b.size and a.size%M==0,'Comparison shape mismatch')
 require(np.isfinite(a).all() and np.isfinite(b).all(),'Comparison requires finite values')
 ua=a.view('<u4');ub=b.view('<u4');mask=ua!=ub
 def order(u):return np.where(u&0x80000000,(~u)&0xffffffff,u|0x80000000).astype(np.int64)
 delta=abs(order(ua)-order(ub));diff=abs(a.astype('f8')-b.astype('f8'))
 witness=[]
 for k in np.flatnonzero(mask)[:5]:
  witness.append(dict(column=int(k)//M,row=int(k)%M,a_bits=f'0x{int(ua[k]):08x}',b_bits=f'0x{int(ub[k]):08x}',a=float(a[k]),b=float(b[k]),ulp_distance=int(delta[k])))
 return dict(total=int(a.size),bit_mismatches=int(mask.sum()),max_ulp_distance=int(delta.max()),max_absolute_difference=float(diff.max()),first_mismatches=witness)
def adjacent(x,direction,count=4):
 x=x.copy();target=np.float32(direction)
 for _ in range(count):x=np.nextafter(x,target,dtype=np.float32)
 return x

def nominal_quantizer(x,K):
 # The source's sum is an XOR butterfly, NOT sequential sum/np.sum.
 require(x.ndim==1 and x.dtype==np.dtype('<f4'),'Quantizer probe requires a 1D little-endian F32 array')
 require(type(K) is int and K>0 and K%32==0 and x.size>0 and x.size%K==0,'Quantizer probe shape mismatch')
 require(np.isfinite(x).all(),'Quantizer probe requires finite input')
 blocks=x.reshape(-1,32);amax=abs(blocks).max(axis=1)
 require((amax>0).all(),'This probe only handles the observed nonzero blocks')
 sums=blocks.copy()
 for offset in [16,8,4,2,1]:sums=np.add(sums,sums[:,np.arange(32)^offset],dtype=np.float32)
 d=np.divide(amax,np.float32(127),dtype=np.float32)
 ratio=np.divide(blocks,d[:,None],dtype=np.float32)
 # roundf to signed integer: exact +0.5 in f64 for observed |ratio|<=128.
 q=(np.sign(ratio)*np.floor(abs(ratio).astype('f8')+0.5)).astype('i1')
 dh=d.astype('<f2');sh=sums[:,0].astype('<f2')
 packed=np.empty((len(d),36),dtype='u1');packed[:,0:2]=dh.view('u1').reshape(-1,2);packed[:,2:4]=sh.view('u1').reshape(-1,2);packed[:,4:]=q.view('u1')
 # Sensitivity probe only. +/-4 representable steps is not an implementation
 # of div.approx or a proof that either endpoint is a real GPU result.
 dlo=adjacent(d,-np.inf);dhi=adjacent(d,np.inf)
 rlo=adjacent(np.divide(abs(blocks),dhi[:,None],dtype=np.float32),-np.inf)
 rhi=adjacent(np.divide(abs(blocks),dlo[:,None],dtype=np.float32),np.inf)
 qlo=np.floor(rlo.astype('f8')+0.5);qhi=np.floor(rhi.astype('f8')+0.5)
 unstable=qlo!=qhi;scaleunstable=dlo.astype('<f2').view('<u2')!=dhi.astype('<f2').view('<u2')
 variants=[]
 # Additional counterfactual: float32 rounded reciprocal multiplication.
 # This is NOT a GPU rcp.approx/div.approx implementation.
 dr=np.multiply(amax,np.divide(np.float32(1),np.float32(127),dtype=np.float32),dtype=np.float32)
 for scale_label,dd in [('RN_div_scale',d),('RN_reciprocal_multiply_scale',dr)]:
  for ratio_label,rr in [('RN_div_ratio',np.divide(blocks,dd[:,None],dtype=np.float32)),('RN_reciprocal_multiply_ratio',np.multiply(blocks,np.reciprocal(dd,dtype=np.float32)[:,None],dtype=np.float32))]:
   qq=(np.sign(rr)*np.floor(abs(rr).astype('f8')+0.5)).astype('i1');changed=qq!=q
   examples=[]
   for bi,lane in np.argwhere(changed)[:3]:
    index=int(bi)*32+int(lane)
    examples.append(dict(column=index//K,k=index%K,x=float(blocks[bi,lane]),amax=float(amax[bi]),nominal_d=float(d[bi]),variant_d=float(dd[bi]),nominal_ratio=float(ratio[bi,lane]),variant_ratio=float(rr[bi,lane]),nominal_q=int(q[bi,lane]),variant_q=int(qq[bi,lane])))
   variants.append(dict(scale=scale_label,ratio=ratio_label,qbyte_differences_from_nominal=int(changed.sum()),half_scale_differences_from_nominal=int((dd.astype('<f2').view('<u2')!=dh.view('<u2')).sum()),examples=examples))
 witnesses=[]
 for bi,lane in np.argwhere(unstable)[:12]:
  index=int(bi)*32+int(lane)
  witnesses.append(dict(column=index//K,k=index%K,block=int(bi),lane=int(lane),x_bits=f'0x{int(blocks[bi,lane].view("u4")):08x}',x=float(blocks[bi,lane]),amax=float(amax[bi]),rn_d_bits=f'0x{int(d[bi].view("u4")):08x}',rn_d=float(d[bi]),rn_ratio=float(ratio[bi,lane]),abs_ratio_low=float(rlo[bi,lane]),abs_ratio_high=float(rhi[bi,lane]),qabs_low=int(qlo[bi,lane]),qabs_high=int(qhi[bi,lane])))
 return dict(status='COUNTERFACTUAL_HOST_RN_DIVISION_NOT_FROZEN_Q8_1',blocks=int(len(d)),q81_bytes=packed.size,nominal_q81_sha256=sha(packed.tobytes()),d_f32_range=[float(d.min()),float(d.max())],d_half_range=[float(dh.min()),float(dh.max())],d_half_nonfinite=int((~np.isfinite(dh)).sum()),d_half_zero=int((dh==0).sum()),d_half_subnormal=int(((abs(dh)<np.finfo('f2').tiny)&(dh!=0)).sum()),sum_half_nonfinite=int((~np.isfinite(sh)).sum()),sum_half_subnormal=int(((abs(sh)<np.finfo('f2').tiny)&(sh!=0)).sum()),scale_half_changed_under_4step_stress=int(scaleunstable.sum()),qbyte_unstable_under_4step_stress=int(unstable.sum()),unstable_blocks=int(np.any(unstable,axis=1).sum()),rounding_boundary_examples=witnesses,counterfactual_arithmetic_variants=variants)

def main():
 p=argparse.ArgumentParser();p.add_argument('--input-dir',type=pathlib.Path,default=pathlib.Path(__file__).parent);p.add_argument('--output',type=pathlib.Path);args=p.parse_args();root=args.input_dir
 # Verify process rounding mode; this is a CPU model, not GPU execution.
 libm=ctypes.CDLL('libm.so.6');require_rounding_mode(libm.fegetround())
 evidence={};parsed={}
 for name in EXPECTED:parsed[name],evidence[name]=validate_compressed(name,(root/name).read_bytes())
 desc=parsed['operands.json.gz'];sample=parsed['operand-sample.json.gz']
 require(isinstance(desc,list) and len(desc)==16,'Expected 16 descriptor records')
 require(isinstance(sample,dict) and set(sample)=={'blk.0.attn_q.weight','blk.0.ffn_down.weight'},'Unexpected sample operators')
 coverage=[]
 for e in desc:
  w,i,o,K,M,N=validate_descriptor(e)
  coverage.append(dict(model=e['model'],weight=w['name'],K=K,M=M,N=N,weight_bytes=w['bytes'],input_bytes=i['bytes'],output_bytes=o['bytes'],sample_available=e['model']=='8B' and w['name'] in sample))
 results={};totaldecoded=0
 for name,fields in sample.items():
  require(isinstance(fields,dict) and set(fields)=={'input','live32','scalar32','packed32','native8'},f'{name}: unexpected sample fields')
  row=one([e for e in desc if e['model']=='8B' and e['descriptor']['weight']['name']==name],name);K,M=row['descriptor']['weight']['ne'][:2]
  require(row['descriptor']['input']['ne'][1]==32,f'{name}: expected N32 input')
  expected={'input':row['inputs']['input'],'live32':row['inputs']['output']}
  expected.update({label:one([r for r in row['routes'] if r['q']==q and r['route']==route],f'{name}/{label}')['sha'] for label,q,route in [('scalar32',32,'scalar'),('packed32',32,'packed'),('native8',8,'wide')]})
  blobs={};arrays={}
  for label,b64 in fields.items():
   expectbytes=K*32*4 if label=='input' else M*(8 if label=='native8' else 32)*4
   b=decode_blob(b64,expected[label],expectbytes,f'{name}/{label}');totaldecoded+=len(b);a=np.frombuffer(b,dtype='<f4');arrays[label]=a
   blobs[label]=dict(bytes=len(b),sha256=sha(b),matches_fixed171_descriptor_or_route_hash=True,float32=stats(a))
  results[name]=dict(K=K,M=M,N=32,blobs=blobs,comparisons={
   'scalar32_vs_packed32':compare(arrays['scalar32'],arrays['packed32'],M),
   'scalar32_vs_live32':compare(arrays['scalar32'],arrays['live32'],M),
   'scalar_first8_vs_native8':compare(arrays['scalar32'][:M*8],arrays['native8'],M),
   'live_first8_vs_native8':compare(arrays['live32'][:M*8],arrays['native8'],M)},nominal_quantizer=nominal_quantizer(arrays['input'],K),missing_weight=dict(bytes=row['descriptor']['weight']['bytes'],sha256=row['inputs']['weight']))
 out=dict(status='OLD_CAPTURE_CPU_PARSE_AND_COUNTERFACTUAL_QUANTIZER_PROBE_NOT_PROJECTION_REPLAY',fixed171=FIXED171,candidate181=FIXED181,environment=dict(python=sys.version,numpy=np.__version__,platform=platform.platform(),rounding='FE_TONEAREST'),evidence=evidence,coverage=coverage,decoded_sample_bytes=totaldecoded,operators=results,limitations=['No actual Q8_0 weight payloads in downloaded evidence.','No frozen Q8_1 quantized activation bytes or their digest.','CPU RN division is not frozen div.approx.ftz or driver-JIT behavior.','No candidate projection executed; no CUDA/GPU execution.','Old scalar/packed equality is old captured evidence, not independent GPU reproduction or evidence for PR181.','Sensitivity endpoints are deliberately hypothetical; counts are not observed GPU quantization disagreements.'])
 dest=args.output or pathlib.Path(__file__).parent/'reproduced'/'probe_results.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(out,indent=2)+'\n');print(dest);print(json.dumps({k:{'comparisons':v['comparisons'],'quantizer':v['nominal_quantizer']} for k,v in results.items()},indent=2))
if __name__=='__main__':
 try:main()
 except (ValidationError,OSError,ValueError,KeyError,TypeError) as exc:
  print(f'PROBE VALIDATION FAILED: {exc}',file=sys.stderr)
  sys.exit(2)
