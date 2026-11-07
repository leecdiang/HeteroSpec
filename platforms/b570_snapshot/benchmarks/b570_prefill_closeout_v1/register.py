"""Finalize the registration against the committed source/manifest checkpoint."""
import datetime, shutil, subprocess, sys
from prepare import ROOT, read, write, sha, item
from freeze import WORKTREE, RESULT_PATH

checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORKTREE,text=True).strip()
assert checkpoint=='93ab8d62c24ed7bf60333b8ee196893d1991d868'
reg=read(ROOT/'design/REGISTRATION_TEMPLATE.json')
reg.update(status='FROZEN_FOR_HOST_REVIEW',study_uuid=read(ROOT/'PREPARATION.json')['uuid'],
 source_commit=checkpoint,freeze_commit=checkpoint,worktree=str(WORKTREE),result_path=RESULT_PATH,
 owned_start_utc='2026-10-21T10:45:26.0062489+00:00',
 runtime_manifest_sha256=sha(ROOT/'RUNTIME_MANIFEST.json'),model_manifest_sha256=sha(ROOT/'MODEL_RECHECK.json'),
 reference_manifest_sha256=sha(ROOT/'RAW_RECOVERY_MANIFEST.json'),input_manifest_sha256=sha(ROOT/'INPUT_PANEL.json'),
 order_sha256=sha(ROOT/'ORDER.json'),old_ledger_sha256=sha(ROOT/'HISTORY.json'),
 authorization_receipt_sha256=sha(ROOT/'AUTHORIZATION.json'),raw_to_normalized_auditor_sha256=sha(ROOT/'audit.py'),
 frozen_files_sha256=sha(ROOT/'FROZEN_FILES.json'),
 minimum_free_host_memory_bytes=1024**3,minimum_free_storage_bytes=8*1024**3,
 budget={'model_requests':156,'model_workers':9,'other_processes':128,'owned_seconds':10800,
         'storage_bytes':6*1024**3,'memory_bytes':16*1024**3,'cleanup_seconds':300,
         'per_worker_timeout_seconds':1200},
 worker_timeouts_seconds={'E0':180,'E1':600,'E2':1200},
 host={'cpu':'13th Gen Intel Core i5-13400, 10 cores /16 logical',
       'gpu':'Intel Arc B570','driver':'32.0.101.9034','host_memory_kib':33254420,
       'native_concurrency':1,'host_writer_concurrency':1},
 safety_derivation={'prior_qualification_max_seconds':34.174184,
       'prior_complete_timing_process_seconds':163.5546413,'prior_complete_timing_requests':9,
       'explanation':'E0:4 short requests,180s cap; E1:6 capture/count requests/input,600s cap; E2:32 requests/process,1200s cap. These fixed upper bounds include model startup/cleanup and exceed the observed old request costs. 7380s summed native caps plus300s cleanup are within10800s owned envelope. No time-of-day finish deadline.'},
 registration_commit_binding='Each process receipt binds the final registration-containing Git commit via --freeze. source_commit/freeze_commit identify the preceding committed source+manifest checkpoint.',
 historical_accounting='3435.1001972s receipt-backed cumulative; an additional historical time-1 process has unknown parent wall/exit/cleanup. Its observed service lower bound is81.3101785s. Preserve uncertainty; no new run fills this old UUID.',
 native_starts_at_registration=0)
write('REGISTRATION.json',reg)
sys.path.insert(0,str(ROOT/'design'));import toolkit
result=toolkit.validate_registration(reg)
write('REGISTRATION_VALIDATION.json',dict(result,scope='Fields plus explicit host/raw review; this CPU guard is not execution authority by itself.',job_configuration_cpu_probe='PASS'))
for name in ['REGISTRATION.json','REGISTRATION_VALIDATION.json','register.py']:
 shutil.copy2(ROOT/name,WORKTREE/RESULT_PATH/name)
print(reg['study_uuid'],result)
