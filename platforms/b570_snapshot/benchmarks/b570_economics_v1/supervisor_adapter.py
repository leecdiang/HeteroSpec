"""Narrow PR187 supervisor environment adaptation; no containment changes."""
from native_host import *
from stage_costs import once

def prepare():
 base=PREVIOUS/'supervisor.py';assert sha(base)==read(ROOT/'HOST_BINDINGS.json')['supervisor_sha256']
 s=base.read_text();old="allowed={'HS_PREFILL_OUTPUT','HS_PREFILL_UB','HS_NO_TRANSFER','HS_TRACE_OFF','HS_MATCHED_TARGET','HS_SMOL_DRAFT_PATH'}"
 flags=['HS_ECON_MICROTRACE','HS_TRANSFER_TRACE','HS_PARALLEL_DISPATCH','HS_ECON_WHOLE']
 s=once(s,old,old[:-1]+','+','.join(repr(x) for x in flags)+'}')
 s=once(s,'        env.update(explicit)',"        check(all(explicit.get(k,'1')=='1' for k in "+repr(tuple(flags))+"),'Invalid economics switch value')\n        env.update(explicit)")
 out=ROOT/'supervisor02.py';assert not out.exists();out.write_text(s)
 write(ROOT/'SUPERVISOR_ADAPTER.json',dict(base_sha256=sha(base),adapted_sha256=sha(out),added_flags=flags,added_values=['1'],resource_job_and_cleanup_code_changed=False,original_reference_or_helper_files_changed=False))
 return out

def validate():
 sup=ROOT/'supervisor02.py';binding=read(ROOT/'SUPERVISOR_ADAPTER.json');assert sha(sup)==binding['adapted_sha256']
 proof=ROOT/'supervisor02-tests';proof.mkdir();exe=Path(sys.executable);manifest=proof/'FILES.json'
 write(manifest,dict(files=[dict(path=str(exe),bytes=exe.stat().st_size,sha256=sha(exe))]));rows=[]
 for mode in ('parent-failure','timeout','invalid-switch'):
  folder=proof/mode;folder.mkdir();child=folder/'child.json';env=folder/'ENV.json';write(env,dict(HS_ECON_MICROTRACE='0' if mode=='invalid-switch' else '1'))
  code="import subprocess,sys,time,json;p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']);open("+repr(str(child))+",'w').write(json.dumps({'pid':p.pid}));"+("sys.exit(2)" if mode=='parent-failure' else 'time.sleep(60)')
  args=[sys.executable,'-B',str(sup),'--manifest',str(manifest),'--receipt',str(folder/'SUPERVISOR.json'),'--process-limit','4','--limit','3','--minimum-free-bytes',str(20*1024**3),'--environment-file',str(env),str(exe),'-c',code]
  key='supervisor02-test-'+mode;ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(key,dict(requests=0,token_rows=0,operators=0));ledger.close();started=time.monotonic()
  with (folder/'host.log').open('x') as f:rc=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=30).returncode
  assert rc!=0
  if mode=='invalid-switch':
   assert not (folder/'SUPERVISOR.json').exists() and not child.exists() and 'Invalid economics switch value' in (folder/'host.log').read_text();row=dict(mode=mode,prelaunch_rejected=True,native_process_created=False)
  else:
   r=read(folder/'SUPERVISOR.json');assert r['assigned_before_resume'] and r['cleanup_verified'] and r['job_accounting']['active_processes']==0 and 2<=r['job_accounting']['total_processes']<=4 and child.exists();row=dict(mode=mode,cleanup_verified=True,accounting=r['job_accounting'],child_pid=read(child)['pid'])
  row.update(wall_seconds=time.monotonic()-started,expected_nonzero_exit=rc,model_requests=0);rows.append(row)
  ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.finish(key,'EXPECTED_FAILURE_VERIFIED',rc);ledger.close()
 write(ROOT/'SUPERVISOR02_VALIDATION.json',dict(status='NARROW_ENV_ADAPTER_AND_REAL_DESCENDANT_CLEANUP_PASS',cases=rows,adapted_sha256=sha(sup),model_requests=0))
 print('SUPERVISOR02_VALIDATED',flush=True)

if __name__=='__main__':prepare();validate()
