"""Optional new-seed holdout: never opens bytes/outputs before prediction freeze."""
import argparse,copy,os,struct,time
from pathlib import Path
from common import V,load,save,sha
from prepare_rtx import root,materialize,LAYOUTS
from collect import verify_freeze,guard,helper,env,Child,telemetry,quiet,lock_runtime,execute,occurrence,utc,git

def prepare():
    r=root();assert (r/'PREDICTION_FREEZE.json').exists();rule=load(r/'PREDICTION_FREEZE.json');assert rule['predictions_before_holdout'] and not (r/'HOLDOUT_INPUTS.json').exists()
    plan=load(r/'plan.json');cases=materialize(plan,True);s=load(r/'RUN_SPEC.json');words=0
    for cid,c in cases.items():
        folder=r/'CPU'/cid;folder.mkdir(parents=True)
        for l in LAYOUTS:
            job=folder/(l+'_JOB.json');save(job,dict(spec=str(r/'RUN_SPEC.json'),context=c,layout=l));w=Child(helper());w.run([str(V/'build/address_cpu.exe'),str(job),str(folder/(l+'.json'))],folder/(l+'_host'),120,env(s),s['host_RAM_bytes']);words+=load(folder/(l+'.json'))['whole_Q_mask_output_words']
    save(r/'HOLDOUT_FREEZE.json',dict(commit=git('rev-parse','HEAD'),source_sha256=sha(V/'holdout_rtx.py'),prediction_sha256=sha(r/'PREDICTION_FREEZE.json'),input_index_sha256=sha(r/'HOLDOUT_INPUTS.json'),core_freeze_sha256=sha(r/'FREEZE.json'),CPU_actual_graphs=len(cases)*3,full_Q_mask_output_words=words,utc=utc()))

def stage(name):
    r=root();s,f=verify_freeze();optional=load(r/'HOLDOUT_FREEZE.json');assert optional['source_sha256']==sha(V/'holdout_rtx.py') and optional['input_index_sha256']==sha(r/'HOLDOUT_INPUTS.json') and optional['prediction_sha256']==sha(r/'PREDICTION_FREEZE.json');assert load(r/'METHOD_DECISION.json')['selected_method']=='H1';assert not (r/'WORKER.lock').exists();save(r/'WORKER.lock',dict(pid=os.getpid(),stage=name));save(r/(name+'_STARTED.json'),dict(pid=os.getpid(),utc=utc(),epoch=time.time()));plan=load(r/'plan.json');cases=load(r/'HOLDOUT_INPUTS.json');k,handles=lock_runtime(s);begin=time.monotonic();rows=[]
    try:
        if name=='holdout_reference':
            telemetry(s,name+'/pre');refs={}
            for cid,c in cases.items():
                parts=[]
                for j,sub in enumerate(c['serial_roots']):
                    one=copy.deepcopy(c);one.update(id=cid+f'/serial{j}',q=1,root=sub,metadata=load(Path(sub)/'snapshot.json'));one['inputs']=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(Path(sub).iterdir()) if p.is_file()];values=[]
                    for t in [t for t in plan['tasks'] if t['stage']=='reference' and t['case_id']==cid and t['query_index']==j]:
                        result,a=execute(t,one,'H1',name+'-'+str(os.getpid()));assert result['numerical_qualified'];values.append(occurrence(a/'native',load(a/'native/RECORD.json')['calls'][0]));rows.append(t['task_id'])
                    assert len(values)==2 and values[0]==values[1];parts.append(values[0])
                p=Path(c['root'])/'ordinary_reference.bin'
                with p.open('xb') as file:file.write(b''.join(parts))
                refs[cid]=dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size,independent_reference_hosts=6);print(name,cid,len(rows),flush=True)
            save(r/'HOLDOUT_REFERENCES.json',refs)
        else:
            for cid,row in load(r/'HOLDOUT_REFERENCES.json').items():
                for l in LAYOUTS:cases[cid]['references'][l]=dict(path=row['path'],sha256=row['sha256'])
            if name=='holdout_qualification':
                telemetry(s,name+'/pre');eligible={}
                for t in [t for t in plan['tasks'] if t['stage']=='qualification' and t['optional']]:
                    key='|'.join([t['case_id'],t['layout'],'H1'])
                    if eligible.get(key) is False:continue
                    result,a=execute(t,cases[t['case_id']],'H1',name+'-'+str(os.getpid()));rows.append(t['task_id']);eligible[key]=result['numerical_qualified'];print(name,t['task_id'],len(rows),flush=True)
                save(r/'HOLDOUT_QUALIFICATION.json',eligible)
            else:
                eligible=load(r/'HOLDOUT_QUALIFICATION.json');assert all(eligible.values());blocks=list(range(4)) if name=='holdout0' else list(range(4,8));session=name+'-'+str(os.getpid())+'-'+utc();save(r/(name+'_SESSION.json'),dict(session_id=session,pid=os.getpid(),utc_start=utc(),blocks=blocks))
                for b in blocks:
                    pre=quiet(s,name+'/'+str(b))
                    if not pre:raise RuntimeError('quiet window unavailable;no tasks retried')
                    blockrows=[]
                    for t in [t for t in plan['tasks'] if t['stage']=='holdout' and t['block']==b]:
                        if not eligible.get('|'.join([t['case_id'],t['layout'],'H1']),False):continue
                        result,a=execute(t,cases[t['case_id']],'H1',session);rows.append(t['task_id']);blockrows.append(t['task_id']);print(name,b,t['task_id'],len(rows),flush=True)
                        if not result['numerical_qualified']:eligible['|'.join([t['case_id'],t['layout'],'H1'])]=False
                    post=telemetry(s,name+'/'+str(b)+'/post');save(r/f'{name}_BLOCK_{b}.json',dict(pre=pre,post=post,environment_qualified=post['quiet'],tasks=blockrows,session_id=session))
        save(r/(name+'_ENDED.json'),dict(status='COMPLETE',hosts=len(rows),tasks=rows,seconds=time.monotonic()-begin,utc=utc()))
    except BaseException as e:
        save(r/(name+'_FAILED.json'),dict(reason=repr(e),completed_tasks=rows,seconds=time.monotonic()-begin,utc=utc()));raise
    finally:
        for h in handles:k.CloseHandle(h)
        (r/'WORKER.lock').rename(r/(name+'_WORKER_CLOSED.json'))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','holdout_reference','holdout_qualification','holdout0','holdout1']);a=ap.parse_args();prepare() if a.action=='prepare' else stage(a.action)
