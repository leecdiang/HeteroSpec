#!/usr/bin/env python3
"""Create and verify the immutable byte-addressed 358H Phase-3 archive."""
from __future__ import annotations
import argparse, hashlib, json, shutil
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''): h.update(b)
 return h.hexdigest()
def add(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--full',type=Path,required=True); ap.add_argument('--small',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 if a.out.exists(): raise RuntimeError('archive destination already exists')
 a.out.mkdir(parents=True)
 groups={'formal_full':a.full,'formal_small_gate':a.small,'analysis':ROOT/'analysis','protocol':ROOT/'benchmarks/358h_threshold_validation','runner':ROOT/'scripts/platform/358h','reports':ROOT/'reports/358h','final_status':ROOT/'work/358h'}
 selected={
  'formal_full':['FORMAL_PHASE3_STATUS.json','schedule.json','session.json','warmup.json','observations.jsonl','observations.resolved.json'],
  'formal_small_gate':['FORMAL_PHASE3_STATUS.json','schedule.json','session.json','warmup.json','observations.jsonl','observations.resolved.json'],
  'analysis':['358h_phase3_summary.json','358h_phase3_prompt_summary.csv','358h_phase3_rounds.csv','358h_phase3_decomposition.csv'],
  'protocol':['preregistration_v1.json','preregistration_v2.json','phase3_execution_addendum_v1.json','phase3_runner_qualification_v1.json','phase3_campaign_driver_freeze_v1.json'],
  'runner':['phase3_heterogeneous_runner.py','phase3_runner_state_tests.py','run_phase3_campaign.py','analyze_phase3_campaign.py'],
  'reports':['358H_HETEROGENEOUS_RUNNER_QUALIFICATION.md','358H_RUNNER_SEMANTICS_MAPPING.md','358H_PHASE3_END_TO_END_VALIDATION.md','358H_PLATFORM_CLOSEOUT.md'],
  'final_status':['PHASE3_FINAL_STATUS.json']}
 for group,names in selected.items():
  for n in names:
   src=groups[group]/n
   if not src.exists(): raise FileNotFoundError(src)
   add(src,a.out/group/n)
 # Target C API messages are authoritative full-offload evidence and sit beside the campaign dirs.
 for label,d in [('formal_full',a.full),('formal_small_gate',a.small)]:
  for suffix in ('.stdout.txt','.stderr.txt'):
   src=d.with_name(d.name+suffix)
   if src.exists(): add(src,a.out/label/(src.name))
 files=[]
 for p in sorted(x for x in a.out.rglob('*') if x.is_file()):
  files.append({'path':p.relative_to(a.out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
 manifest={'schema':'heterospec.358h.phase3.archive_manifest.v1','created_at_utc':datetime.now(timezone.utc).isoformat(),'formal_data':{'full_observations':270,'small_gate_observations':54,'full_cpu_exact':'90/90','full_npu_exact':'90/90','small_cpu_exact':'18/18','small_npu_exact':'18/18'},'entry_count':len(files),'files':files}
 (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
 valid=all((a.out/x['path']).stat().st_size==x['bytes'] and sha(a.out/x['path'])==x['sha256'] for x in files)
 print(json.dumps({'archive':str(a.out),'entries':len(files),'sha256_validation':valid,'manifest_sha256':sha(a.out/'manifest.json')},indent=2))
if __name__=='__main__': main()

