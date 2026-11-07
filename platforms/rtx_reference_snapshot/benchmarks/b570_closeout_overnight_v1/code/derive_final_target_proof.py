"""CPU-only derivation of final target caller/graph scope from paid captures."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
rows=[]
for r in read(ROOT/'G0_TARGET_FINAL_RESULTS.json'):
 if r['warm']:continue
 raw=read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json')));scopes=[]
 for role,phase in [('target','prefill'),('target','continuation')]:
  calls=[x for x in raw['trace'] if x['event']=='decode' and x['role']==role and x['phase']==phase]
  query=[g['ne1'] for call in calls for g in call['graphs'] if g['tensor']=='embd']
  scopes.append(dict(role=role,phase=phase,decode_calls=len(calls),caller_tokens=sum(c['caller_batch_length'] for c in calls),caller_range=[min(c['caller_batch_length'] for c in calls),max(c['caller_batch_length'] for c in calls)] if calls else None,occupied_query_range=[min(query),max(query)] if query else None))
 rows.append(dict(unit_id=r['unit_id'],task=r['task'],config=r['config'],scopes=scopes,raw_evidence_files=r['files']))
proof=dict(model_forwards=0,source='Already paid G0_TARGET_FINAL captures after the one-output reservation amendment',observations=rows,limitations=['Observed graph query rows are not unique Vulkan dispatch identity','Requested output reservation is source-bound, not an independent allocator measurement'],target_source_sha256=hashlib.sha256((ROOT/'src/target.cpp').read_bytes()).hexdigest())
(ROOT/'FINAL_TARGET_SCOPE_PROOF.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
