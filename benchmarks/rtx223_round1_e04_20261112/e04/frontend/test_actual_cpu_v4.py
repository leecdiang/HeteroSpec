from pathlib import Path
import json
from dep_witness_v3 import resolved_cpu,DependencyRefusal
p=Path(__file__).resolve().parent
driver=(p/'run-v3/loop4-effective.stderr.log').read_text(encoding='utf8')
actual=(p/'run-v3/loop4-compile.stderr.log').read_text(encoding='utf8')
left=resolved_cpu(driver);right=resolved_cpu(actual)
if not left or left!=right or right!=json.loads(json.dumps(right)):raise RuntimeError('actual CPU versus prepared CPU or JSON schema differs')
if not all(isinstance(v,list) and len(v)==2 for v in right):raise RuntimeError('CPU output is not JSON-stable')
for bad in ['clang -cc1 version 21.1.0\n',actual+'\n'+driver]:
    try:resolved_cpu(bad)
    except DependencyRefusal:pass
    else:raise RuntimeError('missing or duplicate actual invocation admitted')
print(json.dumps({'new_checks':3,'status':'PASS','resolved_cpu':right[0][1],'feature_entries':len(right)-1,'real_v3_traces_used':True,'GPU_launches':0}))
