"""A gate derived from a separate raw reconstruction, never controller PASS text."""
import argparse
from common import BASE,DESIGN,load,write_new,sha,need
p=argparse.ArgumentParser();p.add_argument('--audit',required=True);p.add_argument('--round',type=int,required=True);a=p.parse_args()
report=load(BASE/a.audit);f=DESIGN/'results/CONFIRMATION_FREEZE.json';fsha=sha(f)
rows=[r for r in report['cases'] if r.get('round')==a.round]
need(len(rows)==19 and all(r['status']=='PASS' and r['receipt']['freeze_sha256']==fsha for r in rows),'round not completely qualified; no later round may start')
need(report['manifest_valid'] and report['process_ledger_valid'] and not report['problems'],'raw engineering audit failed')
write_new(DESIGN/'results'/('ROUND_'+str(a.round)+'_GATE.json'),dict(qualified_round=a.round,freeze_sha256=fsha,raw_audit_path=a.audit,raw_audit_sha256=sha(BASE/a.audit)))
