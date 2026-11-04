"""Validate retained bytes and host RN domains; not a GPU div.approx emulator.

All integrity checks remain enabled under Python -O. Requires NumPy.
"""
import argparse,base64,binascii,gzip,hashlib,json
from pathlib import Path
import numpy as np
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--input-dir',type=Path,default=Path(__file__).parents[1],help='Directory containing authorized operands.json.gz and operand-sample.json.gz')
parser.add_argument('--output',type=Path,default=Path(__file__).with_name('verification.json'),help='Destination JSON; defaults beside this script')
args=parser.parse_args()
P=args.input_dir
manifest=json.load(gzip.open(P/'operands.json.gz'))
sample=json.load(gzip.open(P/'operand-sample.json.gz'))
sha=lambda b:hashlib.sha256(b).hexdigest()
def require(condition, message):
 if not condition:
  raise ValueError(message)
def decode_blob(value, name, key):
 try:
  return base64.b64decode(value, validate=True)
 except (binascii.Error, TypeError, ValueError) as exc:
  raise ValueError(f'{name}/{key}: invalid base64') from exc
expected_names={'blk.0.attn_q.weight','blk.0.ffn_down.weight'}
expected_blobs={'input','live32','scalar32','packed32','native8'}
expected_routes={(q,route) for q in (2,4,8,16,32) for route in ('scalar','wide','tile')+ (('packed',) if q>=8 else ())}
require(isinstance(manifest,list), 'manifest must be a list')
require(isinstance(sample,dict) and set(sample)==expected_names, 'sample operator set mismatch')
def arraystats(b):
 a=np.frombuffer(b,dtype='<f4'); u=a.view('<u4'); fin=np.isfinite(a); z=(u&0x7fffffff)==0; sub=((u&0x7f800000)==0)&~z
 return {'floats':int(a.size),'finite':int(fin.sum()),'nonfinite':int((~fin).sum()),'zero':int(z.sum()),'negative_zero':int((u==0x80000000).sum()),'subnormal':int(sub.sum()),'min':float(a.min()),'max':float(a.max()),'min_abs_nonzero':float(np.abs(a[~z]).min()),'max_abs':float(np.abs(a).max())}
def comparison(ba,bb,columns):
 a=np.frombuffer(ba,dtype='<f4'); b=np.frombuffer(bb,dtype='<f4'); n=min(a.size,b.size); a=a[:n];b=b[:n]
 ua=a.view('<u4');ub=b.view('<u4'); neq=ua!=ub; where=np.flatnonzero(neq); ad=np.abs(a.astype(np.float64)-b.astype(np.float64))
 def order(u):
  return np.where(u&np.uint32(0x80000000),np.uint32(0xffffffff)-u,u+np.uint32(0x80000000)).astype(np.int64)
 ulp=np.abs(order(ua)-order(ub))
 i=int(where[0]) if len(where) else None
 return {'compared_bytes':n*4,'compared_floats':n,'bit_mismatch_count':int(neq.sum()),'value_mismatch_count':int((a!=b).sum()),'equal_bytes':ba[:n*4]==bb[:n*4], 'max_abs_error':float(ad.max()),'rms_error':float(np.sqrt(np.mean(ad**2))),'max_ulp':int(ulp.max()),'mismatched_ulp_quantiles':{str(q):float(np.quantile(ulp[neq],q)) for q in [0,.5,.9,.99,1]} if len(where) else {},'first_mismatch':None if i is None else {'linear_index':i,'token':i//columns,'output_row':i%columns,'a':float(a[i]),'b':float(b[i]),'a_bits':f'0x{ua[i]:08x}','b_bits':f'0x{ub[i]:08x}'},'per_token_mismatch_count':neq.reshape(-1,columns).sum(axis=1).astype(int).tolist()}
result={'file_identities':{n:{'file_bytes':(P/n).stat().st_size,'file_sha256':sha((P/n).read_bytes())} for n in ['operands.json.gz','operand-sample.json.gz']},'manifest_records':len(manifest),'samples':{},'total_base64_blobs':sum(len(x) for x in sample.values()),'total_decoded_bytes':0}
for name,blobs in sample.items():
 require(isinstance(blobs,dict) and set(blobs)==expected_blobs, f'{name}: blob field set mismatch')
 rows=[r for r in manifest if r['model']=='8B' and r['descriptor']['weight']['name']==name]
 require(len(rows)==1, f'{name}: expected one 8B descriptor, found {len(rows)}')
 m=rows[0];rmap={(r['q'],r['route']):r for r in m['routes']};d=m['descriptor']
 require(len(rmap)==len(m['routes']), f'{name}: duplicate route records')
 require(set(rmap)==expected_routes, f'{name}: route set mismatch')
 raw={k:decode_blob(v,name,k) for k,v in blobs.items()}
 expected={'input':m['inputs']['input'],'live32':m['inputs']['output'],'scalar32':rmap[32,'scalar']['sha'],'packed32':rmap[32,'packed']['sha'],'native8':rmap[8,'wide']['sha']}
 require(rmap[32,'wide']['sha']==m['inputs']['output'], f'{name}: wide32/live output digest mismatch')
 nout=d['output']['ne'][0]
 rr={'descriptor':d,'missing_weight_sha256':m['inputs']['weight'],'blob_verification':{},'array_statistics':{},'comparisons':{},'prefix_manifest_checks':[]}
 for k,b in raw.items():
  size=d['input']['bytes'] if k=='input' else d['output']['bytes']//(4 if k=='native8' else 1)
  rr['blob_verification'][k]={'decoded_bytes':len(b),'expected_bytes':size,'length_matches':len(b)==size,'sha256':sha(b),'expected_sha256':expected[k],'digest_matches':sha(b)==expected[k]}
  require(len(b)==size, f'{name}/{k}: decoded byte length mismatch: {len(b)} != {size}')
  require(sha(b)==expected[k], f'{name}/{k}: SHA-256 digest mismatch')
  result['total_decoded_bytes']+=len(b)
  rr['array_statistics'][k]=arraystats(b)
 for a,b in [('scalar32','packed32'),('scalar32','live32'),('scalar32','native8'),('packed32','native8'),('live32','native8')]:
  rr['comparisons'][f'{a}_vs_{b}']=comparison(raw[a],raw[b],nout)
 # Every width scalar/packed/tile digest can be checked against the actual scalar32 prefix;
 # wide 2/4 similarly, and live-wide 16/32 similarly. Check only if raw prefix known.
 for route in m['routes']:
  q=route['q']; which='scalar32' if route['route'] in ('scalar','packed','tile') or (route['route']=='wide' and q<=4) else 'native8' if (route['route']=='wide' and q==8) else 'live32'
  actual=sha(raw[which][:q*nout*4]);rr['prefix_manifest_checks'].append({'q':q,'route':route['route'],'source':which,'digest_matches':actual==route['sha']})
 # Q8_1 domains visible without asserting a GPU quantizer replay.
 x=np.frombuffer(raw['input'],dtype='<f4').reshape(-1,32);am=np.max(np.abs(x),axis=1); ds=am/np.float32(127)
 rr['input_block32_domain']={'blocks':int(x.shape[0]),'zero_amax_blocks':int((am==0).sum()),'min_amax':float(am.min()),'max_amax':float(am.max()),'min_fp32_rn_division_scale':float(ds.min()),'max_fp32_rn_division_scale':float(ds.max()),'rn_scale_finite':bool(np.isfinite(ds).all()),'rn_scale_zero_count':int((ds==0).sum()),'rn_scale_subnormal_count':int(((ds>0)&(ds<np.finfo(np.float32).tiny)).sum()),'rn_half_scale_zero_count':int((ds.astype(np.float16)==0).sum()),'rn_half_scale_subnormal_count':int(((ds.astype(np.float16)>0)&(ds.astype(np.float16)<np.finfo(np.float16).tiny)).sum()),'max_abs_float64_exact_block_sum':float(np.abs(x.astype(np.float64).sum(axis=1)).max())}
 result['samples'][name]=rr
result['all_blob_verifications_pass']=all(x['length_matches'] and x['digest_matches'] for s in result['samples'].values() for x in s['blob_verification'].values())
result['all_prefix_manifest_checks_pass']=all(x['digest_matches'] for s in result['samples'].values() for x in s['prefix_manifest_checks'])
result['missing_weight_bytes']=sum(s['descriptor']['weight']['bytes'] for s in result['samples'].values())
require(result['total_base64_blobs']==10, 'expected exactly 10 base64 blobs')
require(result['all_blob_verifications_pass'], 'aggregate blob verification failed')
require(result['all_prefix_manifest_checks_pass'], 'aggregate route-prefix digest verification failed')
out=args.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
