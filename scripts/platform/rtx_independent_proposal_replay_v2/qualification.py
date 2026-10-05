"""All new reference qualifications and exposed real endpoint probes."""
import json,subprocess,sys
from pathlib import Path
from prepare import ROOT,STUDY,save
from engine import execute,now,digest
TASKS=[f'HumanEval/{i}' for i in [3,10,19,20,28,32,44,47,48,50,54,57,62,64,68,70,89,90,101,104,105,106,107,111,119,123,126,128,129,162]]
def main():
    phase=ROOT/'work/reference-qualification';phase.mkdir(exist_ok=False)
    report={'started_utc':now(),'status':'STARTED','runs':[],'comparisons':[],'planned_executions':180}
    for task in TASKS:
        for rep in [1,2,3]:
            pair=[]
            for condition in ['REFERENCE_UB1','R_REFERENCE_UB1']:
                r=execute(task,rep,condition,phase/'runs');report['runs'].append(r);pair.append(r);save(phase/'records.json',report)
                save(ROOT/'work/progress.json',{'stage':'reference_qualification','count':len(report['runs']),'total':180,'latest_status':r['status'],'utc':now()})
                if r['status']!='VALID':report['status']='HARNESS_NOT_QUALIFIED';save(STUDY/'HARNESS_QUALIFICATION.json',report);raise RuntimeError(r.get('error'))
            a,b=[r['generated_ids'] for r in pair];first=next((i for i in range(max(len(a),len(b))) if (a[i] if i<len(a) else None)!=(b[i] if i<len(b) else None)),None)
            report['comparisons'].append({'task_id':task,'repetition':rep,'exact':a==b,'first_divergence':None if first is None else {'index':first,'CLI_id':a[first] if first<len(a) else None,'R_id':b[first] if first<len(b) else None}})
            save(phase/'records.json',report)
    matches=sum(r['exact'] for r in report['comparisons']);report.update(status='PASS' if matches==90 else 'HARNESS_NOT_QUALIFIED',complete_pairs=90,exact_pairs=matches,ended_utc=now())
    save(phase/'records.json',report);save(STUDY/'HARNESS_QUALIFICATION.json',{k:v for k,v in report.items() if k!='runs'})
    if matches!=90:return
    probes={'started_utc':now(),'formal':False,'runs':[],'status':'STARTED'};phase=ROOT/'work/endpoint-probes'
    for task,text,endpoint in [('SYNTHETIC_EOG','Reply with only OK.','EOS'),('SYNTHETIC_CAP','Write the Python integers from 1 to 1000, one integer per line. Continue until all 1000 integers have been written.','limit')]:
        tape=None
        for c in ['REFERENCE_UB1','RTX_BATCHED_K2','H2_P_R','R_ONLY']:
            r=execute(task,1,c,phase/'runs',text=text,tape_path=tape);probes['runs'].append(r);save(phase/'records.json',probes)
            if r['status']!='VALID':raise RuntimeError(r.get('error'))
            if c=='H2_P_R':tape=phase/'runs'/r['run_id']/'tape.jsonl'
            if r['termination']!=endpoint:probes['status']='PROBE_NOT_TRIGGERED';save(STUDY/'ENDPOINT_QUALIFICATION.json',probes);return
    probes.update(status='PASS',ended_utc=now());save(phase/'records.json',probes);save(STUDY/'ENDPOINT_QUALIFICATION.json',{k:v for k,v in probes.items() if k!='runs'}|{'executions':8,'results':[{'run_id':r['run_id'],'length':len(r['generated_ids']),'termination':r['termination']} for r in probes['runs']]})
    save(ROOT/'work/progress.json',{'stage':'engineering_reference_and_endpoints_complete','status':'PASS','reference_pairs':90,'endpoint_runs':8,'utc':now()})
if __name__=='__main__':main()
