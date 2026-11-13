"""One owned process, one JSONL attempt record; no CUDA imports or host security changes.
Use only after native qualification and owner approval described in RUNBOOK_ZH.md.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time


def completed(path):
    if not path.exists(): return []
    # A writer may be in the middle of a line. Only complete records count.
    data=path.read_bytes(); parts=data.split(b'\n')[:-1]
    return [json.loads(x) for x in parts if x.strip()]


def run(command, results, timeout=600, total_timeout=21600):
    start=time.monotonic();last=start;count=0
    log=Path(str(results)+'.stderr.log')
    with log.open('wb') as err:
        p=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=err,stderr=err)
        try:
            while p.poll() is None:
                events=completed(results)
                n=len(events)
                if n>count:last=time.monotonic();count=n
                if time.monotonic()-last>timeout or time.monotonic()-start>total_timeout:
                    raise TimeoutError('load/request or total wall-clock limit')
                time.sleep(.1)
            if p.returncode:raise RuntimeError(f'worker exit {p.returncode}; see {log}')
            events=completed(results)
            if not events or events[-1].get('event')!='done':raise RuntimeError('no final done receipt')
            return events
        finally:
            if p.poll() is None:
                p.kill();p.wait(timeout=10)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('session');a.add_argument('--exe',required=True);a.add_argument('--model',required=True)
    a.add_argument('--execute',action='store_true',help='explicit native execution; not an approval substitute')
    x=a.parse_args();s=Path(x.session).resolve();out=s.with_suffix('.results.jsonl')
    cmd=[str(Path(x.exe).resolve()),str(Path(x.model).resolve()),str(s.with_suffix('.tsv')),str(out),str(s.with_suffix('.capture'))]
    if not x.execute:
        print(json.dumps({'status':'PREVIEW_ONLY','argv':cmd},indent=2));raise SystemExit(0)
    if out.exists():raise SystemExit('result already exists; preserve and choose a new attempt directory')
    ledger=s.parent/'attempts.jsonl';old=completed(ledger)
    first=old[0]['wall_start'] if old else time.time()
    budget=21600-(time.time()-first)
    specs=json.loads(s.read_text(encoding='utf-8'))
    reserved=sum(z['requests_reserved'] for z in old)+len(specs)
    rows=sum(z['rows_reserved'] for z in old)+sum(len(z['prompt_ids'])+128 for z in specs)
    # Qualifications and retries must be in this same ledger before formal sessions.
    # Direct worker use bypasses this accounting and is forbidden by the runbook.
    if reserved>228 or rows>204288 or len(old)>=18 or budget<=0:raise SystemExit('declared campaign budget exhausted')
    receipt={'session':s.name,'wall_start':time.time(),'requests_reserved':len(specs),'rows_reserved':sum(len(z['prompt_ids'])+128 for z in specs),'argv':cmd}
    with ledger.open('a',encoding='utf-8') as f:f.write(json.dumps(receipt)+'\n');f.flush()
    run(cmd,out,total_timeout=budget)
