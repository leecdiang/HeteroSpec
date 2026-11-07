import os,sys,json,time,datetime,shutil,hashlib
from pathlib import Path
root=Path("C:/hs/b570-capability-v1/fb20a198-4dc2-457a-9310-20a48ed30600");begin=time.perf_counter_ns()
files=dirs=logical=allocation=0
for parent,ds,fs in os.walk(root,followlinks=False):
 dirs+=len(ds);allocation+=4096*len(ds)
 for name in fs:
  p=Path(parent,name);assert not p.is_symlink() and not p.is_junction()
  size=p.stat().st_size;logical+=size;allocation+=((size+4095)//4096)*4096+1024;files+=1
closing=json.loads((root/'CLOSING_STATE.json').read_bytes());acq=json.loads((root/'ACQUISITION.json').read_bytes())
receipt=json.loads((root/'processes/full-review-2/RECEIPT.json').read_bytes())
utc=datetime.datetime.now(datetime.timezone.utc);origin=datetime.datetime.fromisoformat(acq['first_preparation_utc'].replace('Z','+00:00'))
task=(utc-origin).total_seconds();delivery=(time.perf_counter_ns()-receipt['end_ns'])/1e9
free=shutil.disk_usage(root).free
charged=allocation+256*1024**2+64*1024**2
assert task<21600 and 0<=delivery<1800 and charged<1024**3 and free>=10*1024**3
record=dict(status='MEASURED_PREFIX_WITH_RESERVE',observed_utc=utc.isoformat(),begin_ns=begin,end_ns=time.perf_counter_ns(),task_wall_seconds=task,
 delivery_seconds_from_last_review_monotonic_end=delivery,development_stopped_seconds=4020.011,
 logical_bytes=logical,allocation_upper_bytes=allocation,files=files,directories=dirs,evidence_restore_reserve_bytes=256*1024**2,export_reserve_bytes=64*1024**2,
 charged_upper_bytes=charged,limit_bytes=1024**3,free_disk_bytes=free,
 actual_tool_request_count=sum(1 for p in (root/'tools').glob('*.intent.json'))+sum(1 for p in (root/'delivery/post_manifest/tools').glob('*.intent.json')),
 task_total_processes='UNKNOWN',task_total_lifetime_seconds='UNKNOWN',known_observed_prefix=dict(identities=834,actual_closed=834,lifetime_seconds=9423.0304473),
 scope='Real current file inventory and clocks; final subsequent API/delivery cost must be added, not zero; tool requests are not all OS processes')
with (root/'delivery/post_manifest/BUDGET_CLOSE.json').open('x',encoding='utf8',newline='\n') as f:json.dump(record,f,sort_keys=True,indent=2);f.write('\n')
print(json.dumps(record,sort_keys=True))
