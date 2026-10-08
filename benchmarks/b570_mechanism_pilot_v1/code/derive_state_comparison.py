"""CPU-only inherited tensor comparison using the independent state binary parser."""
from pathlib import Path
import json,hashlib
import numpy as np
import validate_B as p
R=Path(__file__).parent
manifest=json.loads((R/'B_MANIFEST.json').read_text(encoding='utf8'));rows=[]
for c in manifest['cases']:
 if c['status']!='ALIGNED':continue
 states=[]
 for d in c['donors']:
  f=R/(d['checkpoint'][:-5]+'.target.kv');states.append(p.kv(f))
 a,b=states;assert a['positions']==b['positions'] and a['layers']==b['layers'] and len(a['tensors'])==len(b['tensors'])
 tensors=[]
 for i,(x,y) in enumerate(zip(a['tensors'],b['tensors'])):
  u=np.frombuffer(x,dtype='<f2');v=np.frombuffer(y,dtype='<f2');assert len(u)==len(v) and np.isfinite(u).all() and np.isfinite(v).all()
  tensors.append(dict(role='key' if i<a['layers'] else 'value',layer=i%a['layers'],elements=len(u),changed_fp16_bits=int(np.count_nonzero(u.view('<u2')!=v.view('<u2'))),max_abs_numeric_difference=float(np.max(np.abs(u.astype('float64')-v.astype('float64'))))))
 rows.append(dict(task=c['task'],round=c['round'],committed_length=c['committed_length'],donors=[d['label'] for d in c['donors']],target_state_sha256=[s['sha256'] for s in states],same_logical_positions=True,primary_common_batch_prefix_reference_aligned=c['primary_batch_prefix_reference_aligned'],changed_elements=sum(t['changed_fp16_bits'] for t in tensors),tensors=tensors))
assert not p.errors,p.errors
(R/'DONOR_STATE_COMPARISON.json').write_text(json.dumps(dict(status='PASS',independent_state_parser_checks=p.checks,rows=rows,scope='Real inherited serialized target KV tensors only; no layer/kernel causal isolation and no model computation'),indent=2)+'\n',encoding='utf8')
print([(r['task'],r['round'],r['changed_elements'],r['primary_common_batch_prefix_reference_aligned']) for r in rows])
