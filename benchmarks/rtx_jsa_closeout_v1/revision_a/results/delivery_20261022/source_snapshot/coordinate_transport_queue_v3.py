"""Bounded, recoverable scheduling of only the owned evidence upload processes."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

WORK=Path(__file__).parent
sys.path.insert(0,str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')
LEASE=FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json'


def identity(pid,created,filename):
    process=psutil.Process(pid)
    assert abs(process.create_time()-created)<0.01
    assert any(Path(arg).name==filename for arg in process.cmdline())
    return process


def alive(pid,created):
    try:return abs(psutil.Process(pid).create_time()-created)<0.01
    except psutil.NoSuchProcess:return False


def resume(lease,reason):
    identity(lease['main_pid'],lease['main_created'],'resume_remote_evidence_v2.py').resume()
    lease.update({'status':'RESUMED','resumed_utc':d.now(),'resume_reason':reason})
    d.save(LEASE,lease)
    print('PRIMARY_DELIVERY_SCHEDULER_RESUMED',flush=True)


def stop_auxiliaries(lease):
    (FOLDER/'STOP_SUPPLEMENT').write_text('Bounded queue recovery; delivery only\n')
    if lease.get('parallel_pid') and alive(lease['parallel_pid'],lease['parallel_created']):
        parallel=identity(lease['parallel_pid'],lease['parallel_created'],'parallel_remaining_delivery_v3.py')
        for child in parallel.children(recursive=True):
            if child.name().lower()=='curl.exe':child.kill()
    end=time.monotonic()+180
    while time.monotonic()<end:
        if Path(lease['supplement_final']).exists() and (FOLDER/'PARALLEL_TRANSPORT_FINAL.json').exists():return
        time.sleep(2)
    for prefix,filename in [('parallel','parallel_remaining_delivery_v3.py'),('supplement','supplement_remote_delivery_v2.py')]:
        if lease.get(prefix+'_pid') and alive(lease[prefix+'_pid'],lease[prefix+'_created']):
            process=identity(lease[prefix+'_pid'],lease[prefix+'_created'],filename)
            for child in process.children(recursive=True):
                if child.name().lower()=='curl.exe':child.kill()
            process.kill()
    d.save(FOLDER/'TRANSPORT_QUEUE_V3_RECOVERY.json',{'utc':d.now(),'native_launches':0,'scope':'Owned transport controllers and their curl children only; primary resumes to reconcile any incomplete attachments.'})


def watchdog():
    while True:
        lease=d.read(LEASE)
        if lease['status']=='RESUMED':return
        if alive(lease['controller_pid'],lease['controller_created']) and time.time()<lease['deadline_epoch']:
            time.sleep(2);continue
        stop_auxiliaries(lease)
        resume(lease,'Independent watchdog recovery')
        return


def main():
    primary=psutil.Process(13664);supplement=psutil.Process(32156)
    identity(primary.pid,primary.create_time(),'resume_remote_evidence_v2.py')
    identity(supplement.pid,supplement.create_time(),'supplement_remote_delivery_v2.py')
    state=d.read(FOLDER/'REMOTE_RESUME_20261022_052cf8f1/PROGRESS.json')
    assert len(state['verified'])<10
    assert not set(['RTX_CLOSEOUT_006.zip','RTX_CLOSEOUT_007.zip','RTX_CLOSEOUT_011.zip']).intersection(state['active'])
    finals=list(FOLDER.glob('SUPPLEMENTAL_TRANSPORT_20261022_*/FINAL.json'))
    runs=list(FOLDER.glob('SUPPLEMENTAL_TRANSPORT_20261022_*'));assert len(runs)==1
    lease={'status':'SUSPEND_REQUESTED','utc':d.now(),'native_launches':0,
        'main_pid':primary.pid,'main_created':primary.create_time(),
        'supplement_pid':supplement.pid,'supplement_created':supplement.create_time(),
        'controller_pid':os.getpid(),'controller_created':psutil.Process().create_time(),
        'supplement_final':str(runs[0]/'FINAL.json'),'deadline_epoch':time.time()+7200,
        'source_sha256':d.sha(Path(__file__)),'psutil_version':psutil.__version__,
        'scope':'Owned Python delivery scheduler only is paused. All curl payload transfers continue, including three independent original queued ZIPs. Resume after both auxiliary groups reconcile; independent watchdog protects recovery. No model/native experiment processes.'}
    d.save(LEASE,lease)
    with (FOLDER/'TRANSPORT_QUEUE_V3_WATCHDOG.log').open('ab') as log:
        subprocess.Popen([sys.executable,str(Path(__file__)),'--watchdog'],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    success=False
    try:
        primary.suspend()
        lease.update({'status':'SUSPENDED','suspended_utc':d.now()});d.save(LEASE,lease)
        with (FOLDER/'PARALLEL_TRANSPORT.log').open('ab') as log:
            parallel=subprocess.Popen([sys.executable,'-u',str(WORK/'parallel_remaining_delivery_v3.py')],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
        lease.update({'parallel_pid':parallel.pid,'parallel_created':psutil.Process(parallel.pid).create_time()});d.save(LEASE,lease)
        print('PRIMARY_SCHEDULER_PAUSED_ALL_NINE_ATTACHMENTS_CAN_TRANSFER',flush=True)
        while not (Path(lease['supplement_final']).exists() and (FOLDER/'PARALLEL_TRANSPORT_FINAL.json').exists()):
            if not alive(parallel.pid,lease['parallel_created']) and not (FOLDER/'PARALLEL_TRANSPORT_FINAL.json').exists():raise RuntimeError('Parallel controller exited without final receipt')
            if time.time()>lease['deadline_epoch']-240:raise RuntimeError('Transport coordination deadline')
            time.sleep(1)
        success=True
    finally:
        if not success:stop_auxiliaries(lease)
        resume(lease,'All independent in-flight attachments reconciled' if success else 'Controller recovery; primary reconciles remaining assets')
    print('QUEUE_COORDINATION_DONE',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--watchdog',action='store_true');args=parser.parse_args()
    watchdog() if args.watchdog else main()
