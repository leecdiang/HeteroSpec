"""Commit offline delivery changes only after the last inference stage ends."""
from pathlib import Path
import json,time,subprocess,hashlib
from datetime import datetime,timezone
import runner
ROOT=Path(__file__).parent
cpu_stages={'independent_verify.py','audit_assets.py','generate_report.py','seal_archive.py','publish_evidence.py'}
while True:
 status=json.loads((ROOT/'PIPELINE_STATUS.json').read_text(encoding='utf-8-sig'))
 ended=runner.identity(9664)!='134357288660194883'
 if not (ROOT/'LOCK.json').exists() and (status.get('script') in cpu_stages or ended):break
 time.sleep(2)
freeze=json.loads((ROOT/'EXECUTION_FREEZE.json').read_text(encoding='utf-8-sig'))
proto=json.loads((ROOT/'PROTOCOL.json').read_text(encoding='utf-8-sig'))
for name,h in proto['sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
files=['independent_verify.py','generate_report.py','publish_evidence.py','commit_cpu_delivery_when_done.py','recovery/CPU_DELIVERY_PATCH_BEFORE.json','recovery/CPU_DELIVERY_PATCH_AMENDMENT.json']
subprocess.run(['git','add',*files],cwd=ROOT,check=True)
subprocess.run(['git','commit','-m','Record offline strong-baseline costs and public frontend sources after inference'],cwd=ROOT,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(ROOT/'recovery/CPU_DELIVERY_COMMIT.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),source_commit=head,inference_freeze_commit=freeze['source_commit'],numerical_and_executor_sources_unchanged=True,additional_model_requests=0),indent=2)+'\n',encoding='utf-8',newline='\n')
