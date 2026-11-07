"""Fixed repaired synthetic endpoint probes; earlier non-triggering attempt retained."""
from prepare import ROOT,STUDY,save
from engine import execute,now
import verify
def main():
    out=ROOT/'work/endpoint-probes-qualified';out.mkdir(exist_ok=False)
    prior=STUDY/'ENDPOINT_QUALIFICATION.json';(ROOT/'work/endpoint-probe-attempt1-receipt.json').write_bytes(prior.read_bytes())
    probes=[('SYNTHETIC_EOG','Reply with only OK.','EOS'),('SYNTHETIC_CAP','Write a detailed 2000-word story about a lighthouse keeper discovering a lost island. Begin the story immediately and include descriptions and dialogue.','limit')]
    save(STUDY/'FINAL_ENDPOINT_PROBE_PLAN.json',{'fixed_before_execution_utc':now(),'probes':[{'task_id':t,'input':text,'required_endpoint':term} for t,text,term in probes],'engineering_only':True,'prior_attempt_retained':'work/endpoint-probes','revision_reason':'Integer enumeration prompt yielded a short program and EOG after 80 IDs; not counted as cap coverage.'})
    report={'started_utc':now(),'status':'STARTED','runs':[],'formal':False}
    for task,text,term in probes:
        tape=None
        for c in ['REFERENCE_UB1','RTX_BATCHED_K2','H2_P_R','R_ONLY']:
            r=execute(task,1,c,out/'runs',text=text,tape_path=tape);report['runs'].append(r);save(out/'records.json',report)
            if r['status']!='VALID':raise RuntimeError(r.get('error'))
            if c=='H2_P_R':tape=out/'runs'/r['run_id']/'tape.jsonl'
            if r['termination']!=term:report.update(status='PROBE_NOT_TRIGGERED',ended_utc=now());save(out/'records.json',report);raise RuntimeError('fixed endpoint not reached')
            verify.check_run(out/'runs'/r['run_id'],tape if c=='R_ONLY' else None)
    report.update(status='PASS',ended_utc=now());save(out/'records.json',report);save(STUDY/'ENDPOINT_QUALIFICATION.json',{'status':'PASS','executions':8,'results':[{'run_id':r['run_id'],'length':len(r['generated_ids']),'termination':r['termination']} for r in report['runs']],'prior_non_triggering_attempt_executions':5,'prior_retained':True})
    print('Real four-condition EOG/cap qualification PASS')
if __name__=='__main__':main()
