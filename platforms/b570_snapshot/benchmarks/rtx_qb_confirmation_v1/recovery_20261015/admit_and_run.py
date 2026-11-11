"""Authenticate restoration evidence, then invoke the unchanged original session.

The original scientific verify_freeze is called without alteration. No retry.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiment as e

BASE='49b992b2ed1cabd05fad6e234cad2d3418c2b65a'
REG='benchmarks/rtx_qb_confirmation_v1/registration/E2_F0.json'
REPAIR_REG='benchmarks/rtx_qb_confirmation_v1/registration/E2_RESTORATION_F0.json'
OUT=Path('D:/hs-qb-confirmation-v02')
REPO=Path(__file__).resolve().parents[3]

def untouched():
    e.require(not (OUT/'SESSION-5.json').exists(),'session receipt already exists')
    e.require(not (OUT/'EXECUTION.lock').exists(),'execution lock already exists')
    ledger=e.Ledger(OUT)
    e.require(not any(x['slot'].startswith('s5/') for x in ledger.events),'session 5 scientific slot already started')
    e.require(sum(x['kind']!='load' for x in ledger.events)==1350,'unexpected request budget history')
    e.require(sum(x['kind']=='load' for x in ledger.events)==270,'unexpected worker budget history')
    for s in range(5):e.require((OUT/f'SESSION-{s}-COMPLETE.json').exists(),'prior session incomplete')
    e.require(ledger.owned()<43200-252,'old owned time exhausted')
    return ledger

def main():
    p=argparse.ArgumentParser();p.add_argument('--repair-commit',required=True);a=p.parse_args()
    evidence=OUT/'exact_restoration_20261015';evidence.mkdir(exist_ok=False)
    e.save(evidence/'CONTROLLER_STARTED.json',dict(utc=e.utc(),pid=os.getpid(),repair_commit=a.repair_commit))
    try:
        untouched()
        body=subprocess.check_output(['git','show',f'{a.repair_commit}:{REPAIR_REG}'],cwd=REPO)
        remote=subprocess.check_output(['gh','api',f'repos/leecdiang/HeteroSpec/contents/{REPAIR_REG}?ref={a.repair_commit}',
                                        '-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],cwd=REPO)
        e.require(body==remote,'authenticated restoration registration differs')
        repair=json.loads(body)
        for item in repair['files']:
            f=Path(item['path']);e.require(f.stat().st_size==item['bytes'] and e.sha(f)==item['sha256'],'restoration source/evidence differs: '+str(f))
        e.require(e.sha(OUT/'FREEZE.json')==repair['original_FREEZE_sha256'],'original freeze changed')
        e.verify_freeze(OUT,REPO,BASE,REG)
        e.save(evidence/'AUTHENTICATED_READBACK.json',dict(status='PASS',utc=e.utc(),original_F0=BASE,
                                                        repair_commit=a.repair_commit,registration_sha256=e.digest(body),
                                                        unchanged_original_verify_freeze_passed=True))
        untouched()
        e.run_session(OUT,REPO,BASE,REG,5)
        result=e.analyze(OUT)
        e.save(evidence/'E2_ANALYSIS.json',result)
        e.save(evidence/'CONTROLLER_COMPLETE.json',dict(utc=e.utc(),sessions_complete=6,analysis_sha256=e.sha(evidence/'E2_ANALYSIS.json')))
    except BaseException as error:
        e.save(evidence/'CONTROLLER_FAILED.json',dict(utc=e.utc(),error=repr(error),traceback=traceback.format_exc()))
        raise
if __name__=='__main__':main()
