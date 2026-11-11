import verify98 as v
from pathlib import Path
R=Path(__file__).resolve().parents[1]
rs=v.load(R/'STUDY_RECORDS.json');p=v.load(R/'PLAN.json');checked=0
for r in rs:
 x=v.load(R/r['raw_path']);a=p['arms'][r['arm']];v.endpoint(x,x['prompt_ids'],a['ub'],r['owned_pid'])
 if r['observation_mode']=='heavy':
  t=v.load(R/r['evidence_path']);v.geometry(t,x,x['prompt_ids'],a['ub'],a['partition'])
  for b in x['phase96']['boundaries']:
   raw=v.payload(R,x['partition98']['full_payloads'][str(b['output_index_zero_based'])]['logits'])
   f,i,j=v.top2(raw);assert i==b['sampled_top1_id'] and j==b['top2_id']
 checked+=1
print('PARTIAL_CLOSED_REQUEST_ENDPOINT_GEOMETRY_PAYLOAD_CHECK',checked)
