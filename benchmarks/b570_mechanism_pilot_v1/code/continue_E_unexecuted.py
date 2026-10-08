"""Frozen E round-two continuation only; no scientific request replay."""
from pathlib import Path
import hashlib,uuid,traceback
import formal_runner as r
R=Path(__file__).parent

def main():
 f=r.read(R/'E_FREEZE.json');assert all(r.sha(R/n)==h for n,h in f['files'].items())
 m=r.read(R/'E_MANIFEST.json');dev={i['id']:i for i in r.read(R/'DEV_INPUTS.json')};new={i['id']:i for i in r.read(R/'E_INPUTS.json')}
 starts=[r.read(R/'E_INTERRUPTION.json')['unit_id']]
 ledger=[__import__('json').loads(l) for l in (R/'LEDGER.jsonl').read_text().splitlines()];sent={e['unit_id'] for e in ledger if e['event']=='REQUEST_START'}
 remaining=[g for g in m['formal_sessions'] if g['config']['round']==2]
 assert all(u['unit_id'] not in sent for g in remaining for u in g['units'])
 assert sum(e['event']=='REQUEST_START' and not e['warm'] for e in ledger)+sum(len(g['units']) for g in remaining)==312
 r.acquire();r.STAGE='E_CONTINUATION'
 try:
  for group in remaining:
   s=r.Session('E-2-'+group['config']['label']+'-'+uuid.uuid4().hex[:6],group['config'])
   try:
    s.request('E/FORMAL/WARM/'+s.name,dev['HumanEval/134'],True)
    for u in group['units']:
     s.request(u['unit_id'],new[u['task']])
     rows=[r.read(p) for p in (R/'raw').glob('*/RESULT.json')];formal=[dict(unit_id=v['unit_id'],task=v['task'],label=v['config']['label'],round=v['config']['round']) for v in rows if v['unit_id'].startswith('E/FORMAL/') and not v['warm']]
     r.save(R/'E_RUN_PROGRESS.json',dict(planned=120,complete=len(formal),rows=formal,no_candidate_changes=True,missing=starts))
   finally:s.close()
  r.save(R/'E_RUN_GATE.json',dict(status='PARTIAL_INFRASTRUCTURE_BUDGET_CLOSED',formal_complete=119,formal_planned=120,bridge_complete=8,missing=starts,all_unexecuted_fixed_units_executed=True,no_rerun=True))
 except BaseException:r.save(R/'E_CONTINUATION_FAILURE.json',dict(traceback=traceback.format_exc()));raise
 finally:r.release()
 print('E fixed continuation closed:119/120; interruption charged, no replay',flush=True)
if __name__=='__main__':main()
