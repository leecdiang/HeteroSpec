"""Final target-only controls; previously paid unchanged native proof is retained."""
from pathlib import Path
from campaign import read,save,stage,R,T,eq
ROOT=Path(__file__).parent
old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
tasks=['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/58']
inputs=[dict(id=t,prompt_ids=read(old[t]['ids'])) for t in tasks]
sessions=[dict(config=dict(R,cap=128,capture=True),inputs=inputs)]
sessions += [dict(config=dict(T,cap=128,capture=True,repetition=rep+1),inputs=inputs) for rep in range(2)]
sessions += [dict(config=dict(T,label=label,prefill=1,plain=plain,cap=128,capture=True),inputs=inputs) for label,plain in [('T_FINAL_PLAIN',True),('T_FINAL_SHAM',False)]]
sessions += [dict(config=dict(T,label='T_FINAL_WIDTH',k=k,ub=ub,cap=128,capture=True),inputs=[inputs[0],inputs[-1]]) for k,ub in [(1,2),(3,4),(5,6),(7,8)]]
rows=stage('G0_TARGET_FINAL',sessions);expected=read(ROOT/'dependencies/B570/HISTORICAL_EXPECTED.json');fail=[];width_observations=[]
for r in rows:
 if r['config']['prefill']==1:continue
 ref=expected[r['task']+'/R/1'];ref=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
 good=eq(r['endpoint'],ref)
 if r['config']['label']=='T_FINAL_WIDTH':width_observations.append(dict(unit_id=r['unit_id'],config=r['config'],reference_equal=good))
 elif not good:fail.append(r['unit_id'])
for task in tasks:
 rr=[r for r in rows if r['task']==task and r['config']['label'] in ['T_FINAL_PLAIN','T_FINAL_SHAM']]
 caps=[read(next(ROOT/f for f in r['files'] if f.endswith('/capture.json'))) for r in rr]
 if len(rr)!=2 or not eq(rr[0]['endpoint'],rr[1]['endpoint']) or caps[0]['trace']!=caps[1]['trace'] or caps[0]['commits']!=caps[1]['commits']:fail.append('plain/sham/'+task)
save(ROOT/'G0_TARGET_FINAL.json',dict(status='PASS' if not fail else 'BLOCKED_REFERENCE',requests=len(rows),warmups=len(sessions),failed=fail,width_observations=width_observations,width_failures_gate_only_their_configuration=True,unchanged_native_proof='G0/bridge/rebuilt/sham and original width native observations; exact native binary retained'))
assert not fail,fail
