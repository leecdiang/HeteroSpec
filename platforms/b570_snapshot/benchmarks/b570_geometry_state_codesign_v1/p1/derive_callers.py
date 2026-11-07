"""Actual native caller events; never substitute them for physical VERIFY witnesses."""
import json,pathlib,collections,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,file_sha,write_new
plan=read_json(ROOT/'p0/PLAN_P1.json');slots={s['slot']:s for s in plan['slots']};rows=[]
for p in sorted((ROOT/'_host/run').glob('*/stdout.jsonl')):
 s=slots[p.parent.name];events=[(i+1,json.loads(line)) for i,line in enumerate(p.read_text(encoding='utf-8').splitlines())];hist=collections.Counter();examples={};starts=0;returns=0
 for line,e in events:
  if e.get('event')=='FORWARD_START':
   key=e['role']+'/'+e['phase']+'/rows'+str(e['caller_rows']);hist[key]+=1;starts+=1;examples.setdefault(key,dict(stdout_line=line,event=e))
  if e.get('event')=='FORWARD_RETURN':assert e['returncode']==0;returns+=1
 assert starts==returns
 rows.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],mode=s['mode'],stdout_sha256=file_sha(p),stdout_path=str(p.relative_to(ROOT)),observed_caller_width_hist=dict(hist),first_source_bound_example_per_role_phase_width=examples,caller_API_starts=starts,caller_API_returns_rc0=returns,scope='Observed caller metadata only. llama_decode return is not completed GPU kernel timing. No per-micrograph/VERIFY binding is inferred.',original_R_event_trace='NOT_INSTRUMENTED' if s['arm']=='R' else None))
write_new(ROOT/'p1/CALLER_OBSERVATIONS.json',dict(rows=rows,ordered_raw_events_retained_in_CAS=True,per_transaction_physical_VERIFY_micrograph_witness='NOT_OBSERVED',native_starts_added=0))
print('Caller event metadata reconstructed; physical VERIFY witness remains NOT_OBSERVED')
