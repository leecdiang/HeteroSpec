"""Reconcile/retry only the failed 007 transport, guarding the paused queue."""
import argparse
import concurrent.futures
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

WORK=Path(__file__).parent
sys.path.insert(0,str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')
LEASE=FOLDER/'REPAIR_007_COORDINATION.json'


def target(lease):
    process=psutil.Process(lease['parallel_pid'])
    assert abs(process.create_time()-lease['parallel_created'])<0.01
    assert any(Path(arg).name=='parallel_remaining_delivery_v3.py' for arg in process.cmdline())
    return process


def resume(lease,reason):
    target(lease).resume()
    lease.update({'status':'RESUMED','resumed_utc':d.now(),'reason':reason})
    d.save(LEASE,lease)


def watchdog():
    while True:
        lease=d.read(LEASE)
        if lease['status']=='RESUMED':return
        alive=psutil.pid_exists(lease['repair_pid'])
        if alive:alive=abs(psutil.Process(lease['repair_pid']).create_time()-lease['repair_created'])<0.01
        if alive and time.time()<lease['deadline_epoch']:
            time.sleep(2);continue
        for process in psutil.process_iter(['pid','ppid','name','create_time','cmdline']):
            info=process.info
            if (info['ppid']==lease['repair_pid'] and info['create_time']>=lease['repair_created']
                and info['name'].lower()=='curl.exe'
                and str(FOLDER/'RTX_CLOSEOUT_007.zip') in (info['cmdline'] or [])):
                process.kill()
        if alive:psutil.Process(lease['repair_pid']).kill()
        resume(lease,'Independent repair watchdog; primary will reconcile 007 if needed')
        return


def main():
    queue=d.read(FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json')
    assert queue['status']=='SUSPENDED'
    lease={'status':'SUSPEND_REQUESTED','utc':d.now(),'native_launches':0,
        'parallel_pid':queue['parallel_pid'],'parallel_created':queue['parallel_created'],
        'repair_pid':os.getpid(),'repair_created':psutil.Process().create_time(),
        'deadline_epoch':time.time()+4200,'driver_sha256':d.sha(Path(__file__)),
        'scope':'Pause owned parallel metadata controller while its 006/011 curl transfers continue. Retry only original 007 bytes; resume controller after reconciliation. Independent bounded watchdog.'}
    d.save(LEASE,lease)
    with (FOLDER/'REPAIR_007_WATCHDOG.log').open('ab') as log:
        subprocess.Popen([sys.executable,str(Path(__file__)),'--watchdog'],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
    run=FOLDER/('REPAIR_007_TRANSPORT_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    identity=next(a for a in d.read(FOLDER/'ARCHIVES.json')['archives'] if a['name']=='RTX_CLOSEOUT_007.zip')
    d.save(run/'AUTHORIZATION.json',lease)
    asset=d.find(identity['name'])
    assert asset is None or d.verified_asset(asset,identity)
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    try:
        target(lease).suspend();lease['status']='SUSPENDED';d.save(LEASE,lease)
        answer=d.deliver(identity['name'],identity,FOLDER,run,token)
        d.save(run/'FINAL.json',{'status':'PASS','utc':d.now(),'native_launches':0,'asset':answer})
        print('REPAIR_007_VERIFIED',flush=True)
    finally:resume(lease,'007 attempt reconciled')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--watchdog',action='store_true');args=parser.parse_args()
    watchdog() if args.watchdog else main()
