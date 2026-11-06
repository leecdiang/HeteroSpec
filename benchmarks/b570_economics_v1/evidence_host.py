"""Read-through PR187 codec/banks; all new writes stay in this study's root."""
from native_host import *
sys.path.insert(0,str(PREVIOUS))
import smol_state as codec
import numpy as np

def native_path(value):
 p=Path(value)
 if p.is_absolute() and ROOT.resolve() in p.resolve().parents:return p
 parts=PureWindowsPath(str(value)).parts
 allowed=(PureWindowsPath('I:/HeteroSpec/b570-decisive-20261105').parts,PureWindowsPath(str(OLD)).parts)
 assert any(tuple(x.lower() for x in parts[:len(a)])==tuple(x.lower() for x in a) for a in allowed),'Unexpected evidence root'
 return old_path(value)

def chunk(h):
 assert len(h)==64 and set(h)<=set('0123456789abcdef')
 if h in codec._chunks:
  x=codec._chunks.pop(h);codec._chunks[h]=x;return x[1]
 p=ROOT/'state-token-cas'/h[:2]/h
 if not p.exists():p=OSMOL/'state-token-cas'/h[:2]/h
 data=p.read_bytes();assert len(data)==196608 and hashlib.sha256(data).hexdigest()==h
 codec._chunks[h]=(None,data)
 if len(codec._chunks)>2048:codec._chunks.popitem(last=False)
 return data

def pack(path):
 p=native_path(path);assert ROOT.resolve() in p.resolve().parents
 raw=p.read_bytes();a,m=codec.decode(raw);assert codec.encode(a,m)==raw;hs=[]
 for row in a:
  b=row.tobytes();h=hashlib.sha256(b).hexdigest();out=ROOT/'state-token-cas'/h[:2]/h;old=OSMOL/'state-token-cas'/h[:2]/h
  if h in codec._chunks or out.exists() or old.exists():assert chunk(h)==b
  else:out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(b)
  hs.append(h)
 record=dict(format='smol-state-token-pack-v1',raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),tokens=hs,framing=m,source_path=p.name)
 b=np.stack([np.frombuffer(chunk(h),dtype='<u2').reshape(24,4096) for h in hs])
 assert hashlib.sha256(codec.encode(b,m)).hexdigest()==sha(p)
 write(str(p)+'.pack.json',record)
 codec._verified_states.add(codec.manifest_key(record))
 p.unlink() # Only this study's redundant flat copy, after exact reconstruction.

codec.native_path=native_path;codec.chunk=chunk
from smol_boundaries import verify as boundaries

def state_equal(x,y):
 return x['prefix']==y['prefix'] and codec.canonical_verified(x['sequence'])==codec.canonical_verified(y['sequence']) and native_path(x['frontier']).read_bytes()==native_path(y['frontier']).read_bytes()

def bank(group,index):
 key=('dev' if group=='development' else 'test')+'-'+str(index);out={}
 old=read(OLD_CAMPAIGN/'runs'/(key+'-oldR')/'0.json')
 assert old==read(OLD_CAMPAIGN/'runs'/(key+'-oldR')/'1.json')
 plan=read(OLD_CAMPAIGN/(key+'-FORCED_PLAN.json'))
 for j in range(len(plan['independent_token_only_jobs'])):
  d=read(OLD_CAMPAIGN/'runs'/(key+'-forced-'+str(j))/'0.json');assert not d['candidate_values_received']
  for x in d['prefixes']:
   k=tuple(x['prefix'])
   if k in out:assert native_path(out[k]['frontier']).read_bytes()==native_path(x['frontier']).read_bytes()
   if k not in out or 'sequence' in x:out[k]=x
 for receipt in sorted((ROOT/'reference'/f'{group}-{index}').glob('COMPLETE-*.json')):
  for p in read(receipt)['captures']:
   d=read(p);assert d['candidate_values_received'] is False
   for x in d['prefixes']:
    k=tuple(x['prefix'])
    if k in out:assert native_path(out[k]['frontier']).read_bytes()==native_path(x['frontier']).read_bytes()
    if k not in out or 'sequence' in x:out[k]=x
 return old,out

def qualify(row,arm,heavy,off,baseline=None):
 old,ref=bank(row['group'],row['index']);a=read(heavy/'1.json');b=read(off/'1.json')
 contract=boundaries(a,old,arm)
 assert (a['ids'],a['eog'])==(b['ids'],b['eog'])==(old['ids'],old['eog'])
 if arm=='M':assert a['commits']==old['commits']
 if baseline:
  z=read(baseline/'1.json');assert (b['prompt_ids'],b['ids'],b['eog'],b['commits'])==(z['prompt_ids'],z['ids'],z['eog'],z['commits'])
 missing=set(tuple(x['prefix']) for x in a['full_target_vectors']+a['committed_states'])-ref.keys()
 assert not missing,('NEW_REFERENCE_BRANCH_REQUIRED',len(missing))
 vals=[];states=[]
 for x in a['full_target_vectors']:
  raw=native_path(x['path']).read_bytes();assert len(raw)==49152*4 and np.isfinite(np.frombuffer(raw,dtype='<f4')).all()
  vals.append(raw==native_path(ref[tuple(x['prefix'])]['frontier']).read_bytes())
 for x in a['committed_states']:states.append(state_equal(x,ref[tuple(x['prefix'])]))
 bridge=state_equal(a['committed_states'][-1],b['committed_states'][-1])
 result=dict(input_id=row['id'],arm=arm,conditional_vectors=len(vals),equal_vectors=sum(vals),committed_states=len(states),equal_states=sum(states),heavy_off_final_equal=bridge,contract=contract,independent_R_unchanged=True)
 write(heavy/'QUALIFICATION.json',result)
 assert all(vals) and all(states) and bridge,result
 return result
