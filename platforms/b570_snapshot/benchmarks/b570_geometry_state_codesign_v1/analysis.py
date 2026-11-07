"""Complete finite-panel comparisons on normalized records, never native inference.
A source-bound host normalizer/raw auditor remains mandatory. Synthetic tests are labelled.
"""
from __future__ import annotations
import argparse
import math
from pathlib import Path
from protocol import require, read_json, write_new, validate_plan, length_bin
from contracts import validate_record

PAIRS = [('R','C_R_QB'),('C_R_PQ','C_R_QB'),('C_B_PQ','C_B_QB'),
         ('C_B_QB','C_R_QB'),('M_R_QB','C_R_QB'),('M_B_QB','C_B_QB'),
         ('C_R_MQ','C_R_QB'),('C_B_MQ','C_B_QB'),('R','M_R_QB'),('R','M_B_QB')]


def time_gate(sessions: list[dict]) -> bool:
    require(len({x['session'] for x in sessions})==len(sessions), 'duplicate session')
    if len(sessions)!=4:return False
    s=sorted(sessions,key=lambda x:x['session'])
    if [x['session'] for x in s] != [0,1,2,3]:return False
    if not all(type(x[k]) in (int,float) and math.isfinite(x[k]) for x in s for k in ('start','end')):return False
    if not all(x['end']>=x['start'] for x in s):return False
    return (s[1]['start']-s[0]['end']>=3600 and s[2]['start']-s[0]['start']>=86400
            and s[2]['start']>=s[1]['end'] and s[3]['start']-s[2]['end']>=3600)


def compare(values: dict, references: dict, tasks: list[str], left: str, right: str, complete: bool) -> dict:
    logs=[]; rows=[]; failures=[]; total_l=0.;total_r=0.
    for session in range(4):
        ll=[]
        for task in tasks:
            l=values.get((session,task,left));r=values.get((session,task,right))
            if not l or not r or task not in references:
                failures.append({'session':session,'task':task,'reason':'MISSING_OR_UNSTABLE_REFERENCE'});continue
            if l['endpoint']!=references[task] or r['endpoint']!=references[task]:
                failures.append({'session':session,'task':task,'reason':'TREATMENT_ENDPOINT_COUNTEREXAMPLE'});continue
            value=math.log(l['wall_ms']/r['wall_ms']);ll.append(value);total_l+=l['wall_ms'];total_r+=r['wall_ms']
            rows.append({'session':session,'task':task,'left_over_right':math.exp(value),
                         'left_ms':l['wall_ms'],'right_ms':r['wall_ms']})
        logs.append({'session':session,'qualified_tasks':len(ll),
                     'log_left_over_right':sum(ll)/len(ll) if len(ll)==len(tasks) else None})
    qualified=complete and not failures and len(rows)==len(tasks)*4
    return {'left':left,'right':right,'qualified':qualified,'failures':failures,
            'per_session':logs,'task_ratios':rows,
            'geomean_ratio': math.exp(sum(r['log_left_over_right'] for r in logs)/4) if qualified else None,
            'ratio_of_total_request_cost':total_l/total_r if qualified else None,
            'right_latency_reduction':1-total_r/total_l if qualified else None,
            'regression_coordinates':sum(r['left_over_right']<1 for r in rows),
            'CI':None,'scope':'fixed-panel descriptive estimate; no request-level bootstrap; failed rows never used in aggregate'}


def analyze(plan: dict, records: list[dict], sessions: list[dict], runtime_hash: str,
            root: Path | None=None, *, allow_synthetic: bool=False) -> dict:
    validate_plan(plan);require(plan['phase']=='confirm','confirmation only')
    expected={s['slot']:s for s in plan['slots']};seen={};values={};failures=[];invalid=[];groups={}
    for rec in records:
        sid=rec['slot'];require(sid in expected and sid not in seen,'unknown/duplicate slot');seen[sid]=rec
        s=expected[sid]
        if rec['status']!='COMPLETED':failures.append(sid);continue
        try:
            require(allow_synthetic or rec.get('evidence_origin')=='NATIVE','synthetic records cannot become native evidence')
            checked=validate_record(s,rec,runtime_hash,root)
        except (ValueError,KeyError,TypeError,OSError) as error:
            invalid.append({'slot':sid,'error':str(error)});continue
        groups.setdefault(s['process_group'],[]).append((s,rec,checked))
        if not s['warmup']:values[(s['session'],s['task'],s['arm'])]=checked
    # Logical process identity is not established by PID alone; PID may be reused.
    pid_links=[];repeat_drift=[]
    for group,rs in groups.items():
        if len(rs)!=2:continue
        a,b=sorted(rs,key=lambda r:not r[0]['warmup'])
        if a[1]['pid']!=b[1]['pid'] or a[1]['lifecycle_id']!=b[1]['lifecycle_id']:
            pid_links.append(group)
        if a[2]['endpoint']!=b[2]['endpoint']:repeat_drift.append({'process_group':group,'arm':a[0]['arm']})
    missing=sorted(set(expected)-set(seen));gated=time_gate(sessions)
    common_complete=gated and not missing and not failures and not invalid and not pid_links
    references={};reference_changes=[];tasks=[c['id'] for c in plan['panel']]
    for task in tasks:
        endpoints=[values[(s,task,'R')]['endpoint'] for s in range(4) if (s,task,'R') in values]
        if len(endpoints)!=4 or any(e!=endpoints[0] for e in endpoints):reference_changes.append(task)
        else:references[task]=endpoints[0]
    if any(r['arm']=='R' for r in repeat_drift):common_complete=False
    arm_results={}
    for r in plan['recipes']:
        arm=r['name']; stable=not any(v['arm']==arm for v in repeat_drift)
        answer=compare(values,references,tasks,'R',arm,common_complete and stable and not reference_changes)
        answer['strata']={}
        for domain in ('code','math'):
            for b in range(3):
                sub=[c['id'] for c in plan['panel'] if c['domain']==domain and length_bin(len(c['prompt_ids']))==b]
                answer['strata'][f'{domain}/bin{b}']=compare(values,references,sub,'R',arm,answer['qualified'])
        arm_results[arm]=answer
    comparisons={}
    for left,right in PAIRS:
        comparisons[left+'/'+right]=compare(values,references,tasks,left,right,
                arm_results[left]['qualified'] and arm_results[right]['qualified'])
    return {'study':plan['study'],'status':'COMPLETE' if common_complete and not reference_changes else 'INCOMPLETE_OR_BLOCKED',
            'evidence_origin':'SYNTHETIC_TEST_ONLY' if allow_synthetic else 'NORMALIZED_NATIVE_PENDING_INDEPENDENT_RAW_AUDIT',
            'time_gate':gated,'missing_slots':missing,'failed_slots':failures,'invalid_records':invalid,
            'process_link_errors':pid_links,'within_process_output_drift':repeat_drift,
            'reference_changes':reference_changes,'arms':arm_results,'comparisons':comparisons,
            'raw_hash_check_performed':root is not None,
            'actual_hardware_numerical_contract_verified':False,
            'limitation':'Normalized fields and hashes do not prove independent raw semantic reconstruction. No GPU experiment is performed by this script.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('plan','records','sessions','out'):p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--runtime-hash',required=True);p.add_argument('--raw-root',type=Path)
    a=p.parse_args();write_new(a.out,analyze(read_json(a.plan),read_json(a.records),read_json(a.sessions),a.runtime_hash,a.raw_root))
if __name__=='__main__':main()
