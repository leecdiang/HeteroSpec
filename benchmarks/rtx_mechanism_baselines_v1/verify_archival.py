"""CPU-only cross-check of both freezes, actual task membership and native identity."""
import argparse
from pathlib import Path
from common import load,save,sha
from prepare_rtx import root
from plan import validate
def main(out):
    r=root();s=load(r/'RUN_SPEC.json');f1=load(r/'FREEZE.json');f2=load(r/'FREEZE_REPAIR1.json');assert sha(r/'FREEZE.json')==f2['previous_freeze_sha256'];p=load(r/'plan.json');validate(p);assert sha(r/'plan.json')==f2['plan_exact_sha256']
    for f,folder in [(f1,'SOURCE'),(f2,'SOURCE_REPAIR1')]:
        for n,h in f['files'].items():assert sha(r/folder/n)==h,'actual consumed source/host drift'
    plans={t['task_id']:t for t in p['tasks']}
    if (r/'P0_FREEZE.json').exists():
        f0=load(r/'P0_FREEZE.json');assert sha(r/'FREEZE_REPAIR1.json')==f0['B0_freeze_sha256'];assert sha(r/'P0_PLAN.json')==f0['plan_exact_sha256'];pp=load(r/'P0_PLAN.json');validate(pp);assert pp['parent_B0_plan_sha256']==p['plan_sha256'];plans.update({t['task_id']:t for t in pp['tasks']})
        for name,h in f0['source'].items():assert sha(r/'P0_SOURCE'/name)==h,'prospective P0 source snapshot'
    tasks=[];counts={};capabilities=[]
    for a in (r/'attempts').iterdir():
        start=load(a/'STARTED.json');t=start['task'];job=load(a/'JOB.json');assert start['native_sha256'] in [f1['native_sha256'],f2['native_sha256']];assert job['execution_id']==s['execution_id'] and job['layout']==t['layout'] and job['graph_mode']==t['graph_mode'];assert job['calls']==t['measured_calls'] and job['warmups']==t['warmups'];assert job['lifecycle']=='persistent_inputs' and job['method']=='H1'
        if t['task_id'] in plans:
            for k,v in plans[t['task_id']].items():assert t[k]==v,'actual frozen task changed'
        else:assert t['stage']=='capability' and t['task_id'].startswith('capability');capabilities.append(t)
        if t['stage'] in ['confirm','producer']:assert job['profile']==False,'profile cost contaminates clean'
        counts[t['stage']]=counts.get(t['stage'],0)+1;tasks.append(t['task_id'])
    assert len(tasks)==len(set(tasks)) and len(capabilities)<=12
    profile_attempts=sum(load(a/'JOB.json')['profile'] for a in (r/'attempts').iterdir());assert profile_attempts<=24
    save(out,dict(status='PASS',attempts=len(tasks),by_stage=counts,capability_hosts=len(capabilities),profile_attempts=profile_attempts,all_tasks_match_exact_plans=True,original_freeze_sha256=sha(r/'FREEZE.json'),tool_repair_freeze_sha256=sha(r/'FREEZE_REPAIR1.json'),P0_freeze_sha256=sha(r/'P0_FREEZE.json') if (r/'P0_FREEZE.json').exists() else None,source_host_snapshots_exact=True,clean_has_no_profile=True,GPU_calls=0))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();main(a.out)
