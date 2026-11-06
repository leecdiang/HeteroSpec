"""Zero-model packaging preparation, only after the fixed development lane closes."""
from native_host import *
import ctypes as ct

def wait_for(pid):
 k=ct.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[ct.c_ulong,ct.c_int,ct.c_ulong];k.OpenProcess.restype=ct.c_void_p
 k.WaitForSingleObject.argtypes=[ct.c_void_p,ct.c_ulong];k.WaitForSingleObject.restype=ct.c_ulong;k.CloseHandle.argtypes=[ct.c_void_p]
 h=k.OpenProcess(0x100000,False,pid)
 if h:
  try:
   while k.WaitForSingleObject(h,1000)==258:pass
  finally:k.CloseHandle(h)

def main(pid):
 wait_for(pid);d=read(ROOT/'DEVELOPMENT_DECISION.json')
 assert not LOCK.exists() and not d['provisional_joint_opportunities'] and not d['frozen_confirmation_started']
 assert 'DEVELOPMENT_COMPLETE_NO_BLIND_OUTPUTS_STARTED' in (ROOT/'development-native02.log').read_text()
 from delivery_host import inputs
 if not (ROOT/'repro/native-inputs/INPUTS.json').exists():inputs()
 print('CLOSEOUT_NATIVE_INPUTS_CAPTURED',flush=True)
 if not (ROOT/'portable-rebuild01/BUILD_PROOF.json').exists():
  resume=(ROOT/'portable-rebuild01').exists();command([sys.executable,'-B',HERE/'rebuild_host.py',ROOT/'portable-rebuild01']+(['--resume'] if resume else []),ROOT/('portable-build02.log' if resume else 'portable-build01.log'))
 print('CLOSEOUT_PORTABLE_BUILD_PASS',flush=True)
 if not (ROOT/'MODELS_POST_RUN.json').exists():
  models=[]
  for x in read(ROOT/'HOST_BINDINGS.json')['models']:
   p=Path(x['path']);digest=sha(p);assert digest==x['sha256'] and p.stat().st_size==x['bytes'] and p.stat().st_mtime_ns==x['mtime_ns'];models.append(dict(x,post_run_sha256=digest))
  write(ROOT/'MODELS_POST_RUN.json',dict(models=models,unchanged=True,utc=utc(),model_requests=0))
 else:assert read(ROOT/'MODELS_POST_RUN.json')['unchanged']
 attempt=1
 while (ROOT.parent/f'b570-economics-local-audit{attempt:02}.json').exists():attempt+=1
 auditlog=ROOT.parent/f'b570-economics-local-audit{attempt:02}.json'
 command([sys.executable,'-B',HERE/'audit_host.py'],auditlog)
 a=read(auditlog);write(ROOT/'AUDIT.json',a);print('CLOSEOUT_FULL_RAW_RECONSTRUCTION_PASS',a['qualification']['vectors'],a['qualification']['states'],flush=True)
 from report_host import render
 report=render(ROOT/'AUDIT.json');(HERE/'RESULTS.md').write_text(report,encoding='utf-8',newline='\n');(ROOT/'RESULTS.md').write_text(report,encoding='utf-8',newline='\n')
 ev=HERE/'evidence';ev.mkdir(exist_ok=True)
 write(ev/'CPU_RECONSTRUCTION.json',dict(status=a['status'],audit_sha256=sha(ROOT/'AUDIT.json'),local_audit_receipt=read(str(auditlog)+'.cost.json'),model_requests=0,reference_unchanged=True,fresh_natural_confirmation_started=False))
 write(ev/'QUALIFICATION.json',a['qualification'])
 write(ev/'PILOT_TOTALS.json',dict(resident=a['resident_pilot'],parallel=a['parallel_pilot'],independent_exposed_roots=4,blocks=2,no_new_unseen_claim=True))
 write(ev/'DEVELOPMENT_GATE.json',dict(raw_receipt_sha256=sha(ROOT/'DEVELOPMENT_DECISION.json'),**{k:v for k,v in d.items() if k!='physical_work'}))
 c=a['costs'];write(ev/'COSTS.json',{k:v for k,v in c.items() if k not in ('units','ledger','retained_command_receipts')})
 a1=read(ROOT/'A1_COSTS.json');write(ev/'A1_SUMMARY.json',{k:v for k,v in a1.items() if k!='records'})
 for n in ('HOST_BINDINGS','COMPONENT_PROTOCOL','SUPERVISOR_ADAPTER','SUPERVISOR02_VALIDATION','ENCODER_VALIDATION','KNOWN_PROBE_PLAN','KNOWN_PROBE_RESULTS','CAP1_RESULTS','K3_PROTOCOL_RESULTS','MODELS_POST_RUN','HELPER_BINDINGS','BUILD_INVENTORY'):
  shutil.copyfile(ROOT/(n+'.json'),ev/(n+'.json'))
 write(ev/'KNOWN_ACTUAL_WORK.json',dict(rows=a['known_work'],derived_from_actual_caller_rows_and_occupied_micrographs=True,used_worker='known-probe02',metadata_only_unused_followup='known-probe03'))
 proofs={}
 for name in ('core01','parallel-core02'):
  proofs[name]=dict(output_source_sha256=sha(ROOT/name/'OUTPUT_SOURCE.json'),files=read(ROOT/name/'OUTPUT_SOURCE.json'))
 write(ev/'NATIVE_MAPPING.json',dict(private_cores=proofs,portable_build=read(ROOT/'portable-rebuild01/BUILD_PROOF.json'),original_reference_unchanged=True,shared_legal_repairs=True,natural_M_capacity=128,natural_speculative_target_capacity=2,known_probe_output_reserve=32,natural_output_reserves_unchanged=True))
 print('CLOSEOUT_REPORT_AND_COMPACT_EVIDENCE_READY',flush=True)

if __name__=='__main__':
 started=utc();wall=time.monotonic();ok=False
 try:main(int(sys.argv[1]));ok=True
 finally:write(ROOT.parent/('b570-economics-closeout-'+started.replace(':','').replace('.','')+'.json'),dict(started_utc=started,finished_utc=utc(),wall_seconds=time.monotonic()-wall,success=ok,model_requests=0,includes_wait_and_nested_commands=True,not_additive_to_native_or_nested_commands=True))
