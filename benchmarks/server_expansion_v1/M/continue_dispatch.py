"""Retain checker failure and completed diagnostics, then execute unstarted M1.

Repairs a Python callable/list name collision only. No native binary, reference,
job, proposal stream or completed native request is replaced or replayed.
"""
from pathlib import Path
import argparse, datetime, json, subprocess, sys
import run_m1 as m

def main():
    p=argparse.ArgumentParser()
    for key in ('work','baseline','repo','builds','runtime','observer-builds','failed-source'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();m.load_runtime(a.runtime.resolve());w=a.work.resolve();source=Path(__file__).parent;phase='DISPATCH_CHECKER_REPAIR';status='FAILED_RETAINED'
    ledger=[json.loads(x) for x in (w/'ledger.jsonl').read_text().splitlines()]
    m.need(not any(x.get('event')=='RESERVE' and x.get('phase')=='confirmation' for x in ledger),'Only unstarted formal panel may continue')
    m.need(m.read(w/'PIPELINE_STATUS.json')['status']=='FAILED_RETAINED','Retain original failure')
    m.save(w/'DISPATCH_CONTINUATION-02.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        reason='Projection checker callable verify was overwritten by a list after first arm; second arm native runs had completed successfully',
        failed_source_sha256=m.sha(a.failed_source),fixed_source_sha256=m.sha(source/'check_dispatch.py'),
        original_status_sha256=m.sha(w/'PIPELINE_STATUS.json'),original_failure_log_sha256=m.sha(w/'capability-negatives-phase-01.log'),
        formal_slots_previously_reserved=0,numerical_or_reference_changes=False,native_replays=False))
    def event(label):
        with (w/'pipeline-events.jsonl').open('a') as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=label))+'\n')
    try:
        event(phase);cmd=[sys.executable,'-B',str(source/'check_dispatch.py'),'--resume-complete-native']
        for key in ('work','baseline','runtime','repo','builds','observer-builds'):cmd+=['--'+key,str(getattr(a,key.replace('-','_')).resolve())]
        with (w/'dispatch-checker-phase-02.log').open('xb') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        phase='FIXED_BALANCED_M1_CONFIRMATION';event(phase);cmd=[sys.executable,'-B',str(source/'run_panel.py')]
        for key in ('work','baseline','repo','builds','runtime'):cmd+=['--'+key,str(getattr(a,key).resolve())]
        with (w/'confirmation-phase-01.log').open('xb') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        phase='COMPLETE';status='COMPLETE';event(phase)
    finally:m.save(w/'PIPELINE_STATUS-02.json',dict(status=status,last_phase=phase,M2='NOT_RUN',original_failure_preserved=True,no_native_replays=True,no_formal_retries=True))

if __name__=='__main__':main()
