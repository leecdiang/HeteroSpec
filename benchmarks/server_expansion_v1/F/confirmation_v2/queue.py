"""After primary archive/readback, admit and run the prospective Llama panel."""
from pathlib import Path
import argparse, datetime, fcntl, hashlib, json, subprocess, sys, time

def read(path):return json.loads(path.read_text()) if path.exists() else None
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('root','audit','exporter'):parser.add_argument('--'+key,type=Path,required=True)
    parser.add_argument('--source-commit',required=True)
    a=parser.parse_args();r=a.root.resolve();audit=a.audit.resolve();audit.mkdir(exist_ok=False)
    source=Path(__file__).resolve().parent;started=time.monotonic();phase='WAIT_PRIMARY_ARCHIVE'
    files={str(p):sha(p) for p in source.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    save(audit/'SOURCE_FREEZE.private.json',dict(source_commit=a.source_commit,files=files,exporter_sha256=sha(a.exporter),
        policy='Complete primary D14 timing and primary full archive/readback first; same device/mutex; exact prospective cohort before its R/candidate outputs',
        M2='NOT_RUN',Q4_GPU='NOT_RUN',new_model_forwards=0))
    def execute(label,command):
        nonlocal phase
        phase=label
        for path,h in files.items():
            if sha(Path(path))!=h:raise RuntimeError('Prospective source/material changed')
        save(audit/(label+'-START.json'),dict(command=command,elapsed_s=time.monotonic()-started))
        with (audit/(label+'.stdout.log')).open('x') as stdout,(audit/(label+'.stderr.log')).open('x') as stderr:
            result=subprocess.run(command,stdout=stdout,stderr=stderr)
        save(audit/(label+'-EXIT.json'),dict(returncode=result.returncode,elapsed_s=time.monotonic()-started))
        return result.returncode
    try:
        terminal=r/'primary-postprocess-03/STATUS.json'
        while not terminal.exists():
            if time.monotonic()-started>18*3600:raise RuntimeError('Primary archive has no terminal receipt after18h')
            time.sleep(5)
        if read(terminal)['status']!='COMPLETE':
            save(audit/'STATUS.json',dict(status='DEFERRED_PRIMARY_REPAIR_REQUIRED',primary_archive=read(terminal),no_new_native_work=True));return
        primary=read(r/'primary-evaluation-02/STATUS.json')
        if not primary['status'].startswith('PRIMARY_'):raise RuntimeError('Primary native/pilot/formal eligibility failed')
        if read(r/'d14-run-01/FORMAL_STAGE_STATUS-01.json')['status']!='COMPLETE':raise RuntimeError('Admitted D14 formal stage incomplete')
        w=r/'f-run-01'
        with (r/'STUDY_SCHEDULING.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            for path,h in files.items():
                if sha(Path(path))!=h:raise RuntimeError('Prospective source/material changed while waiting')
            prepare=[sys.executable,'-B',str(source/'prepare.py')]
            paths=dict(integration=r/'f-source-06/F',runtime=r/'f-runtime-01',work=w,builds=r/'f-deployment-build-01',
                assets=r/'f-assets-checked-01',vocabulary_build=r/'f-vocabulary-build-03',materials=source)
            for key,value in paths.items():prepare+=['--'+key.replace('_','-'),str(value)]
            if execute('prepare',prepare)!=0:raise RuntimeError('Retained native no-forward cohort preparation failure')
            prepared=w/'inputs-formal-02/PROSPECTIVE_COHORT_CHECKED.json';ready=read(prepared)
            if not ready['passed'] or ready['model_forwards']!=0:raise RuntimeError('Prospective cohort eligibility missing')
            admission=audit/'FORMAL_ADMISSION.json'
            save(admission,dict(status='ADMITTED_AFTER_NATIVE_QUALIFICATION_AND_PROSPECTIVE_COHORT_FREEZE',
                utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prepared_sha256=sha(prepared),
                original_primary_assessment_sha256=sha(r/'primary-evaluation-02/FORMAL_PANEL_ASSESSMENT.json'),
                reason='Complete-service cross-family transfer remains unanswered by the three exposed unbalanced pilot roots. All six native paths qualify; exact12-root cohort is fixed before its outcomes. No favorable pilot-speed threshold or subset selection.',
                measurements=288,primers=48,reference_requests=14,request_and_row_forecast=ready,
                earlier_NOT_REGISTERED_scope_preserved=True,arithmetic_or_reference_changed=False))
            command=[sys.executable,'-B',str(source/'run_panel.py')]
            for key,value in dict(work=w,baseline=r/'run-01',runtime=r/'f-runtime-01',builds=r/'f-deployment-build-01',repo=r/'repository-01',integration=r/'f-source-06/F').items():command+=['--'+key,str(value)]
            command+=['--source-commit',a.source_commit]
            code=execute('formal',command);slots=read(w/'panel-01/ALL_SLOT_STATUS.json')
            ledger=[json.loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()]
            attempted=any(x.get('event')=='RESERVE' and x.get('phase')=='confirmation' for x in ledger)
            complete=code==0 and slots and slots['complete_workers']==24 and (w/'panel-01/RESULTS.json').exists()
            save(w/'FORMAL_STAGE_STATUS-01.json',dict(status='COMPLETE' if complete else 'QUALIFIED_WITH_RETAINED_FORMAL_FAILURE',
                returncode=code,actual_slot_status=slots,formal_performance='COMPLETE' if complete else ('FAILED_OR_PARTIAL_RETAINED' if attempted else 'NOT_RUN'),
                admission_sha256=sha(admission),qualification_summary_sha256=ready['qualification_sha256'],no_native_formal_retries=True))
            if not complete:raise RuntimeError('Retain all actual slots; no selected native retry or successful-subset inference')
        phase='ARCHIVE_COMPLETE_F_SCOPE'
        completion=audit/'F_FORMAL_EXPORT_COMPLETION.json'
        save(completion,dict(status='COMPLETE',finite_qualification_passed=True,formal_performance_status='COMPLETE',
            formal_stage_sha256=sha(w/'FORMAL_STAGE_STATUS-01.json'),results_sha256=sha(w/'panel-01/RESULTS.json'),
            earlier_finite_primary_archive_scope_preserved=True,actual_slot_status=slots))
        previous=read(r/'primary-postprocess-03/F-SUPPORT_MANIFEST.private.json');support=list(previous['files'])
        def add(name,path):support.append(dict(name=name,source=str(path),sha256=sha(path)))
        add('completion/F_FORMAL_COMPLETION_02.json',completion)
        for prior_dir in (r/'f-confirmation-audit-01',r/'f-tokenizer-byte-audit-03'):
            for prior_path in sorted(prior_dir.glob('*')):
                if prior_path.is_file() and prior_path.suffix in ('.json','.log') and 'private' not in prior_path.name:
                    add('retained-preparation/'+prior_dir.name+'/'+prior_path.name,prior_path)
        for name in ('BUILD.json','DEPENDENCIES.json','compile/command.json','link/command.json'):
            add('vocabulary-byte-observer/'+name,r/'f-vocabulary-build-03'/name)
        add('prior-ledger/PRIOR_PRIMARY_LEDGER_BINDING.json',r/'f-confirmation-audit-01/PRIOR_PRIMARY_LEDGER_BINDING.json')
        for path in sorted(audit.glob('*')):
            if path.is_file() and path!=completion and path.suffix in ('.json','.log'):
                add('f-confirmation-02/'+path.name,path)
        manifest=audit/'F-SUPPORT_MANIFEST.private.json'
        save(manifest,dict(schema='linux-transfer.exact-support-files.v1',files=support,
            not_produced_optional_records=previous.get('not_produced_optional_records',[])))
        out=r/'f-public-export-04';command=[sys.executable,'-B',str(a.exporter),'--work',str(w),'--runtime',str(r/'f-runtime-01'),
            '--builds',str(r/'f-deployment-build-01'),'--completion',str(completion),'--support-manifest',str(manifest),'--out',str(out)]
        if execute('export',command)!=0:raise RuntimeError('Retained complete-scope archive/readback failure; never replay native slots')
        save(audit/'STATUS.json',dict(status='F_CONFIRMATION_COMPLETE_AND_ARCHIVED',elapsed_s=time.monotonic()-started,
            measurements=288,primers=48,reference_requests=14,results_sha256=sha(w/'panel-01/RESULTS.json'),
            archive_scope_sha256=sha(out/'EXPORT_SCOPE.json'),local_readback_sha256=sha(out/'LOCAL_READBACK.json'),
            public_upload='NOT_RUN',M2='NOT_RUN',Q4_GPU='NOT_RUN',no_selected_native_retry=True))
    except BaseException as error:
        if not (audit/'STATUS.json').exists():save(audit/'STATUS.json',dict(status='FAILED_RETAINED',phase=phase,error=str(error),
            elapsed_s=time.monotonic()-started,no_selected_native_retry=True))
        raise

if __name__=='__main__':main()
