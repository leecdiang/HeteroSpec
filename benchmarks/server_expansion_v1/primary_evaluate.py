"""After PR205/206 qualification, run bounded pilots and assess formal admission.

No numerical pass is inferred from process exit. Unregistered F confirmation,
M2 and Q4 GPU studies cannot be launched by this queue.
"""
from pathlib import Path
import argparse, datetime, fcntl, hashlib, json, subprocess, sys, time

def read(path):return json.loads(path.read_text()) if path.exists() else None
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def save(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--deadline-utc')
    a=parser.parse_args();r=a.root.resolve();audit=a.audit.resolve();audit.mkdir(exist_ok=False)
    deadline=datetime.datetime.fromisoformat(a.deadline_utc) if a.deadline_utc else None
    assert deadline is None or deadline.tzinfo is not None
    phase='WAIT_PRIMARY_QUALIFICATION_PAIR';started=time.monotonic()
    source=Path(__file__).parent
    source_files={str(p):sha(p) for p in source.glob('*.py')}
    save(audit/'SOURCE_FREEZE.private.json',dict(files=source_files,deadline_utc=deadline.isoformat() if deadline else None,
        policy='All actual native gates before bounded pilots; formal admission based on eligibility, budget and remaining time, never a favorable pilot speed threshold',
        M2='NOT_RUN',Q4_GPU='NOT_RUN',F_formal='Requires separate prospective12-root exposure audit; never substitute old development roots'))
    def execute(label,command):
        nonlocal phase
        phase=label
        for p,h in source_files.items():assert sha(Path(p))==h,'Primary queue source changed'
        save(audit/(label+'-START.json'),dict(command=command,elapsed_s=time.monotonic()-started))
        with (audit/(label+'.stdout.log')).open('x') as stdout,(audit/(label+'.stderr.log')).open('x') as stderr:
            result=subprocess.run(command,stdout=stdout,stderr=stderr)
        save(audit/(label+'-EXIT.json'),dict(returncode=result.returncode,elapsed_s=time.monotonic()-started))
        return result.returncode
    try:
        pair=r/'mainline-native-queue-02/STATUS.json'
        while not pair.exists():
            if time.monotonic()-started>12*3600:raise RuntimeError('Primary qualification pair has no terminal receipt after12h')
            time.sleep(3)
        assert read(pair)['status']=='PRIMARY_QUALIFICATION_PAIR_COMPLETE','Primary native gates failed; do not bypass'
        pilot_results={}
        with (r/'STUDY_SCHEDULING.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            assert (r/'q32-download-audit-01/PAUSE_DOWNLOAD').exists(),'Q32 download must continue yielding to mainline'
            lanes={
                'F':dict(source=r/'f-source-05/F',runtime=r/'f-runtime-01',work=r/'f-run-01',builds=r/'f-deployment-build-01',qualification=r/'f-run-01/qualification-complete-03'),
                'D14':dict(source=r/'d14-source-07/D14',runtime=r/'d14-runtime-02',work=r/'d14-run-01',builds=r/'d14-deployment-build-02',qualification=r/'d14-run-01/qualification-03')}
            for lane,paths in lanes.items():
                paths['repo']=r/'repository-01';paths['out']=paths['work']/'qualification-pilot-clean-01'
                cmd=[sys.executable,'-B',str(source/'primary_pilot.py')]
                for name,value in paths.items():cmd+=['--'+name,str(value)]
                assert execute(lane+'-bounded-pilot',cmd)==0,'Retained native pilot failure: '+lane
                pilot_results[lane]=read(paths['out']/'STATUS.json')
                assert pilot_results[lane]['status']=='COMPLETE' and pilot_results[lane]['all_six_arms']
            # D14's original prospective24-worker plan is ready. Pilot speed is
            # descriptive only; even a negative speed result is publishable.
            d14=r/'d14-run-01';plan=read(d14/'panel-01/PLAN.json')
            assert plan['measurements']==384 and plan['primers']==48 and len(plan['workers'])==24
            assert read(d14/'panel-01/PROSPECTIVE_ORDER.json')['plan_sha256']==sha(d14/'panel-01/PLAN.json')
            ledger=[json.loads(x) for x in (d14/'ledger.jsonl').read_text().splitlines()]
            assert not any(x.get('phase')=='confirmation' for x in ledger),'No attempted formal slot may be replayed'
            reserved=[x for x in ledger if x.get('event')=='RESERVE']
            charged_requests=sum(x['requests'] for x in reserved);charged_rows=sum(x['rows'] for x in reserved)
            sys.path.insert(0,str(r/'d14-runtime-02'))
            from host import reservation
            future=[reservation(read(d14/'panel-01'/x['job'])) for x in plan['workers']]
            # Include a bounded allowance for the18-endpoint pristine R job.
            future_requests=sum(x[0] for x in future)+18
            future_rows=sum(x[1] for x in future)+30000
            budget_ok=charged_requests+future_requests<=2560 and charged_rows+future_rows<=12000000
            record_paths=[Path(x['path']) for x in pilot_results['D14']['records']]
            records=[read(p) for p in record_paths]
            worst_call=max(c['service_s'] for x in records for c in x['calls'] if c['kind']=='measurement')
            estimate_s=24*(max(x['adapter_invocation_inclusive_s'] for x in records)+16*worst_call)+900
            now=datetime.datetime.now(datetime.timezone.utc)
            time_ok=deadline is None or (deadline-now).total_seconds()>=estimate_s
            f_ready=r/'f-run-01/inputs-formal-01/PROSPECTIVE_COHORT_CHECKED.json'
            assessment=dict(status='ASSESSED_AFTER_BOTH_NATIVE_QUALIFICATIONS_AND_PILOTS',utc=now.isoformat(),
                primary_qualification_sha256=sha(pair),
                pilots={k:dict(status=v['status'],scope=v['scope'],service_totals_s=v['service_totals_s'],LP_over_each_control=v['LP_over_each_control']) for k,v in pilot_results.items()},
                D14=dict(formal_admitted=budget_ok and time_ok,reason='Qualified fixed exposed-root deployment panel, all six strong controls, request/row and wall-time admission; speed sign does not select admission',
                    charged_requests=charged_requests,charged_reserved_row_bound=charged_rows,future_request_allowance=future_requests,future_reserved_row_allowance=future_rows,
                    budget_ok=budget_ok,time_ok=time_ok,conservative_estimated_panel_s=estimate_s,plan_sha256=sha(d14/'panel-01/PLAN.json')),
                F=dict(formal_admitted=False,prospective_new_cohort_ready=f_ready.exists(),
                    reason='A new12-root confirmation requires completed ID/text/token exposure exclusions and prospective registration; old diagnostic roots cannot replace it',
                    current_scope='Complete finite Linux transfer qualification and exposed-root bounded clean-service pilot'),
                next_extra_experiment='Evaluate real physical-q8 versus Q4 numeric-type extension from primary results; neither is auto-launched merely to add experiments')
            save(audit/'FORMAL_PANEL_ASSESSMENT.json',assessment)
            if budget_ok and time_ok:
                cmd=[sys.executable,'-B',str(r/'d14-source-07/D14/run_panel.py')]
                for key,value in dict(work=d14,baseline=r/'run-01',runtime=r/'d14-runtime-02',builds=r/'d14-deployment-build-02',repo=r/'repository-01').items():cmd+=['--'+key,str(value)]
                cmd+=['--source-commit','fefd9e1054597c4ed4732ce9e9c2245f53a596f4']
                code=execute('D14-formal-panel',cmd)
                slots=read(d14/'panel-01/ALL_SLOT_STATUS.json')
                complete=code==0 and slots and slots['complete_workers']==24 and (d14/'panel-01/RESULTS.json').exists()
                save(d14/'FORMAL_STAGE_STATUS-01.json',dict(status='COMPLETE' if complete else 'QUALIFIED_WITH_RETAINED_FORMAL_FAILURE',
                    returncode=code,qualification_status_sha256=sha(d14/'CONTINUATION-03-STATUS.json'),
                    assessment_sha256=sha(audit/'FORMAL_PANEL_ASSESSMENT.json'),actual_slot_status=slots,
                    no_native_formal_retries=True))
                assert complete,'Formal failure/partial slots retained; never label them NOT_RUN or rerun selected native slots'
            save(audit/'STATUS.json',dict(status='PRIMARY_ASSESSED_AND_ADMITTED_D14_PANEL_COMPLETE' if budget_ok and time_ok else 'PRIMARY_QUALIFIED_ASSESSED_FORMAL_NOT_ADMITTED',
                elapsed_s=time.monotonic()-started,assessment_sha256=sha(audit/'FORMAL_PANEL_ASSESSMENT.json'),
                F_formal='NOT_RUN_NEW_COHORT_NOT_REGISTERED',M2='NOT_RUN',Q4_GPU='NOT_RUN',next='Archive/readback complete current evidence and evaluate the next scientifically useful extension'))
    except BaseException as error:
        save(audit/'STATUS.json',dict(status='FAILED_RETAINED',phase=phase,error=str(error),elapsed_s=time.monotonic()-started,
            no_selected_native_retry=True));raise

if __name__=='__main__':main()
