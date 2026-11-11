"""Preserve active core qualification; replace only idle remaining-gate jobs."""
from pathlib import Path
import argparse,json,os,signal,subprocess,sys,time
from build import read,sha,save
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args();r,w=a.root,a.work;src=Path(__file__).parent
 assert read(r/'q32-q4-full-operands-build-12/COMPLETE.json')['passed'];assert not(w/'closure-08').exists()and not(w/'qualification-08/CORE_GATES_COMPLETE.json').exists()
 save(w/'SOURCE15_ACTUAL_LAUNCH_BINDING.private.json',dict(epoch=time.time(),sources={p.name:sha(p)for p in src.glob('*.py')},main_build_sha256=sha(r/'q32-q4-full-build-10/COMPLETE.json'),offline_build_sha256=sha(r/'q32-q4-full-operands-build-12/COMPLETE.json'),reference_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),runtime_host_sha256=sha(w/'runtime-06/host.py'),main_native_ELF_changed=False,new_Q32_request_ceiling=640,formal_measurements=96,matched_warmups=96))
 # Preserve a consistent immutable ledger prefix; the authoritative original
 # ledger keeps growing and every previous reservation remains charged.
 prefix=w/'BUDGET_REGISTRATION_V2.ledger-prefix.jsonl'
 if(w/'BUDGET_REGISTRATION_V2.json').exists():
  registry=read(w/'BUDGET_REGISTRATION_V2.json');assert registry['new_request_ceiling']==640 and registry['R_freeze_sha256']==sha(w/'reference/REFERENCE_FREEZE.json')and registry['immutable_prior_ledger_prefix_sha256']==sha(prefix)
 else:
  while True:
   data=(w/'ledger.jsonl').read_bytes()
   try:
    assert data.endswith(b'\n');rows=[json.loads(x)for x in data.decode().splitlines()];break
   except (AssertionError,ValueError):time.sleep(.05)
  reserved=[x for x in rows if x['event']=='RESERVE'];inherited=read(w/'INHERITED_ACCOUNTING.json');prefix.write_bytes(data)
  save(w/'BUDGET_REGISTRATION_V2.json',dict(schema='heterospec.independent32B.pre-timing-budget.v2',epoch=time.time(),original_request_ceiling=512,new_request_ceiling=640,row_ceiling=2000000,at_registration_requests=inherited['requests']+sum(x['requests']for x in reserved),at_registration_reserved_rows=inherited['rows']+sum(x['rows']for x in reserved),immutable_prior_ledger_prefix_sha256=sha(prefix),R_freeze_sha256=sha(w/'reference/REFERENCE_FREEZE.json'),reason='User requested complete32B after earlier partial attempts; retain every failed/replaced preparation and full necessary reference branches, plus96 exact-root warmups and96 measured requests. Prospective registration before any formal measurement; no refunds or old8B budget borrowing',formal_measurements=96,matched_full_warmups=96,main_native_ELF_changed=False,old_8B_request_ceiling_unchanged=2048,old_8B_row_ceiling_unchanged=8000000,old_quota_markers_retained=True,new_worker_cutoff_UTC='2026-11-09T21:00:00Z',delivery_UTC='2026-11-10T00:00:00Z'))
 # These two processes are still idle. The scientific native worker and its
 # qualification parent continue without any signal or changed code.
 launched=read(w/'PIPELINE_LAUNCH_08.private.json')['processes'];retired=[]
 save(w/'FINISH_NOT_ADMITTED-08.json',dict(reason='Idle finisher replaced before any remaining-gate native admission: offline post-compute copy callback must return true to resume full graph. Fresh offline ELF and all full-model/remaining checks follow; core qualification and main native ELF unchanged',timing_admitted=False,epoch=time.time()))
 for name,needle in [('archive-08',b'q32-q4-full-source-13/archive.py'),('finish-08',b'q32-q4-full-source-13/finish.py')]:
  x=launched[name];p=Path(f"/proc/{x['pid']}");raw=(p/'stat').read_text();assert raw[raw.rfind(')')+2:].split()[19]==x['start_ticks'];assert needle in(p/'cmdline').read_bytes();assert not(w/'export-10').exists();os.kill(x['pid'],signal.SIGTERM);retired.append(dict(name=name,pid=x['pid'],idle=True))
 x=read(w/'DELIVERY_WAITER_LAUNCH08.private.json');p=Path(f"/proc/{x['pid']}")
 if p.exists():
  assert b'q32-q4-full-source-11/postprocess_delivery.py'in(p/'cmdline').read_bytes()and not(w/'delivery-01').exists();os.kill(x['pid'],signal.SIGTERM);retired.append(dict(name='idle-delivery-waiter08',pid=x['pid']))
 save(w/'REMAINING_HANDOFF.private.json',dict(epoch=time.time(),idle_processes_retired=retired,scientific_native_requests_interrupted=False,core_qualification_continues=True,unused_offline_build11_retained=True))
 while not(w/'PIPELINE_COORDINATOR_CLOSED08.private.json').exists():time.sleep(2)
 children={};launched={}
 for name,script,cpu,extra in [('finish-09','finish.py','32,33',['--builds',str(r/'q32-q4-full-build-10'),'--operand-builds',str(r/'q32-q4-full-operands-build-12')]),('archive-09','archive.py','34,35',[]),('delivery-waiter09','postprocess_delivery.py','34,35',['--epoch','09','--qualification-epoch','08','--closure-epoch','09','--request-ceiling','640','--export','export-11','--out','delivery-01'])]:
  with(w/(name+'.stdout.log')).open('xb')as so,(w/(name+'.stderr.log')).open('xb')as se:c=subprocess.Popen(['taskset','-c',cpu,'nice','-n','10',sys.executable,'-B',str(src/script),'--root',str(r),'--work',str(w),*extra],stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
  raw=Path(f'/proc/{c.pid}/stat').read_text();launched[name]=dict(pid=c.pid,start_ticks=raw[raw.rfind(')')+2:].split()[19],script=script,detached=True);children[name]=c
 save(w/'PIPELINE_LAUNCH_09.private.json',dict(epoch=time.time(),client_required=False,processes=launched,core_gates_from='qualification-08',all_six_required=True));print('Q32_REMAINING_GATES_CORRECT_OFFLINE_OBSERVER_LAUNCHED',flush=True)
 finish=children['finish-09']
 while finish.poll()is None:
  f=w/'PIPELINE_HEARTBEAT09.private.json';tmp=f.with_suffix('.tmp');tmp.write_text(json.dumps(dict(epoch=time.time(),finish_returncode=None),indent=2)+'\n');os.replace(tmp,f);time.sleep(5)
 complete=(w/'panel-01/COMPLETE.json').exists()or(w/'FINISH_NOT_ADMITTED-09.json').exists();failure=w/'closure-09/FAILURE.json'
 if not complete and not failure.exists():save(failure,dict(error='Remaining gate controller exited without successful terminal gate',returncode=finish.returncode,stderr_sha256=sha(w/'finish-09.stderr.log'),automatic_native_retry=False))
 save(w/'PIPELINE_COORDINATOR_CLOSED09.private.json',dict(epoch=time.time(),returncode=finish.returncode,no_more_native_admissions=True,core_gate_epoch='qualification-08'))
if __name__=='__main__':main()
