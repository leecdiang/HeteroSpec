"""Commit offline metadata only after the authorized numerical continuation ends."""
from pathlib import Path
import json,time,hashlib,subprocess
from datetime import datetime,timezone
import runner
ROOT=Path(__file__).parent
owner=json.loads((ROOT/'PIPELINE_LOCK.json').read_text(encoding='utf-8-sig'))
cpu={'independent_verify.py','audit_assets.py','generate_report.py','seal_archive.py','publish_evidence.py'}
while True:
 status=json.loads((ROOT/'PIPELINE_STATUS.json').read_text(encoding='utf-8-sig'))
 if not (ROOT/'LOCK.json').exists() and (status.get('script') in cpu or runner.identity(owner['pid'])!=owner['creation_identity']):break
 time.sleep(2)
freeze=json.loads((ROOT/'CONTINUATION_FREEZE.json').read_text(encoding='utf-8-sig'))
for name,h in freeze['current_sources'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,name
files=['CONTINUATION_FREEZE.json','G0_CONTINUATION_QUAL.json','G0_CONTINUATION_QUAL_SCHEDULE.json','commit_continuation_when_done.py','CONTINUATION_CPU_SOURCES_AT_FREEZE.json','OFFLINE_VERIFIER_CONTINUATION_AMENDMENT.json','PAUSE_RESUME_AMENDMENT.json','CPU_PAYLOAD_RECOVERY_PAUSE.json','PAUSE.json','independent_verify.py','generate_report.py','publish_evidence.py']
files=[n for n in files if (ROOT/n).exists()]
subprocess.run(['git','add',*files],cwd=ROOT,check=True)
if subprocess.run(['git','diff','--cached','--quiet'],cwd=ROOT).returncode:subprocess.run(['git','commit','-m','Seal authorized continuation metadata after numerical stages'],cwd=ROOT,check=True)
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
(ROOT/'recovery/CONTINUATION_CPU_COMMIT.json').write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),source_commit=head,inference_freeze_commit=freeze['source_commit'],numerical_and_executor_sources_unchanged=True,additional_model_requests=0),indent=2)+'\n',encoding='utf-8',newline='\n')
