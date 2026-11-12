"""Read completed compiler records during a build; never changes frozen inputs."""
import json
from pathlib import Path
import frozen_build_v2 as b
commands=json.loads((b.FREEZE/'COMMANDS.json').read_bytes());manifest=json.loads((b.FREEZE/'FREEZE.json').read_bytes())
done=[json.loads(line) for line in (b.OUT/'PROGRESS.jsonl').read_text(encoding='utf8').splitlines() if line]
receipts=[]
for row in done:
 if row['code']!=0:continue
 job=commands[row['index']];log=b.OUT/'logs'/f'{row["index"]:03d}-{Path(job["source"]).name}.log'
 receipts.append({**job,'log':str(log),'dependency_sha256':b.sha(job['dependency'])})
result=b.dependency_audit(receipts,manifest)
summary={'checked_completed_units':len(receipts),'status':result['status'],'missing_dependency_files':result['missing_dependency_files'],'unbound_inputs':result['unbound_inputs']}
print(json.dumps(summary,indent=2))
