"""Archive terminal primary scopes; keep heavy reads after formal timing."""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time

def read(p):return json.loads(p.read_text()) if p.exists() else None
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
    return h.hexdigest()
def save(p,j):
    with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--exporter',type=Path,required=True);parser.add_argument('--include-failed-primary',action='store_true')
    a=parser.parse_args();r=a.root.resolve();audit=a.audit.resolve();audit.mkdir(exist_ok=False)
    primary=r/'primary-evaluation-02';terminal=primary/'STATUS.json';started=time.monotonic()
    save(audit/'START.json',dict(status='WAIT_PRIMARY_TERMINAL_SCOPE',exporter_sha256=sha(a.exporter),
        own_source_sha256=sha(Path(__file__)),new_model_forwards=0,public_upload='NOT_RUN'))
    try:
        while not terminal.exists():
            if time.monotonic()-started>18*3600:raise RuntimeError('Primary terminal scope missing after18h')
            time.sleep(5)
        result=read(terminal);primary_ok=result['status'].startswith('PRIMARY_')
        if not primary_ok and not a.include_failed_primary:
            save(audit/'STATUS.json',dict(status='DEFERRED_PRIMARY_REPAIR_REQUIRED',primary_status=result,
                no_archive_started=True,Q32_download_still_paused=True,new_model_forwards=0))
            return
        outcomes={}
        for lane in ('F','D14'):
            work=r/('f-run-01' if lane=='F' else 'd14-run-01')
            q=work/('qualification-registry-04' if lane=='F' else 'qualification-03')
            native_status=r/('f-registry-completion-04/STATUS.json' if lane=='F' else 'd14-run-01/CONTINUATION-03-STATUS.json')
            native=read(native_status);neg=read(work/'capability-negatives-01/CHECKED.json')
            qualified=bool(native and native['status']=='QUALIFIED_FORMAL_NOT_RUN' and neg and neg['passed'] and (q/'REGISTRY.json').exists())
            ledger=[json.loads(x) for x in (work/'ledger.jsonl').read_text().splitlines()]
            attempted=any(x.get('event')=='RESERVE' and x.get('phase')=='confirmation' for x in ledger)
            slots=read(work/'panel-01/ALL_SLOT_STATUS.json');formal_stage=read(work/'FORMAL_STAGE_STATUS-01.json')
            formal_complete=bool(formal_stage and formal_stage['status']=='COMPLETE' and slots and slots['complete_workers']==24)
            formal_state='COMPLETE' if formal_complete else ('FAILED_OR_PARTIAL_RETAINED' if attempted else 'NOT_RUN')
            status=('COMPLETE' if formal_complete else 'QUALIFIED_FORMAL_NOT_RUN') if primary_ok and qualified else (
                'QUALIFIED_WITH_RETAINED_FORMAL_FAILURE' if qualified and attempted else
                ('QUALIFIED_WITH_RETAINED_PRIMARY_FAILURE' if qualified else 'FAILED_SCOPE_RETAINED'))
            completion=audit/(lane+'-EXPORT_COMPLETION.json')
            save(completion,dict(status=status,finite_qualification_passed=qualified,formal_performance_status=formal_state,
                qualification_status_path=str(native_status) if native else None,
                qualification_status_sha256=sha(native_status) if native else None,
                primary_status_sha256=sha(terminal),actual_slot_status=slots,
                source='Terminal-scope archive observer; not a native HOST or fabricated numerical result'))
            files=[];missing=[]
            def add(name,path,required=True):
                if not path.is_file():
                    if required:raise RuntimeError('Missing required scientific record: '+str(path))
                    missing.append(name);return
                files.append(dict(name=name,source=str(path),sha256=sha(path)))
            add('completion/EXPORT_COMPLETION.json',completion)
            old=r/('f-study-audit-01' if lane=='F' else 'd14-study-audit-01')
            names=('SOURCE_FREEZE.private.json','STATUS.json','prepare-START.json','prepare-COMPLETE.json','prepare.stdout.log','prepare.stderr.log',
                'reference-START.json','reference-COMPLETE.json','reference.stdout.log','reference.stderr.log','qualify-START.json','qualify.stdout.log','qualify.stderr.log')
            for name in names:add('original-coordinator/'+name,old/name)
            for name in ('USER_PRIORITY.json','HANDOFF.json','IDLE_COORDINATOR_BOUNDARY.json'):
                add('priority/'+name,r/'mainline-priority-01'/name)
            for directory in ('mainline-native-queue-01','mainline-native-queue-02','mainline-native-queue-03','primary-evaluation-01','primary-evaluation-02'):
                for path in sorted((r/directory).glob('*')):
                    if path.is_file() and path.suffix in ('.json','.log'):
                        add('primary/'+directory+'/'+path.name,path)
            builds=r/('f-deployment-build-01' if lane=='F' else 'd14-deployment-build-02')
            runtime=r/('f-runtime-01' if lane=='F' else 'd14-runtime-02')
            add('builds/BUILD_COMPLETE.json',builds/'BUILD_COMPLETE.json')
            if lane=='F':
                for name in ('assets-START.json','assets-COMPLETE.json','assets.stdout.log','assets.stderr.log'):
                    add('original-coordinator/'+name,old/name)
                for directory in ('f-eog-completion-02','f-retained-audit-01','f-retained-audit-03','f-retained-audit-04','f-marker-completion-03','f-registry-completion-04'):
                    for name in ('SOURCE_FREEZE.private.json','STATUS.json'):add(directory+'/'+name,r/directory/name,required=False)
                    add(directory+'/coordinator.log',r/(directory+'.log'),required=False)
                add('assets/CHECKED.json',r/'f-assets-checked-01/CHECKED.json')
                for name in ('FREEZE.json','BEFORE.json','LLAMA_INITIAL.json','RULE_TRANSFER.json'):
                    add('rules/'+name,r/'f-rule-freeze-01'/name)
                for role in ('target','draft'):add('models/'+role+'-VERIFIED.json',r/'f-models-01'/(role+'-VERIFIED.json'))
                add('marker-build/BUILD_COMPLETE.json',r/'f-marker-build-01/BUILD_COMPLETE.json')
                for role in ('loop4','packed'):
                    for name in ('BUILD.json','DEPENDENCIES.json','compile/command.json','compile/stdout.log','link/command.json','link/stdout.log'):
                        add('marker-build/'+role+'/'+name,r/'f-marker-build-01'/role/name)
                for epoch in ('01','02'):
                    for name in ('BUILD.json','DEPENDENCIES.json','compile/command.json','compile/stdout.log','link/command.json','link/stdout.log'):
                        add('vocabulary-build-'+epoch+'/'+name,r/('f-vocabulary-build-'+epoch)/name,required=False)
            else:
                add('admission/ADMISSION.json',r/'d14-admission-01/ADMISSION.json')
                add('admission/AUDIT_STATUS.json',r/'d14-admission-audit-01/STATUS.json')
                add('continuation-02.log',r/'d14-continuation-02.log')
                add('models/target-VERIFIED.json',r/'d14-models-03/Qwen14B-VERIFIED.json')
            manifest=audit/(lane+'-SUPPORT_MANIFEST.private.json')
            save(manifest,dict(schema='linux-transfer.exact-support-files.v1',files=files,not_produced_optional_records=missing))
            out=r/('f-public-export-02' if lane=='F' else 'd14-public-export-02')
            cmd=[sys.executable,'-B',str(a.exporter),'--work',str(work),'--runtime',str(runtime),
                '--builds',str(builds),'--completion',str(completion),'--support-manifest',str(manifest),'--out',str(out)]
            if 'FAIL' in status:cmd.append('--allow-retained-failure')
            begin=time.monotonic()
            with (audit/(lane+'.stdout.log')).open('x') as stdout,(audit/(lane+'.stderr.log')).open('x') as stderr:
                child=subprocess.run(cmd,stdout=stdout,stderr=stderr)
            record=dict(status='COMPLETE' if child.returncode==0 else 'FAILED_RETAINED',returncode=child.returncode,
                wall_s=time.monotonic()-begin,command=cmd,completion_sha256=sha(completion))
            save(audit/(lane+'-STATUS.json'),record);outcomes[lane]=record
        complete=all(x['status']=='COMPLETE' for x in outcomes.values())
        save(audit/'STATUS.json',dict(status='COMPLETE' if complete else 'FAILED_RETAINED',lanes=outcomes,
            primary_ok=primary_ok,public_upload='NOT_RUN',new_model_forwards=0))
        flag=r/'q32-download-audit-01/PAUSE_DOWNLOAD'
        if complete and primary_ok and flag.exists():flag.rename(audit/'Q32_PAUSE_RESOLVED.json')
    except BaseException as error:
        save(audit/'STATUS.json',dict(status='FAILED_RETAINED',error=str(error),new_model_forwards=0));raise

if __name__=='__main__':main()
