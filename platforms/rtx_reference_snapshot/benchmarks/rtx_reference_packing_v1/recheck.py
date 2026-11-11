"""Read saved traces and independent reference; never reschedule formal cells."""
import gzip
import json
from pathlib import Path
import sys
import checker
from prepare import sha

def inspect(root):
    root=Path(root);plan=json.loads((root/'PLAN.json').read_bytes());resources={r['id']:r for r in plan['resources']};checks=[]
    for i,cell in enumerate(plan['cells']):
        d=root/f'formal/{i:04d}';receipt=json.loads((d/'CELL_RESULT.json').read_bytes());assert receipt['status']=='PASS'
        wpath=root/'inputs'/(cell['workload']+'.json');assert sha(wpath)==receipt['input_sha256']
        assert sha(d/'OUTPUT.json')==receipt['output_sha256'] and sha(d/'trace.jsonl.gz')==receipt['trace_sha256']
        with gzip.open(d/'trace.jsonl.gz','rt',encoding='utf-8') as f:trace=[json.loads(line) for line in f]
        result=json.loads((d/'OUTPUT.json').read_bytes());check=checker.validate(json.loads(wpath.read_bytes()),resources[cell['resource']],trace,result['output'])
        assert check==receipt['checker'];checks.append(dict(index=i,checker=check))
    return dict(cells=len(checks),independent_saved_trace_checks='PASS',new_schedules=0,checks=checks)
if __name__=='__main__':
    root=Path(sys.argv[1]);out=Path(sys.argv[2]);data=inspect(root)
    with out.open('x',encoding='utf-8') as f:json.dump(data,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(dict(cells=data['cells'],status='PASS',new_schedules=0)))
