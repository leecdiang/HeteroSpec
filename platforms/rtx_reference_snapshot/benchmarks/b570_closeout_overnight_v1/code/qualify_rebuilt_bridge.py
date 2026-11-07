"""Fresh final-build R/T/N1 exposed controls after timer-only rebuild."""
from pathlib import Path
from campaign import read,save,stage,R,T,N1,eq
ROOT=Path(__file__).parent
old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
tasks=['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/58']
inputs=[dict(id=t,prompt_ids=read(old[t]['ids'])) for t in tasks]
rows=stage('G0_REBUILT',[dict(config=dict(c,cap=128,capture=True,repetition=rep+1),inputs=inputs) for rep in range(2) for c in [R,T,N1]])
expected=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/evaluation/HISTORICAL_EXPECTED.json'))
bad=[]
for r in rows:
 ref=expected[r['task']+'/R/1'];ref=dict(ref,reason='EOG' if ref['endpoint']=='EOG' else 'CAP')
 if not eq(r['endpoint'],ref):bad.append(r['unit_id'])
save(ROOT/'G0_REBUILT.json',dict(status='PASS' if not bad else 'BLOCKED_REFERENCE',requests=len(rows),warmups=6,failed=bad,numerical_change='NONE: exact source assertions restrict changes to timer location and file close'))
assert not bad,bad
