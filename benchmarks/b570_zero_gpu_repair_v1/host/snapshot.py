"""Immutable audit-input snapshot, cut at an already completed broker command."""
import argparse,hashlib,json,os
from pathlib import Path
from common import BASE,DESIGN,write_new,sha
p=argparse.ArgumentParser();p.add_argument('--id',required=True);a=p.parse_args()
folder=BASE/'task/snapshots'/a.id;folder.mkdir(parents=True,exist_ok=False)
parts=[BASE/'task/PROCESS_LEDGER.jsonl']
if (BASE/'task/PROCESS_LEDGER_v2.jsonl').exists():parts.append(BASE/'task/PROCESS_LEDGER_v2.jsonl')
lines=[]
for part in parts:lines.extend(part.read_bytes().splitlines(keepends=True))
ends=[i for i,line in enumerate(lines) if json.loads(line)['kind']=='COMMAND_END'];assert ends
(folder/'LEDGER.jsonl').write_bytes(b''.join(lines[:ends[-1]+1]))
paths=[]
for sub in ('runs','e0','sources','frozen_remote','queue','queue-v2'):
    if (BASE/sub).exists():paths.extend(p for p in (BASE/sub).rglob('*') if p.is_file())
paths.extend(p for p in (DESIGN/'host').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
paths.extend(p for p in DESIGN.iterdir() if p.is_file() and p.suffix in ('.py','.json','.md') and p.name not in ('IMPLEMENTATION_STATUS.md',))
for name in ('DESIGN_DECISION.md','DEVELOPMENT_REGISTRY.jsonl','SOURCE_VERIFICATION.json','ENVIRONMENT.json','CONFIRMATION_FREEZE.json','REMOTE_FREEZE.json','REVIEW_STATUS.json','ROUND_0_GATE.json','ROUND_1_GATE.json','ROUND_2_GATE.json'):
    q=DESIGN/'results'/name
    if q.is_file():paths.append(q)
active_ids={json.loads(s)['request']['id'] for s in lines if json.loads(s)['kind']=='COMMAND_BEGIN'}-{json.loads(s)['request_id'] for s in lines if json.loads(s)['kind']=='COMMAND_END'}
for q in (BASE/'task').glob('*'):
    if not q.is_file() or q.name.startswith('PROCESS_LEDGER') or any(q.name.startswith(i+'.') for i in active_ids):continue
    if q.suffix in ('.log','.json','.py','.ps1','.txt','.md'):paths.append(q)
for q in (DESIGN/'results').glob('*.json'):
    if q.name not in ('RAW_AUDIT.json','RAW_MANIFEST.json','BUDGET_ACTUAL.json','REMOTE_RESTORE.json','ARCHIVE.json'):paths.append(q)
paths.append(folder/'LEDGER.jsonl')
manifest=dict(schema=1,ledger_prefix_boundary='last completed COMMAND_END before snapshot command; future audit/delivery tail explicitly excluded',members=[dict(path=q.relative_to(BASE).as_posix(),bytes=q.stat().st_size,sha256=sha(q)) for q in sorted(set(paths))])
write_new(folder/'INPUT_MANIFEST.json',manifest)
print(json.dumps(dict(manifest=str((folder/'INPUT_MANIFEST.json').relative_to(BASE)),ledger=str((folder/'LEDGER.jsonl').relative_to(BASE)),members=len(manifest['members']))))
