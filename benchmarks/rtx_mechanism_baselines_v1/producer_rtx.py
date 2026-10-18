"""Optional P0 OFF cohort, separately frozen; no change to B0 dual receipts."""
import argparse,copy,json,os,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root,LAYOUTS
from plan import digest,validate
import runner as core
def make_producer_plan(original):
    p=copy.deepcopy(original);p['tasks']=[t for t in p['tasks'] if t['optional']]
    for t in p['tasks']:t['task_id']='p0off-'+t['task_id'];t['graph_mode']='OFF'
    p['modes']=['OFF'];p['graph_plan']='producer-off-only';p['counts']={};p['unresolved']=[];p['scope']='P0 separately admitted OFF transaction;core B0 dual plan and identities unchanged'
    p['parent_B0_plan_sha256']=original['plan_sha256']
    for t in p['tasks']:
        entry=p['counts'].setdefault(t['stage'],dict(hosts=0,calls=0));entry['hosts']+=1;entry['calls']+=t['warmups']+t['measured_calls']
    p.pop('plan_sha256');p['plan_sha256']=digest(p);validate(p);return p
def freeze():
    r=root();s,f=core.verify_freeze();p=make_producer_plan(load(r/'plan.json'))
    assert not core.git('status','--porcelain','--untracked-files=no','--',str(V)),'commit P0 entry first'
    save(r/'P0_PLAN.json',p)
    files=['producer_rtx.py','audit_rtx.py','plan.py','analyze.py']
    snapshot=r/'P0_SOURCE';snapshot.mkdir()
    import shutil
    for name in files:shutil.copyfile(V/name,snapshot/name)
    save(r/'P0_FREEZE.json',dict(commit=core.git('rev-parse','HEAD'),utc=core.utc(),source={n:sha(V/n) for n in files},B0_freeze_sha256=sha(r/'FREEZE_REPAIR1.json'),plan_exact_sha256=sha(r/'P0_PLAN.json'),plan_sha256=p['plan_sha256'],input_index_sha256=f['input_index_sha256'],native_sha256=f['native_sha256'],runtime_manifest_sha256=f['runtime_manifest_sha256'],mode='OFF',reason='Actual q4 ON signatures would require additional profiled hosts beyond24 including preserved tool failure;uniform OFF chosen prospectively, not from P0 outputs or speed',budget=dict(hosts=176,graph_calls=5968,serial_reference_hosts=16,qualification_hosts=32,timing_hosts=128,profile_hosts=0,extra_capability_hosts=0,global_total_seconds=s['global_seconds'],closure_reserve_seconds=s['delivery_reserve_seconds']),pipeline='one native QPC interval:copy/transpose complete preexisting permuted Q->Q upload/sync->graph compute/sync->complete ordinary readback;resident KV/mask;preallocated destination;Q production UNKNOWN'))
    print('P0 FROZEN',sha(r/'P0_FREEZE.json'))
def cases():
    rows=core.contexts();r=root()
    if (r/'P0_REFERENCES.json').exists():
        for cid,ref in load(r/'P0_REFERENCES.json').items():
            for l in LAYOUTS:rows[cid]['references'][l]=dict(path=ref['path'],sha256=ref['sha256'])
    return rows
def stage(name):
    r=root();s,f=core.verify_freeze();p=load(r/'P0_PLAN.json');validate(p);f0=load(r/'P0_FREEZE.json');assert sha(r/'P0_PLAN.json')==f0['plan_exact_sha256']
    for n,h in f0['source'].items():assert sha(V/n)==h,'P0 source drift'
    assert not (r/'WORKER.lock').exists(),'single GPU worker';assert not (r/(name+'_STARTED.json')).exists(),'no retry'
    if name!='p0reference':assert (r/'p0reference_ENDED.json').exists()
    save(r/'WORKER.lock',dict(stage=name,pid=os.getpid(),utc=core.utc()));save(r/(name+'_STARTED.json'),dict(pid=os.getpid(),utc=core.utc(),epoch=time.time(),P0_F0_sha256=sha(r/'P0_FREEZE.json')));k,handles=core.lock_runtime(s);done=[];started=time.monotonic();rows=cases();session=name+'-'+str(os.getpid())+'-'+core.utc();status='COMPLETE'
    try:
        if name=='p0reference':
            core.telemetry(s,name+'/pre');parts={};refs={cid:ref for cid,ref in load(r/'REFERENCES.json').items() if cid.startswith('q2-k256')}
            for t in [t for t in p['tasks'] if t['stage']=='reference']:
                base=core.case_for(t,rows);one=copy.deepcopy(base);sub=base['serial_roots'][t['query_index']];one.update(id=base['id']+'/serial'+str(t['query_index']),q=1,root=sub,metadata=load(Path(sub)/'snapshot.json'));one['inputs']=[dict(name=x.name,bytes=x.stat().st_size,sha256=sha(x)) for x in sorted(Path(sub).iterdir()) if x.is_file()]
                result,a=core.execute(t,one,'H1',session);assert result['numerical_qualified'];done.append(t['task_id']);data=core.occurrence(a/'native',load(a/'native/RECORD.json')['calls'][0]);parts.setdefault((base['case_id'],t['query_index']),[]).append(data)
            for cid in sorted({key[0] for key in parts}):
                c=rows[cid];pieces=[parts[cid,j] for j in range(c['q'])];assert all(len(x)==2 and x[0]==x[1] for x in pieces);dest=Path(c['root'])/'ordinary_reference.bin'
                with dest.open('xb') as file:file.write(b''.join(x[0] for x in pieces))
                refs[cid]=dict(path=str(dest),sha256=sha(dest),bytes=dest.stat().st_size,independent_hosts=8)
            save(r/'P0_REFERENCES.json',refs)
        elif name=='p0qualification':
            core.telemetry(s,name+'/pre');eligible={}
            for t in [t for t in p['tasks'] if t['stage']=='producer_qualification']:
                c=core.case_for(t,rows);source=rows[f"q{c['q']}-k256-v{c['realization']}"];expected=sha(Path(source['root'])/'Q.bin');result,a=core.execute(t,c,'H1',session);assert sha(Path(source['root'])/'Q.bin')==expected
                done.append(t['task_id']);key=t['case_id']+'|'+t['arm'];eligible.setdefault(key,[]).append(result['numerical_qualified']);assert result['numerical_qualified'],'P0 exact numerical qualification failed';print(name,len(done),t['task_id'],flush=True)
            save(r/'P0_QUALIFICATION.json',eligible)
        else:
            eligible=load(r/'P0_QUALIFICATION.json');blocks=range(0,4) if name.endswith('0') else range(4,8);save(r/(name+'_SESSION.json'),dict(session_id=session,blocks=list(blocks),utc=core.utc()))
            for b in blocks:
                pre=core.quiet(s,name+'/'+str(b))
                if not pre:status='QUIET_WINDOW_UNAVAILABLE';break
                ids=[]
                for t in [t for t in p['tasks'] if t['stage']=='producer' and t['block']==b]:
                    assert eligible[t['case_id']+'|'+t['arm']]==[True,True]
                    c=core.case_for(t,rows);source=rows[f"q{c['q']}-k256-v{c['realization']}"];before=sha(Path(source['root'])/'Q.bin');result,a=core.execute(t,c,'H1',session);assert sha(Path(source['root'])/'Q.bin')==before;done.append(t['task_id']);ids.append(t['task_id']);assert result['numerical_qualified'];print(name,b,len(done),t['task_id'],flush=True)
                post=core.telemetry(s,name+'/'+str(b)+'/post');save(r/f'{name}_BLOCK_{b}.json',dict(pre=pre,post=post,environment_qualified=post['quiet'],tasks=ids,session_id=session))
        save(r/(name+'_ENDED.json'),dict(status=status,hosts=len(done),tasks=done,seconds=time.monotonic()-started,utc=core.utc()))
    except BaseException as exc:
        save(r/(name+'_FAILED.json'),dict(reason=repr(exc),completed=done,seconds=time.monotonic()-started,utc=core.utc()));raise
    finally:
        for h in handles:k.CloseHandle(h)
        (r/'WORKER.lock').rename(r/(name+'_WORKER_CLOSED.json'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['freeze','p0reference','p0qualification','p0confirm0','p0confirm1']);a=ap.parse_args();freeze() if a.action=='freeze' else stage(a.action)
