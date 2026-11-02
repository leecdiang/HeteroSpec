"""Run independent reconstruction only after all registered timing has finished."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

REPO=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
CODE=REPO/'benchmarks/rtx_llama_repair_v1/host_execution'
OPS=Path('D:/rtx160/operations');ROOT=Path('E:/rtx160/research');EPOCH=ROOT/'epoch07'


def run(name,script,args,python=sys.executable):
    subprocess.run([sys.executable,'-B',str(OPS/'run_logged.py'),name,str(python),'-B',str(CODE/script),*map(str,args)],cwd=REPO,check=True)


def main():
    done=OPS/'CONFIRMATION_SEQUENCE07.json';deadline=time.monotonic()+86400
    while not done.exists():
        assert time.monotonic()<deadline,'finite confirmation wait expired'
        time.sleep(10)
    assert json.loads(done.read_text())['exit_code']==0,'confirmation did not finish'
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    out=ROOT/'independent_qualification01';out.mkdir(exist_ok=False)
    run('INDEPENDENT_QUALIFICATION01','independent_qualification.py',['--bundle',EPOCH,'--out',out/'REPORT.json'],
        'D:/HeteroSpec-PC/.venv-analysis/Scripts/python.exe')
    assert not (EPOCH/'INDEPENDENT_QUALIFICATION.json').exists()
    shutil.copy2(out/'REPORT.json',EPOCH/'INDEPENDENT_QUALIFICATION.json')
    run('LEDGER_AUDIT01','audit_ledger.py',['--root',ROOT,'--out',ROOT/'LEDGER_AUDIT.json'])
    run('COLLECT_RESULTS01','collect_results.py',['--out',CODE/'records'])
    print('INDEPENDENT_QUALIFICATION_LEDGER_AND_RECEIPTS_COMPLETE',flush=True)


if __name__=='__main__':main()
