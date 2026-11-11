"""Source-consistent serialized F16 K/V geometry and FP64 numerical distances."""
from __future__ import annotations
import argparse,struct
from pathlib import Path
import numpy as np
from contracts import require,read,write,Resolver,CASES,STATES

def layout(data,n):
 require(type(n)is int and 0<n<=768,'invalid cells');c=0
 def take(fmt):
  nonlocal c
  size=struct.calcsize('<'+fmt);require(c+size<=len(data),'truncated header');v=struct.unpack_from('<'+fmt,data,c)[0];c+=size;return v
 require(take('I')==0xaf143cd8 and take('i')==0 and take('I')==1 and take('I')==n,'state contract')
 for pos in range(n):require((take('i'),take('I'),take('i'))==(pos,1,0),'position/sequence metadata')
 trans=take('I');require(trans in (0,1) and take('I')==32,'layer/layout mismatch');ts=[];meta=[];previous=0
 for role in ('K','V'):
  for layer in range(32):
   require(take('i')==1,'not F16')
   if role=='V' and trans:require(take('I')==2 and take('I')==1024,'V extent')
   else:require(take('Q')==2048,'row width')
   meta.append((previous,c));size=n*2048;require(c+size<=len(data),'cropped tensor');ts.append({'role':role,'layer':layer,'offset':c,'bytes':size,'transposed':role=='V' and bool(trans)});c+=size;previous=c
 require(c==len(data),'extended tensor');return {'n':n,'tensors':ts,'metadata':meta,'heads':8,'channels':128,'v_transposed':bool(trans)}
def tensor_bits(data,t,n):
 b=np.frombuffer(data,dtype='<u2',count=n*1024,offset=t['offset'])
 return (b.reshape(1024,n).T if t['transposed'] else b.reshape(n,1024)).reshape(n,8,128)
def selector_geometry(name,n):
 require(name in (*STATES,'K_all','V_all','KV_early','KV_middle','KV_late'),'unknown historical selector');roles={'K'} if name.startswith('K_') else {'V'} if name.startswith('V_') else {'K','V'};layers=range(1) if name.endswith('layer0') else range(32);positions=range(n)
 if name=='KV_early':layers=range(0,8)
 if name=='KV_middle':layers=range(8,24)
 if name=='KV_late':layers=range(24,32)
 if name=='EMPTY':positions=range(0)
 if name=='KV_prefix128':positions=range(min(128,n))
 if name=='KV_tail128':positions=range(min(128,n),n)
 return roles,layers,positions
def splice(recipient,donor,n,name):
 l,r=layout(recipient,n),layout(donor,n);require(l==r and all(recipient[a:b]==donor[a:b] for a,b in l['metadata']),'metadata/geometry differs');out=bytearray(recipient);roles,layers,positions=selector_geometry(name,n)
 if positions:
  lo,hi=positions.start,positions.stop
  for t in l['tensors']:
   if t['role'] not in roles or t['layer'] not in layers:continue
   if t['transposed']:
    for f in range(1024):a=t['offset']+2*(f*n+lo);b=t['offset']+2*(f*n+hi);out[a:b]=donor[a:b]
   else:a=t['offset']+2048*lo;b=t['offset']+2048*hi;out[a:b]=donor[a:b]
 return bytes(out)
def ordered(bits):
 # Standard sign-aware ordered encoding; signed zeros are adjacent, distance one.
 b=bits.astype(np.uint16);return np.where(b&0x8000,(~b)&0xffff,b^0x8000).astype(np.int32)
def metrics(a,b):
 a=np.asarray(a,dtype=np.uint16).ravel();b=np.asarray(b,dtype=np.uint16).ravel();require(a.shape==b.shape,'different extents');fa=a.view(np.float16).astype(np.float64);fb=b.view(np.float16).astype(np.float64)
 require(np.isfinite(fa).all() and np.isfinite(fb).all(),'nonfinite F16 state')
 if not a.size:return {'elements':0,'selected_bytes':0,'changed_bytes':0,'changed_F16_elements':0,'numerically_unequal_elements':0,'finite':True,'max_absolute_error':0.,'rms_absolute_error':None,'L2_relative_error':None,'reference_norm_zero':True,'ordered_ULP_histogram':{},'zero_reference':0,'zero_donor':0,'sign_bit_changes':0,'signed_zero_changes':0}
 diff=fb-fa;norm=float(np.linalg.norm(fa));ulp=np.abs(ordered(b)-ordered(a));uv,counts=np.unique(ulp,return_counts=True)
 return {'elements':int(a.size),'selected_bytes':int(2*a.size),'changed_bytes':int(np.count_nonzero(a.view(np.uint8)!=b.view(np.uint8))),'changed_F16_elements':int(np.count_nonzero(a!=b)),'numerically_unequal_elements':int(np.count_nonzero(fa!=fb)),'finite':True,'max_absolute_error':float(np.max(np.abs(diff))),'rms_absolute_error':float(np.sqrt(np.mean(diff*diff,dtype=np.float64))),'L2_absolute_error':float(np.linalg.norm(diff)),'L2_reference_norm':norm,'L2_relative_error':float(np.linalg.norm(diff)/norm) if norm!=0 else None,'reference_norm_zero':norm==0,'ordered_ULP_histogram':{str(int(u)):int(c) for u,c in zip(uv,counts)},'ordered_ULP_max':int(np.max(ulp)),'zero_reference':int(np.count_nonzero(fa==0)),'zero_donor':int(np.count_nonzero(fb==0)),'sign_bit_changes':int(np.count_nonzero((a^b)&0x8000)),'signed_zero_changes':int(np.count_nonzero((fa==0)&(fb==0)&(a!=b))),'nonzero_numeric_sign_changes':int(np.count_nonzero((fa!=0)&(fb!=0)&(np.signbit(fa)!=np.signbit(fb))))}
def compare_states(recipient,donor,n,name):
 l=layout(recipient,n);require(layout(donor,n)==l,'layout differs');roles,layers,positions=selector_geometry(name,n);aa=[];bb=[]
 for t in l['tensors']:
  if t['role'] in roles and t['layer'] in layers and positions:
   aa.append(tensor_bits(recipient,t,n)[positions.start:positions.stop].ravel());bb.append(tensor_bits(donor,t,n)[positions.start:positions.stop].ravel())
 return metrics(np.concatenate(aa) if aa else np.array([],dtype=np.uint16),np.concatenate(bb) if bb else np.array([],dtype=np.uint16))
def run(fresh,dest):
 frozen=read(fresh/'FREEZE.json');original=Path(next(x['path'] for x in frozen['inputs'] if Path(x['path']).name=='PLAN.json')).parent;res=Resolver(fresh,original);plan=read(fresh/'PLAN.json');ds=read(fresh/'DONORS.json');rows=[];detail=[]
 for task in CASES:
  n=len(plan['cases'][task]['prompt_ids']);states={side:res.payload(dict(ds[task+'|'+side]['KV'],path='baseline/pr99/'+ds[task+'|'+side]['KV']['path'])) for side in ('A','B')}
  for recipient in ('A','B'):
   donor='B' if recipient=='A' else 'A'
   for selector in STATES:rows.append({'task':task,'direction':donor+'->'+recipient,'selector':selector,'full_KV_value_bytes':64*n*2048,'selected_fraction_denominator':'all 64*n*2048 K/V value bytes; immutable metadata excluded',**compare_states(states[recipient],states[donor],n,selector)})
  desc=layout(states['A'],n)
  for t in desc['tensors']:
   a=tensor_bits(states['A'],t,n);b=tensor_bits(states['B'],t,n)
   af=a.view(np.float16).astype(np.float64);bf=b.view(np.float16).astype(np.float64);d=bf-af;coord=np.unravel_index(int(np.argmax(np.abs(d))),d.shape)
   detail.append({'task':task,'recipient':'A','donor':'B','role':t['role'],'layer':t['layer'],'heads':[0,8],'channels':[0,128],'positions':[0,n],**metrics(a,b),'max_error_coordinate':{'position':int(coord[0]),'head':int(coord[1]),'channel':int(coord[2])},'position_RMS':np.sqrt(np.mean(d*d,axis=(1,2))).tolist(),'position_max_absolute':np.max(np.abs(d),axis=(1,2)).tolist(),'head_RMS':np.sqrt(np.mean(d*d,axis=(0,2))).tolist(),'channel_RMS':np.sqrt(np.mean(d*d,axis=(0,1))).tolist()})
 write(dest,{'arithmetic':'stored F16 decoded to exact FP64; no epsilon in relative denominator','ULP_rule':'negative bitwise complement; positive sign-toggle; signed zeros adjacent at distance one; finite only','geometry':'K token-major [N,8,128]; V feature-major [1024,N], exposed as [N,8,128] with logical strides K=(2048,256,2), V=(2,128*N*2,N*2)','geometry_provenance':'PR101 llama-kv-cache state_write_data/cpy_k/cpy_v plus native stderr n_head_kv=8, n_embd_head_k/v=128; source and stderr pinned by raw audit','rows':rows,'role_layer_head_rows':detail})
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--fresh',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();run(a.fresh,a.output)
