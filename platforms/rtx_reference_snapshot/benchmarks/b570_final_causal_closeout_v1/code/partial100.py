from pathlib import Path
import sys,json
import verify100 as v
root=Path(sys.argv[1]);rs=v.load(root/'STUDY_RECORDS.json')
for r in rs:
 x=v.load(root/r['raw_path']);v.endpoint100(x,x['prompt_ids'],x['actual_condition']['prefill_ub'],r['owned_pid'],x['restore100'] is not None)
 if r['observation_mode']=='heavy':
  v.geometry100(v.load(root/r['evidence_path']),x,x['prompt_ids'],x['actual_condition']['prefill_ub'],x['partition100']['caller_lengths']);v.snapshots(root,x)
print(json.dumps(dict(status='PASS',completed_checked=len(rs),model_forwards=0)))
