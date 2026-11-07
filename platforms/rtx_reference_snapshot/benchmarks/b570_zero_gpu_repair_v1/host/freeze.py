"""Prospective freeze only after a completed final implementation review."""
import argparse,hashlib,sys
from pathlib import Path
from common import BASE,DESIGN,HERE,load,write_new,sha,need,now
P=argparse.ArgumentParser();P.add_argument('--revision',type=int,required=True);P.add_argument('--review-commit',required=True);a=P.parse_args()
review=load(DESIGN/'results/REVIEW_STATUS.json');need(review['status']=='FINAL_IMPLEMENTATION_REVIEW_PASS','no final clean implementation review')
files={p.relative_to(DESIGN).as_posix():sha(p) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
files.update({n:sha(DESIGN/n) for n in ('ACCEPTANCE.json','BUDGET.json','PROTOCOL.md','EVIDENCE.md','SOURCE_LOCK.json','check_receipts.py')})
need(all(review['covered_files'].get(k)==v for k,v in files.items()),'review does not cover final implementation')
need(sha(BASE/'task/task_ledger.py')==sha(HERE/'outer_task_ledger.py'),'executed outer broker differs from reviewed source')
obj=dict(schema=1,scope='PR117 CPU-only confirmation; no PR115 or scientific authorization',design_commit='8b8c78f8fc63195369e276c83216075b8475a352',review_commit=a.review_commit,final_development_revision=a.revision,registered_ns=now(),bound_files=files,review_status_sha256=sha(DESIGN/'results/REVIEW_STATUS.json'),environment=load(DESIGN/'results/ENVIRONMENT.json'),budget=load(DESIGN/'BUDGET.json'),rounds=[dict(round=r,id='confirm-'+str(r),order=o,cases=19,transition_pairs=8) for r,o in enumerate(('listed','reversed','sha256_case_id'))],task_root=str(BASE),external_logs='runs/<registered round>/external/launcher',forbidden_counts=load(DESIGN/'BUDGET.json')['forbidden_counts'],no_confirmation_retries=True)
cpu_paths=[sys.executable,str(Path(sys.executable).parent/'python312.dll'),'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','C:/Windows/Microsoft.NET/Framework64/v4.0.30319/csc.exe','C:/hs/pr108-tools/git/cmd/git.exe','C:/Users/DIANG/AppData/Local/OpenAI/Codex/bin/9614f1d9b40d9c4f/codex.exe']
obj['external_cpu_files']=[dict(path=p,bytes=Path(p).stat().st_size,sha256=sha(p)) for p in cpu_paths]
write_new(DESIGN/'results/CONFIRMATION_FREEZE.json',obj);print(sha(DESIGN/'results/CONFIRMATION_FREEZE.json'))
