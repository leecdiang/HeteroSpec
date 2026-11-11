"""Finite sequential regression continuation; never overlaps native workers."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path('E:/rtx160/research')
REPO=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
CODE=REPO/'benchmarks/rtx_llama_repair_v1/host_execution'
LOG=Path('D:/rtx160/operations/run_logged.py')


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,script,args):
    subprocess.run([sys.executable,'-B',str(LOG),name,sys.executable,'-B',str(CODE/script),*args],cwd=REPO,check=True)
def passed(bundle):
    report=read(bundle/'REGRESSION_AUDIT.json')
    assert report['all_reference_equal'] and not report['observer_errors'],report
    receipt=read(bundle/'units/regression/RECEIPT.json')
    assert receipt['success'] and receipt['active_processes_after_wait']==0


def main():
    b8=ROOT/'qwen8b02';b14=ROOT/'qwen14b02';deadline=time.monotonic()+7200
    while not (Path('D:/rtx160/operations/QWEN8B_RUN02.json')).exists():
        assert time.monotonic()<deadline,'bounded wait expired'
        time.sleep(10)
    passed(b8)
    assert read(b8/'ORIGINAL_R_CONTROL.json')['status']=='ORIGINAL_R_PRESERVED'
    for command,name in [('admit','QWEN14B_ADMISSION02'),('run','QWEN14B_RUN02')]:
        assert read(Path('D:/rtx160/operations')/(name+'.json'))['exit_code']==0
    passed(b14)
    run('QWEN14B_ORIGINAL_CONTROL05','qwen_original_control.py',['--repo',str(REPO),'--bundle',str(b14)])
    paths=[b/name for b in (b8,b14) for name in ('REGRESSION_AUDIT.json','ORIGINAL_R_CONTROL.json','EPOCH.json')]
    paths += [CODE/'qwen_regression.py',CODE/'qwen_original_control.py',Path(__file__)]
    report={'status':'CROSS_MODEL_REGRESSION_PASS','families':['Qwen3-8B','Qwen3-14B'],
      'new_candidate_requests':336,'additional_immutable_original_R_requests':56,
      'evidence':{str(p):sha(p) for p in paths},
      'scope':'Previously exposed fixed panels; exact original assets, new combined-policy executions; original R full-vector controls.'}
    with (ROOT/'CROSS_MODEL_REGRESSION.json').open('x') as f:json.dump(report,f,indent=2)
    print(report['status'],flush=True)


if __name__=='__main__':main()
