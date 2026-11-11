"""Continue one already running finite qualification, then negatives and M1 only.

No automatic retries or M2. A failed gate preserves its epoch and stops this
coordinator. Other company processes are never signalled.
"""
from pathlib import Path
import argparse, datetime, json, os, subprocess, sys, time
import run_m1 as m

def main():
    p=argparse.ArgumentParser()
    for key in ('work','baseline','repo','builds','runtime'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--qualifier-pid',type=int,required=True);a=p.parse_args();m.load_runtime(a.runtime.resolve());w=a.work.resolve();source=Path(__file__).parent
    events=w/'pipeline-events.jsonl';phase='WAIT_QUALIFICATION';status='FAILED_RETAINED'
    def event(label):
        with events.open('a') as f:f.write(json.dumps(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),phase=label))+'\n');f.flush();os.fsync(f.fileno())
    try:
        event(phase);began=time.monotonic();summary=w/'qualification-01/NATIVE_CHECKS_COMPLETE.json'
        while not summary.exists():
            proc=Path('/proc')/str(a.qualifier_pid)/'stat'
            m.need(proc.exists() and proc.read_text().split()[2]!='Z','Finite qualification exited without complete native proof; preserve failure')
            m.need(time.monotonic()-began<7200,'Finite coordinator wait ceiling');time.sleep(2)
        m.need(m.read(summary)['passed'],'Native qualification failure')
        phase='NATIVE_NEGATIVE_CAPABILITY_GATES';event(phase)
        cmd=[sys.executable,'-B',str(source/'negative_capabilities.py'),'--work',str(w),'--runtime',str(a.runtime.resolve()),'--builds',str(a.builds.resolve())]
        with (w/'capability-negatives-phase-01.log').open('xb') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        phase='FIXED_BALANCED_M1_CONFIRMATION';event(phase)
        cmd=[sys.executable,'-B',str(source/'run_panel.py')]
        for key in ('work','baseline','repo','builds','runtime'):cmd+=['--'+key,str(getattr(a,key).resolve())]
        with (w/'confirmation-phase-01.log').open('xb') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
        phase='COMPLETE';status='COMPLETE';event(phase)
    finally:
        m.save(w/'PIPELINE_STATUS.json',dict(status=status,last_phase=phase,M2='NOT_RUN',no_formal_retries=True,original_panel_unchanged=True))

if __name__=='__main__':main()
