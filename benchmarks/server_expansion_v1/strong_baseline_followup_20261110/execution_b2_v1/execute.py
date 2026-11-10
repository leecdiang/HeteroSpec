"""Bounded B2 scheduler for the unchanged original 8B native implementations.

Separate admission, ledger and full public readback are mandatory. Legacy
operation_s remains the native endpoint: external marker spans are not relabeled
as that endpoint, and missing native absolute timestamps are never invented.
"""
import argparse
from collections import defaultdict
from contextlib import ExitStack
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback


def need(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024**2),b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as f:
        json.dump(value,f,indent=2,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def state(path, value):
    path=Path(path);temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');os.replace(temporary,path)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def epoch(value):
    x=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    need(x.tzinfo is not None,'Explicit allocation timezone')
    return x.timestamp()


def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def verify_files(files):
    for path,digest in files.items():
        need(sha(path)==digest,'Frozen B2 file changed: '+path)


def public_readback(proof):
    need(proof['status']=='COMPLETE_FILE_BYTES_MATCHED' and proof['anonymous'] is True,
         'Full anonymous B2 public byte readback required')
    need(len(proof['commit'])==40 and proof['files'],'Immutable complete B2 public index')
    for item in proof['files']:
        need(item['url'].startswith('https://raw.githubusercontent.com/leecdiang/HeteroSpec/'+proof['commit']+'/'),
             'B2 immutable URL binding')
        need(sha(item['source_file'])==item['sha256']==sha(item['downloaded_file']) and
             Path(item['downloaded_file']).stat().st_size==item['bytes'],'B2 readback bytes changed')


def analyze(records, plan):
    need(len(records)==16,'Partial B2 has no complete-panel estimate')
    contrasts=[]
    for core,pos in plan['cells']:
        processes=[]
        for record in records:
            worker=record['worker']
            if (worker['core'],worker['boundary'])!=(core,pos):
                continue
            totals=defaultdict(float)
            for item in record['operations']:
                if item['role']=='measured':
                    x=item['receipt']['operation_s']
                    need(type(x) in (int,float) and math.isfinite(x) and x>0,'Finite native operation time')
                    totals[item['item']['execution']]+=x
            ratio=totals['q8']/totals['q4pair']
            processes.append(dict(worker=worker['id'],round=worker['round'],ratio_B_over_A=ratio,
                                  measured_totals_s=dict(totals),complete_caller_s=record['caller_s']))
        need(len(processes)==4 and {x['round'] for x in processes}==set(range(4)),'Four original process clusters per cell')
        ratios=[x['ratio_B_over_A'] for x in processes]
        contrasts.append(dict(core=core,boundary=pos,processes=processes,
                              geometric_B_over_A=math.exp(sum(math.log(x) for x in ratios)/4),
                              minimum=min(ratios),maximum=max(ratios)))
    return dict(complete=True,descriptive_only=True,warmups=64,measurements=64,workers=16,
                independent_processes_per_cell=4,contrasts=contrasts,
                native_endpoint='Original unmodified B operation_s; restore/startup separately recorded',
                absolute_native_timestamps='Not recorded by the unchanged legacy ELF; no fabricated ns endpoints',
                external_endpoint='Actual host launch/result markers; includes disk/restore/hash/serialization between results',
                limitations=['One exposed root, two boundaries and two projections',
                             'Two equal warm operations per path do not prove general steady state',
                             'Four clusters per cell; no independent-operation inference or live-k7 speed claim'])


def run(configuration):
    need(sys.flags.optimize==0,'Run the unchanged original checker with assertions enabled')
    c=read(configuration);w=Path(c['work_root']);root=Path(c['study_root'])
    need(c['schema']=='hs.B2.host-admission.v1' and c['GPU_authorized'] is True,'Explicit current B2 admission')
    need(c['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'Reboot requires new audit')
    need(read(w/'CPU_REUSE_COMPLETE.json')['original_32_cells_recomputed'] is True,'Complete saved numerical reuse first')
    public_readback(c['public_readback']);verify_files(c['source_files']);verify_files(c['frozen_files'])
    core=read(c['admission_core']);need(sha(c['admission_core'])==c['admission_core_sha256'],'B2 admission core changed')
    need(all(c.get(key)==value for key,value in core.items()),'Actual admission differs from frozen complete core')
    public_core=Path(c['public_core']);registered={x['source_file']:x['sha256']for x in c['public_readback']['files']}
    need(registered.get(str(public_core))==sha(public_core),'Complete B2 admission was not publicly read back')
    public_text=Path(c['admission_core']).read_text().replace(str(root),'${HS_ROOT}').replace(str(Path.home()),'${HOST_HOME}')
    need(public_core.read_text()==public_text,'B2 public admission transform differs')
    delivery=read(c['main_delivery_proof'])
    need(sha(c['main_delivery_proof'])==c['main_delivery_proof_sha256'] and
         delivery['statistical_replay']=='PASSED_COMPLETE_72_OPERATIONS',
         'Complete current32B public statistical/byte delivery before B2')
    need(not(w/'ledger.jsonl').exists(),'Existing B2 journal: audit before any launch')
    need(not(w/'STATE.json').exists(),'Never restart a B2 execution epoch')
    plan=read(w/'PLAN.json');need(len(plan['workers'])==16 and plan['total_requests']==128,'Fixed full B2 panel')
    need(time.time()+c['whole_panel_bound_s']+c['archive_bound_s']+900<=epoch(c['allocation_end_utc']),
         'Complete B2 and closure must fit')
    sys.path.insert(0,c['runtime']);host=module('_new_B2_host',Path(c['runtime'])/'host.py')
    old=module('_original_B_checker',root/'pr210-stage-b-source-05/run.py')
    checker=old.Runner.__new__(old.Runner);checker.oracles={0:Path(plan['reuse']['oracle'])}
    guard=None;records=[];began=time.monotonic()
    with ExitStack() as stack:
        for path in (w/'lifecycle.lock',root/'STUDY_SCHEDULING.lock',root/'strong-baseline-followup-20261110/activity.lock'):
            lock=stack.enter_context(path.open('a+'));fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        save(w/'LOCK_ACQUIRED.private.json',dict(pid=os.getpid(),utc=utc()))
        try:
            with (w/'guard.stdout.log').open('xb') as so,(w/'guard.stderr.log').open('xb') as se:
                guard=subprocess.Popen([c['native_parent_guard'],'--parent',str(os.getpid()),'--',
                    'taskset','-c','36',sys.executable,'-B',c['guard_script'],'--work',str(w)],
                    stdin=subprocess.DEVNULL,stdout=so,stderr=se,start_new_session=True)
            for _ in range(40):
                if (w/'RESOURCE_GUARD_LATEST.private.json').exists():
                    break
                need(guard.poll() is None,'Resource guard failed');time.sleep(.5)
            for worker in plan['workers']:
                state(w/'STATE.json',dict(status='B2_RUNNING',worker=worker['id'],completed_workers=len(records),utc=utc()))
                need(not(w/'STOP_REQUESTED').exists() and not(w/'PAUSE.json').exists(),'Requested/resource stop')
                need(time.time()<=epoch(c['last_new_worker_utc']) and epoch(c['allocation_end_utc'])-time.time()>=960,
                     'No remaining B2 worker window')
                verify_files(c['source_files']);verify_files(c['frozen_files'])
                observed=read(w/'RESOURCE_GUARD_LATEST.private.json')
                need(time.time()-observed['epoch']<20 and not observed['events'],'Resource observation unavailable/conflict')
                path=w/worker['job'];need(sha(path)==worker['job_sha256'],'Fixed B2 job changed')
                job=read(path);build=plan['reuse']['builds'][worker['core']]
                output=w/'runs'/worker['id'];start=time.monotonic()
                host.run(Path(c['allocation_file']),Path(build['path']),path,output,'development')
                caller=time.monotonic()-start
                need(read(output/'LOADED_MODULES.json')==build['loaded_modules'],'Actual B2 modules differ from original qualification')
                native=read(output/'native/result.json')
                need(native['context']==build['context'] and native['draft_calls']==0,'Actual original context/residency')
                clocks=read(output/'CLOCKS.json')['markers']
                need([x['name'] for x in clocks]==[x['name'] for x in job['diagnostics']],'All ordered warm/measurement markers')
                operations=[]
                for item,clock in zip(job['diagnostics'],clocks):
                    proof=old.Runner.check(checker,output/'native',item,worker['core'],False)
                    receipt_path=output/'native'/item['name']/'receipt.json';receipt=read(receipt_path)
                    need(not receipt['capture'],'Heavy observer entered B2 timing')
                    operations.append(dict(role='warm' if item['name'].startswith('warm-') else 'measured',
                                           item=item,proof=proof,receipt=receipt,receipt_sha256=sha(receipt_path),
                                           actual_host_marker=clock))
                record=dict(worker=worker,caller_s=caller,HOST=read(output/'HOST.json'),
                            CLOCKS=read(output/'CLOCKS.json'),operations=operations)
                save(w/'checked'/(worker['id']+'.json'),record);records.append(record)
            result=analyze(records,plan);save(w/'RESULTS.json',result)
            save(w/'COMPLETE.json',dict(passed=True,requests=128,rows=33024,workers=16,utc=utc()))
            state(w/'STATE.json',dict(status='B2_COMPLETE_REQUIRES_PUBLIC_ARCHIVE_REPLAY',caller_s=time.monotonic()-began,utc=utc()))
        except BaseException as error:
            state(w/'STATE.json',dict(status='B2_PARTIAL_STOPPED',reason=str(error),completed_workers=len(records),
                                     caller_s=time.monotonic()-began,utc=utc(),no_automatic_native_retry=True))
            save(w/'FAILURE.json',dict(reason=str(error),traceback=traceback.format_exc()));raise
        finally:
            (w/'GUARD_DONE').touch(exist_ok=False)
            if guard:
                try:guard.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    guard.terminate();guard.wait(timeout=10)
            save(w/'LOCK_RELEASED.private.json',dict(pid=os.getpid(),utc=utc()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--configuration',type=Path,required=True)
    a=p.parse_args();run(a.configuration)
