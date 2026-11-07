#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
ROOTS=[
 'benchmarks/358h_threshold_validation/preregistration_v1.json',
 'benchmarks/358h_threshold_validation/protocol_addendum_v1.json',
 'benchmarks/358h_threshold_validation/protocol_addendum_v1_implementation_erratum_1.json',
 'benchmarks/358h_threshold_validation/protocol_addendum_v1_implementation_erratum_2.json',
 'benchmarks/358h_threshold_validation/protocol_addendum_v1_implementation_erratum_3.json',
 'benchmarks/358h_threshold_validation/protocol_addendum_v1_implementation_erratum_4.json',
 'runs/358h/preformal_manifest.json','runs/358h/preformal_addendum_manifest.json',
 'runs/358h/preformal_addendum_erratum_1_manifest.json','runs/358h/preformal_addendum_erratum_2_manifest.json',
 'runs/358h/preformal_addendum_erratum_3_manifest.json','runs/358h/preformal_addendum_erratum_4_manifest.json',
 'runs/358h/preflight_after_addendum_20260918T0830.json',
 'runs/358h/phase1/358h-p1-cpu-20260918T082639-63294459',
 'runs/358h/phase1/358h-p1-npu-20260918T082821-e1471810',
 'runs/358h/phase1/358h-p1-energy-cpu-20260918T082952',
 'runs/358h/phase2/358h-exactness-20260918T083359','runs/358h/phase2/358h-exactness-20260918T091353',
 'runs/358h/phase2/358h-exactness-20260918T092303','runs/358h/phase2/358h-exactness-20260918T092509',
 'runs/358h/phase2/358h-exactness-20260918T092722',
 'runs/358h/phase2/358h-tb-20260918T094615','runs/358h/phase2/358h-v2-20260918T104308',
 'analysis/358h_draft_device_summary.json','analysis/358h_draft_device_summary.csv',
 'analysis/358h_threshold_input_cpu.json','analysis/358h_threshold_input_npu.json',
 'analysis/358h_threshold_gate_cpu.json','analysis/358h_threshold_gate_npu.json','analysis/358h_threshold_summary.json',
 'reports/358h/358H_DRAFT_DEVICE_CHARACTERIZATION.md','reports/358h/358H_DRAFT_THRESHOLD_ANALYSIS.md',
 'scripts/platform/358h/run_phase1_draft_characterization.py','scripts/platform/358h/run_cpu_energy_track.py',
 'scripts/platform/358h/run_exactness_gate.py','scripts/platform/358h/run_target_tb_v2.py',
 'scripts/platform/358h/process_phase1_phase2_results.py','scripts/platform/358h/threshold_gate_v2.py']
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
files=[]
for rel in ROOTS:
 p=ROOT/rel
 if not p.exists(): raise FileNotFoundError(rel)
 paths=sorted(x for x in p.rglob('*') if x.is_file()) if p.is_dir() else [p]
 for x in paths: files.append({'path':x.relative_to(ROOT).as_posix(),'bytes':x.stat().st_size,'sha256':sha(x)})
payload={'schema':'heterospec.358h.campaign_manifest.v1','created_at':datetime.now(timezone.utc).astimezone().isoformat(),
 'original_freeze_commit':'6cdb84fe7962c1871136fc316fd6d12e40b99271','blocked_preflight_commit':'314ba642be75dce5986044d1a827d1fcd9a5108b',
 'addendum_freeze_commit':'82dcbc26150f1f56c40b4a839ff0c5d032087be8','latest_implementation_erratum_commit':'fff34471eb9f2593c8ef3af1c2ef3ed91eda8d55',
 'formal_runs_expected':30,'formal_runs_completed':30,'cpu_energy_windows_completed':15,'exactness_pairs':'18/18 PASS',
 'tb_contexts_completed':[512,2048,8192],'v2_contexts_completed':[512,2048,8192],
 'phase2':{'CPU':'BORDERLINE','NPU':'BORDERLINE'},'phase3_started':False,
 'exclusions':['Four preserved exactness attempts are inadmissible implementation failures and supply zero valid pairs/timings.'],
 'deviations':['Implementation-only errata 1-4; no frozen scientific parameter or classification rule changed.'],
 'formal_contamination':'NONE; failed outputs are preserved and excluded before pair admission','artifact_count':len(files),'artifacts':files}
out=ROOT/'runs/358h/358h_campaign_manifest.json';out.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
check=all((ROOT/a['path']).stat().st_size==a['bytes'] and sha(ROOT/a['path'])==a['sha256'] for a in files)
print(json.dumps({'path':str(out),'artifact_count':len(files),'sha256_validation':check,'manifest_sha256':sha(out)},indent=2))

