"""Owned gated controller; CPU fixtures cannot become a scientific fallback."""
import sys
sys.dont_write_bytecode=True
if sys.stdin.readline()!='LAUNCH_GO\n':raise SystemExit('owned launcher required')
import json
import os
from pathlib import Path
import time
from common import HERE,BASE,JOURNALS,OUTPUTS,load,write_new,need
from supervisor import supervise

case=load(sys.argv[1]);need(case['purpose'] in ('CPU_INTEGRATION','FROZEN_SCIENCE'),'purpose')
need(Path(case['active']).resolve().parent==OUTPUTS.resolve(),'flat per-attempt output topology required')
need(JOURNALS.resolve() in Path(case['journal_dir']).resolve().parents,'owned external journal path')
if case['purpose']=='FROZEN_SCIENCE':
    from native_case import execute
    raise SystemExit(execute(case))

# CPU fault controls are reachable only through this explicit CPU-only entry.
from identity import verify_loaded
from storage import Watch
events=[]
if case.get('notification_loss'):
    original_accept=Watch.accept
    def loss(self,data):
        self.journal.emit('CPU_INJECTED_NOTIFICATION_LOSS',actual_notification_bytes=len(data))
        return original_accept(self,b'')
    Watch.accept=loss

def received(row,proc):
    events.append(row)
    if row['event']=='READY':
        if case.get('identity_delay'):time.sleep(case['identity_delay'])
        evidence=verify_loaded(proc.pid,case['required_modules'],strict=False)
        write_new(Path(case['journal_dir'])/'MODULE_GATE.json',evidence)
        return b'GO\n'

def resource_failure():raise OSError('CPU injected actual observer read failure')
def slow_directory():
    time.sleep(1.2)
    return dict(bytes=0,files=0,historical_files_scanned=0)
def post():
    if case.get('post_hash_delay'):time.sleep(case['post_hash_delay'])
    need((Path(case['active'])/'DATA.bin').stat().st_size==case.get('frames',14)*4096,'missing/truncated CPU output')
    raw=[json.loads(s) for s in (Path(case['journal_dir'])/'stdout.log').read_text().splitlines() if s]
    need(any(x['event']=='CPU_RESULT' for x in raw),'missing CPU completion event')
    return dict(status='CPU_OUTPUT_AUDITED',frames=case.get('frames',14))

result=supervise([sys.executable,'-B',str(HERE/'cpu_child.py'),sys.argv[1]],case['active'],case['protected_roots'],case['journal_dir'],
    case.get('native_timeout',5),received,post_audit=post,
    read_resource=resource_failure if case.get('resource_failure') else None,
    read_directory=slow_directory if case.get('monitor_stall') else None,
    log_soft=case.get('native_log_soft',16*1024**2))
write_new(Path(case['case_dir'])/'CONTROLLER_RESULT.json',dict(result=result,events=events,CPU_only=True,model_requests=0,graph_computes=0,GPU_queries=0))
raise SystemExit(0 if result['status']=='ADMITTED' else 1)
