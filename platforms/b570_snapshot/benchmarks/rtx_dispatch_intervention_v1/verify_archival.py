"""Offline frozen-identity, order, admission and retained-source verification."""
import argparse,hashlib,os
from pathlib import Path
from common import load,save,sha
from prepare_rtx import root

def main(out):
    r=root();spec=load(r/'RUN_SPEC.json');files=[]
    for n,folder in [('FREEZE.json','SOURCE'),('FREEZE_REPAIR1.json','SOURCE_REPAIR1')]:
        f=load(r/n)
        for name,h in f['files'].items():assert sha(r/folder/name)==h;files.append(folder+'/'+name)
    f=load(r/'FREEZE_REPAIR1.json');assert f['parent_freeze_sha256']==sha(r/'FREEZE.json')
    for key,file in [('plan_exact_sha256','plan.json'),('spec_sha256','RUN_SPEC.json'),('runtime_manifest_sha256','RUNTIME_MANIFEST.json'),('input_index_sha256','INPUTS.json'),('policy_sha256','EXECUTION_POLICY.json'),('build_dependencies_sha256','BUILD_DEPENDENCIES.json')]:assert sha(r/file)==f[key]
    assert load(r/'FREEZE.json')['native_sha256']==f['native_sha256']
    p=load(r/'plan.json');ad=load(r/'ADMISSION.json');assert ad['qualification_sha256']==sha(r/'QUALIFICATION.json') and ad['capability_sha256']==sha(r/'CAPABILITY.json') and ad['reference_sha256']==sha(r/'REFERENCES.json') and ad['schedule_sha256']==sha(r/'plan.json')
    expected={t['task_id']:t for t in p['timed_jobs']};by_session={};starts=[]
    for a in (r/'attempts').iterdir():
        x=load(a/'STARTED.json');t=x['task'];starts.append(x)
        if t['stage']=='timed':
            old=expected[t['task_id']]
            for k in old:assert old[k]==t[k],'timed task changed'
            by_session.setdefault(t['session'],[]).append(x)
    for session,rows in by_session.items():
        rows.sort(key=lambda x:x['epoch']);observed=[x['task']['task_id'] for x in rows];planned=[]
        for t in p['timed_jobs']:
            if t['session']!=session:continue
            c=next(c for c in p['cells'] if c['id']==t['cell']);arm=c['arms'][0]['name'] if t['arm']==c['arms'][1]['name'] else t['arm'];key=c['id']+'/'+arm
            if ad['arms'][key]['eligible']:planned.append(t['task_id'])
        assert observed==planned[:len(observed)],'actual schedule is not admitted original order'
    for c in p['cells']:
        for q in range(c['q']):
            one=load(r/'serial'/c['id']/'INDEX.json')[q]
            for row in one['inputs']:assert sha(r/'serial'/c['id']/str(q)/row['name'])==row['sha256']
    save(out,dict(status='PASS',frozen_files=len(files),actual_order_matches_original_eligible_slots=True,all_frozen_identities=True,native_unchanged_after_pregraph_tool_repair=True,profile_attempts=sum(bool(x['task'].get('profile')) for x in starts),original_UUID=spec['execution_id'],GPU_calls=0))
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);z=a.parse_args();main(z.out)
