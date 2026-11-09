"""Prospective whole-panel clock adjustment; same complete gates and native ELF.

Retires only the still-idle continuation coordinator, never core qualification
or a native request. Whole-panel conservative runtime+900s must fit before05:00;
latest whole-panel admission is03:30, with delivery still08:00.
"""
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 assert read(w/'BUDGET_REGISTRATION_V2.json')['new_request_ceiling']==640
 assert(w/'REMAINING_HANDOFF.private.json').exists()and not(w/'PIPELINE_LAUNCH_09.private.json').exists()and not(w/'closure-09').exists()and not(w/'qualification-08/CORE_GATES_COMPLETE.json').exists()
 x=read(w/'COORDINATOR15_LAUNCH.private.json');p=Path(f"/proc/{x['pid']}");assert b'q32-q4-full-source-15/coordinator.py'in(p/'cmdline').read_bytes();assert not(p/'task'/str(x['pid'])/'children').read_text().strip()
 save(w/'SCHEDULE_REGISTRATION_V2.json',dict(epoch=time.time(),before_any_formal_measurement=True,original_whole_panel_admission_UTC='2026-11-09T19:00:00Z',whole_panel_admission_UTC='2026-11-09T19:30:00Z',new_worker_start_boundary_UTC='2026-11-09T21:00:00Z',minimum_seconds_before_new_worker=960,delivery_UTC='2026-11-10T00:00:00Z',whole_panel_observed_runtime_plus_margin_required=True,whole_panel_margin_seconds=900,measured=96,matched_warmups=96,main_native_ELF_changed=False,reference_changed=False,reason='Prioritize complete eligibility and the unchanged full panel within user05:00/08:00 boundaries; conservative whole-panel runtime admission remains mandatory; no formal effect estimates observed'))
 save(w/'SOURCE16_ACTUAL_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.glob('*.py')},main_build_sha256=sha(r/'q32-q4-full-build-10/COMPLETE.json'),offline_build_sha256=sha(r/'q32-q4-full-operands-build-12/COMPLETE.json'),reference_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),runtime_host_sha256=sha(w/'runtime-06/host.py'),budget_registration_sha256=sha(w/'BUDGET_REGISTRATION_V2.json'),schedule_registration_sha256=sha(w/'SCHEDULE_REGISTRATION_V2.json')))
 os.kill(x['pid'],signal.SIGTERM);save(w/'IDLE_COORDINATOR15_RETIRED.private.json',dict(epoch=time.time(),pid=x['pid'],no_children_at_retirement=True,native_requests_interrupted=False))
 while not(w/'PIPELINE_COORDINATOR_CLOSED08.private.json').exists():time.sleep(2)
 children={};launched={}
 for name,script,cpu,extra in [('finish-09','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-10'),'--operand-builds',str(r/'q32-q4-full-operands-build-12')]),('archive-09','archive.py','34,35',[]),('delivery-waiter09','postprocess_delivery.py','34,35',['--epoch','09','--qualification-epoch','08','--closure-epoch','09','--request-ceiling','640','--export','export-11','--out','delivery-01'])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:c=subprocess.Popen(['taskset','-c',cpu,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{c.pid}/stat').read_text();launched[name]=dict(pid=c.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=c
 save(w/'PIPELINE_LAUNCH_09.private.json',dict(epoch=time.time(),client_required=False,processes=launched,core_gates_from='qualification-08',all_six_required=True));print('Q32_REMAINING_GATES_AND_CONDITIONAL_FULL_PANEL_LAUNCHED',flush=True)
 finish=children['finish-09']
 while finish.poll()is None:
  f=w/'PIPELINE_HEARTBEAT09.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),finish_returncode=None),indent=2)+'\n');os.replace(tmp,f);time.sleep(5)
 complete=(w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-09.json').exists();failure=w/'closure-09/FAILURE.json'
 if not complete and not failure.exists():save(failure,dict(error='Remaining gate controller exited without successful terminal gate',returncode=finish.returncode,stderr_sha256=sha(w/'finish-09.stderr.log'),automatic_native_retry=False))
 save(w/'PIPELINE_COORDINATOR_CLOSED09.private.json',dict(epoch=time.time(),returncode=finish.returncode,no_more_native_admissions=True,core_gate_epoch='qualification-08'))
if __name__=='__main__':main()
