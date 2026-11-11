"""Deadline-governed14B attribution after successful Llama closure; local only."""
from pathlib import Path
import argparse,datetime,fcntl,hashlib,json,shutil,subprocess,sys,time

def read(p):return json.loads(p.read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def utc():return datetime.datetime.now(datetime.timezone.utc)
def before(t):return utc()<datetime.datetime.fromisoformat(t)

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--source-commit',required=True);a=p.parse_args();r=a.root.resolve()
    source=Path(__file__).resolve().parent;integration=source.parent;w=r/'d14-attribution-run-01';prior=r/'d14-run-01';audit=r/'d14-attribution-audit-01';audit.mkdir(exist_ok=False)
    start=time.monotonic();phase='WAIT_LLAMA';files={str(p):sha(p) for p in integration.rglob('*') if p.is_file() and '__pycache__' not in p.parts};files[str(integration.parent/'shared/experiment.py')]=sha(integration.parent/'shared/experiment.py')
    save(audit/'SOURCE_FREEZE.private.json',dict(files=files,source_commit=a.source_commit,external_publication='HOLD',deadline_utc='2026-11-09T00:00:00+00:00',stop_new_workers_utc='2026-11-08T21:00:00+00:00',four_arm_latest_start_utc='2026-11-08T18:30:00+00:00',two_arm_latest_start_utc='2026-11-08T19:30:00+00:00',fallback_criterion='time only, never observed performance sign',old_baselines_and_measurements_immutable=True))
    def execute(label,cmd):
        nonlocal phase
        phase=label
        for path,h in files.items():assert sha(Path(path))==h,'Attribution source changed'
        save(audit/(label+'-START.json'),dict(command=cmd,utc=utc().isoformat(),elapsed_s=time.monotonic()-start))
        with (audit/(label+'.stdout.log')).open('x') as o,(audit/(label+'.stderr.log')).open('x') as e:result=subprocess.run(cmd,stdout=o,stderr=e)
        save(audit/(label+'-EXIT.json'),dict(returncode=result.returncode,utc=utc().isoformat(),elapsed_s=time.monotonic()-start));return result.returncode
    try:
        f=r/'f-confirmation-audit-03/STATUS.json'
        while not f.exists():
            if not before('2026-11-08T17:00:00+00:00'):
                save(audit/'STATUS.json',dict(status='DEFERRED_DEADLINE',phase=phase,reason='Llama has not closed; reserve qualification and archive time',no_attribution_native_started=True));return
            time.sleep(5)
        assert read(f)['status']=='F_CONFIRMATION_COMPLETE_AND_ARCHIVED','Llama needs repair; no silent advancement'
        with (r/'STUDY_SCHEDULING.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            assert before('2026-11-08T17:00:00+00:00'),'Insufficient reliable qualification/formal/archive reserve'
            assert read(prior/'FORMAL_STAGE_STATUS-01.json')['status']=='COMPLETE'
            assert sha(prior/'qualification-03/NATIVE_CHECKS_COMPLETE.json')=='d40fff3eee672eafb9bc40f0a788b5be907b544a6140b539ea05863d5469e5af'
            index=read(r/'d14-public-export-02/TEXT_INDEX.json');changed=[]
            for row in index['files']:
                if not row['path'].startswith('support/'):
                    path=prior/row['path']
                    if not path.is_file() or sha(path)!=row['raw_sha256']:changed.append(row['path'])
            assert not changed,'Predecessor text commitment changed: '+str(changed)
            assert not w.exists(),'Fresh attribution root required'
            w.mkdir();shutil.copytree(prior/'inputs-01',w/'inputs-01');shutil.copytree(prior/'termination-fixture-01',w/'termination-fixture-01')
            shutil.copy2(prior/'MODEL_STRUCTURES.json',w/'MODEL_STRUCTURES.json')
            cfg=read(prior/'config-reference-frozen-01.json');cfg.update(work_root=str(w),freeze=None,freeze_sha256=None)
            save(w/'config-reference-frozen-01.json',cfg);save(w/'config.json',cfg)
            save(w/'PRIOR_ACCOUNTING.private.json',dict(independent_ledger=True,prior_ledger_sha256=sha(prior/'ledger.jsonl'),prior_reference_freeze_sha256=cfg['reference_freeze_sha256'],predecessor_text_index_sha256=sha(r/'d14-public-export-02/TEXT_INDEX.json'),predecessor_binary_index_sha256=sha(r/'d14-public-export-02/BINARY_CAPTURE_INDEX.json'),reused_old_measurement_times=False,request_ceiling=2560,row_ceiling=12000000))
            cmd=[sys.executable,'-B',str(integration/'qualify_attribution.py')]
            args=dict(work=w,baseline=r/'run-01',runtime=r/'d14-runtime-02',builds=r/'d14-deployment-build-02',repo=r/'repository-01',admission=r/'d14-admission-01',target=r/'d14-models-03/Qwen3-14B-Q8_0.gguf',draft=r/'models-final/Qwen3-0.6B-Q8_0.gguf',previous_qualification=prior/'qualification-02',f_completion=f,predecessor=prior)
            for k,v in args.items():cmd+=['--'+k.replace('_','-'),str(v)]
            cmd+=['--source-commit',a.source_commit]
            assert execute('qualification',cmd)==0,'Retained attribution qualification failure; no performance inference'
            phase='FORMAL_ADMISSION'
            if before('2026-11-08T18:30:00+00:00'):panel='attribution'
            elif before('2026-11-08T19:30:00+00:00'):panel='packed_pair'
            else:panel=None
            save(audit/'TIME_ONLY_PANEL_DECISION.json',dict(utc=utc().isoformat(),panel=panel,qualification_sha256=sha(w/'qualification-03/NATIVE_CHECKS_COMPLETE.json'),performance_values_consulted=False,prior_times_not_pooled=True))
            if panel:
                cmd=[sys.executable,'-B',str(source/'prepare_panel.py'),'--root',str(r),'--work',str(w),'--integration',str(integration),'--panel',panel,'--source-commit',a.source_commit]
                assert execute('prepare-panel',cmd)==0,'Prospective attribution plan failed'
                cmd=[sys.executable,'-B',str(source/'run_panel.py')]
                for k,v in dict(work=w,baseline=r/'run-01',runtime=r/'d14-runtime-02',builds=r/'d14-deployment-build-02',repo=r/'repository-01',predecessor=prior).items():cmd+=['--'+k,str(v)]
                cmd+=['--source-commit',a.source_commit];code=execute('formal',cmd)
                slots=read(w/'panel-01/ALL_SLOT_STATUS.json') if (w/'panel-01/ALL_SLOT_STATUS.json').exists() else None
                complete=code==0 and slots and slots['complete_workers']==slots['expected_workers'] and (w/'panel-01/RESULTS.json').exists()
                save(w/'FORMAL_STAGE_STATUS-01.json',dict(status='COMPLETE' if complete else 'QUALIFIED_WITH_RETAINED_FORMAL_FAILURE',panel=panel,returncode=code,actual_slot_status=slots,no_selected_native_retry=True))
                assert complete,'Retain every failed/unstarted slot; no successful-subset inference'
            else:save(w/'FORMAL_STAGE_STATUS-01.json',dict(status='QUALIFIED_FORMAL_NOT_RUN',reason='No reliable formal time remains; preserve qualification and old results'))
        phase='ARCHIVE'
        cmd=[sys.executable,'-B',str(source/'archive.py'),'--root',str(r),'--work',str(w),'--audit',str(audit)]
        assert execute('archive',cmd)==0,'Archive/readback needs repair; never replay numerical slots'
        save(audit/'STATUS.json',dict(status='COMPLETE_AND_ARCHIVED',panel=panel,formal_performance='COMPLETE' if panel else 'NOT_RUN',elapsed_s=time.monotonic()-start,external_publication='NOT_RUN',M2='NOT_RUN',Q4_GPU='NOT_RUN'))
    except BaseException as e:
        if not (audit/'STATUS.json').exists():save(audit/'STATUS.json',dict(status='FAILED_RETAINED',phase=phase,error=str(e),elapsed_s=time.monotonic()-start,no_selected_native_retry=True))
        raise
if __name__=='__main__':main()
