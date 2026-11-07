"""Pure stdlib logical alignment; never imports executor and never executes native code."""
import json,hashlib,struct,itertools,collections,math
from pathlib import Path
def load(p):return json.loads(Path(p).read_bytes())
def raw(root,p):
 b=(root/p['path']).read_bytes();assert len(b)==p['bytes'] and hashlib.sha256(b).hexdigest()==p['sha256'];return b
def groups(root,tensors,prompt):
 groups=[];g=None;offset=0;stale=[]
 for t in tensors:
  emb=t['op']=='GET_ROWS' and t['operands'] and t['operands'][0]['name']=='token_embd.weight'
  if emb:
   assert t['ne'][1]==t['micrograph_width'];width=t['ne'][1]
   ids=struct.unpack('<'+'i'*width,raw(root,t['operands'][1]['payload']))
   assert list(ids)==prompt[offset:offset+width]
   if t['micrograph_pos']!=offset:stale.append(dict(recorded=t['micrograph_pos'],derived=offset,width=width))
   g=dict(pos=offset,width=width,tensors=[],tokens=list(ids));groups.append(g);offset+=width
  assert g is not None,'No actual embedding graph anchor'
  if t['op']=='ROPE' and len(t['operands'])>1:
   posraw=raw(root,t['operands'][1]['payload']);poss=list(struct.unpack('<'+'i'*(len(posraw)//4),posraw))
   assert poss==list(range(g['pos'],g['pos']+g['width'])),'Actual native logical positions differ'
  g['tensors'].append(t)
 assert offset==len(prompt),'Missing actual physical graph rows'
 return groups,stale
def dense_rows(root,t,width):
 assert t['payload'] and t['dtype'] in ['f32','f16','i32']
 ne=t['ne'];nb=t['nb'];size={'f32':4,'f16':2,'i32':4}[t['dtype']]
 # source-defined projected 2D or reshaped Q/K/V/ROPE axis2; padded score row differences excluded.
 axis=1 if ne[1]==width and ne[2]==1 and ne[3]==1 else 2 if ne[2]==width and ne[3]==1 else None
 if axis is None:return None
 b=raw(root,t['payload']);dims=[i for i in range(4) if i!=axis];rows=[]
 for token in range(width):
  row=bytearray()
  # canonical logical order ne0 fastest, no contiguous-buffer assumption
  for idx in itertools.product(*[range(ne[i]) for i in reversed(dims)]):
   inds=dict(zip(reversed(dims),idx));off=token*nb[axis]+sum(inds[i]*nb[i] for i in dims)
   assert off+size<=len(b);row.extend(b[off:off+size])
  rows.append(bytes(row))
 return rows
def aligned(root,gs,select):
 values=[];metadata=[]
 for g in gs:
  matches=[t for t in g['tensors'] if select(t)]
  if len(matches)!=1:return None
  t=matches[0];rows=dense_rows(root,t,g['width'])
  if rows is None:return None
  values+=rows;metadata.append({k:t[k] for k in ['name','op','dtype','ne','nb','buffer_type','device','op_params_sha256']})
 return dict(bytes=b''.join(values),rows=values,dtype=matches[0]['dtype'],metadata=metadata)
def stats(a,b,dtype):
 assert len(a)==len(b);size={'f32':4,'f16':2,'i32':4}[dtype];fmt={'f32':'f','f16':'e','i32':'i'}[dtype];N=len(a)//size
 first=next((i for i in range(N) if a[i*size:(i+1)*size]!=b[i*size:(i+1)*size]),None)
 fa=struct.unpack('<'+str(N)+fmt,a);fb=struct.unpack('<'+str(N)+fmt,b);ds=[abs(x-y) for x,y in zip(fa,fb)]
 finite=all(math.isfinite(x) for x in fa+fb)
 return dict(bitwise_equal=a==b,elements=N,unequal_bit_elements=sum(a[i*size:(i+1)*size]!=b[i*size:(i+1)*size] for i in range(N)),first_bitwise_divergent_element=first,finite=finite,max_abs=max(ds,default=0) if finite else None,max_rel=max((d/max(abs(x),abs(y),1e-30) for d,x,y in zip(ds,fa,fb)),default=0) if finite else None)
def native_ops(root,records):
 results=[];hist=load(root/'baseline/pr99/STUDY_RECORDS.json');guards=[]
 selectors=[('embedding',lambda t:t['op']=='GET_ROWS' and t['operands'] and t['operands'][0]['name']=='token_embd.weight'),('RMS_norm',lambda t:t['name']=='norm-0' and t['op']=='RMS_NORM'),('norm_weight_mul',lambda t:t['name']=='attn_norm-0' and t['op']=='MUL'),('Q_projection',lambda t:t['name']=='Qcur-0' and t['op']=='MUL_MAT'),('K_projection',lambda t:t['name']=='Kcur-0' and t['op']=='MUL_MAT'),('V_projection',lambda t:t['name']=='Vcur-0' and t['op']=='MUL_MAT'),('Q_RoPE',lambda t:t['name']=='Qcur-0' and t['op']=='ROPE'),('K_RoPE',lambda t:t['name']=='Kcur-0' and t['op']=='ROPE')]
 def endpoint(x):return {k:x[k] for k in ['ids','eog','length','terminal_id','stop_reason','cap']}
 for r in [x for x in records if x['phase']=='P1C']:
  x=load(root/r['raw_path']);old=next(t for t in hist if t['task']==r['task'] and t['arm']==r['arm'] and t['repeat']==0);ref=load(root/'baseline/pr99'/old['raw_path']);guards.append(dict(slot=r['slot'],full_endpoint_equal=endpoint(x)==endpoint(ref)))
 guard=all(g['full_endpoint_equal'] for g in guards) and len(guards)==18
 for task in ['GSM8K/test/1248','GSM8K/test/831']:
  for rep in [1,2]:
   raws={r['arm']:load(root/r['raw_path']) for r in records if r['phase']=='P1C' and r['task']==task and r['repeat']==rep}
   if set(raws)!=set('ABC'):results.append(dict(task=task,repeat=rep,status='UNRESOLVED_INCOMPLETE_GRID'));continue
   sets={};stales={}
   for arm,x in raws.items():sets[arm],stales[arm]=groups(root,x['operator100']['tensors'],x['prompt_ids'])
   comparisons=[]
   for label,select in selectors:
    vals={a:aligned(root,g,select) for a,g in sets.items()}
    if any(v is None for v in vals.values()):comparisons.append(dict(operator=label,status='UNKNOWN_NOT_COMPARABLE'));continue
    assert len(vals['A']['rows'])==len(raws['A']['prompt_ids'])
    row=dict(operator=label,status='COMPARABLE',A_B=stats(vals['A']['bytes'],vals['B']['bytes'],vals['A']['dtype']),B_C=stats(vals['B']['bytes'],vals['C']['bytes'],vals['B']['dtype']),metadata={a:v['metadata'] for a,v in vals.items()})
    # Exactly compare aligned dynamic input + actual static operand bytehash when operator src arrays are available.
    if label!='embedding':
     operand_checks=[]
     for si in range(min(len(sets['A'][0]['tensors']),1)):pass
     for arm,g in sets.items():
      selected=next(t for t in g[0]['tensors'] if select(t));operand_checks.append(dict(arm=arm,source_operands=[dict(name=o['name'],dtype=o['dtype'],ne=o['ne'],nb=o['nb'],payload=o['payload']) for o in selected['operands']]))
     row['source_operands']=operand_checks
    comparisons.append(row)
   first=next((c['operator'] for c in comparisons if c['status']=='COMPARABLE' and not c['A_B']['bitwise_equal']),None)
   results.append(dict(task=task,repeat=rep,status='SUPPORTED_NATIVE_LOCATION' if first and guard else 'UNRESOLVED',first_comparable_divergence=first,first_scope='Registered embedding/RMS/scale/QKV source dataflow; sibling projection order does not identify unique kernel; actual shader/dispatch UNKNOWN',comparisons=comparisons,stale_non_authoritative_metadata=stales,physical_widths={a:[g['width'] for g in gs] for a,gs in sets.items()}))
 return dict(status='SUPPORTED_NATIVE_LOCATION' if guard and all(r.get('first_comparable_divergence') for r in results) else 'UNRESOLVED',full_endpoint_observer_guard=guard,guards=guards,cases=results,later_attention_FFN='Raw named layer0 operands/payloads preserved; paddedscore alignment and unique shader identification UNRESOLVED; first-divergence search stops on upstream matched-source divergence',actual_shader_pipeline=None,dispatch_dimensions=None)
