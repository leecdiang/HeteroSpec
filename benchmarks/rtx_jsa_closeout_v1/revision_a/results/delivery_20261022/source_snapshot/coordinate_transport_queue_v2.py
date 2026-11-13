"""Let in-flight original attachments finish without colliding with the main queue.

Only the owned Python delivery scheduler is suspended; its curl children continue.
An independent watchdog resumes it on controller failure after stopping supplements.
This never touches native study processes or scientific files.
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

WORK = Path(__file__).parent
sys.path.insert(0, str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER = Path('D:/hs144-evidence-e5c03228')
MAIN = FOLDER/'REMOTE_RESUME_20261022_052cf8f1/PROGRESS.json'
LEASE = FOLDER/'TRANSPORT_QUEUE_COORDINATION.json'


def identity(pid, created, filename):
    process=psutil.Process(pid)
    assert abs(process.create_time()-created)<0.01
    assert any(Path(arg).name==filename for arg in process.cmdline())
    return process


def resume(lease):
    process=identity(lease['main_pid'],lease['main_created'],'resume_remote_evidence_v2.py')
    process.resume()
    current=d.read(LEASE)
    current.update({'status':'RESUMED','resumed_utc':d.now()})
    d.save(LEASE,current)
    print('MAIN_DELIVERY_SCHEDULER_RESUMED',flush=True)


def watchdog():
    while True:
        lease=d.read(LEASE)
        if lease['status'] in ['RESUMED','NO_PAUSE_NEEDED']:return
        alive=psutil.pid_exists(lease['controller_pid'])
        if alive:
            alive=abs(psutil.Process(lease['controller_pid']).create_time()-lease['controller_created'])<0.01
        if alive and time.time()<lease['deadline_epoch']:
            time.sleep(2);continue
        if lease['status']=='SUSPENDED':
            # Stop/clean only the authorized supplemental delivery before resuming.
            (FOLDER/'STOP_SUPPLEMENT').write_text('Queue coordination watchdog recovery\n')
            end=time.monotonic()+300
            while not Path(lease['supplement_final']).exists() and time.monotonic()<end:time.sleep(2)
            if not Path(lease['supplement_final']).exists():
                supplement=identity(lease['supplement_pid'],lease['supplement_created'],'supplement_remote_delivery_v2.py')
                for child in supplement.children(recursive=True):
                    if child.name().lower()=='curl.exe':child.kill()
                supplement.kill()
                d.save(FOLDER/'TRANSPORT_QUEUE_WATCHDOG_RECOVERY.json',{'utc':d.now(),'native_launches':0,'scope':'Owned failed supplemental transport only'})
            resume(lease)
        return


def main():
    main_process=psutil.Process(13664)
    supplement=psutil.Process(32156)
    identity(main_process.pid,main_process.create_time(),'resume_remote_evidence_v2.py')
    identity(supplement.pid,supplement.create_time(),'supplement_remote_delivery_v2.py')
    supplemental=list(FOLDER.glob('SUPPLEMENTAL_TRANSPORT_20261022_*'))
    assert len(supplemental)==1
    final=supplemental[0]/'FINAL.json'
    lease={'status':'WAITING_FOR_QUEUE_BOUNDARY','utc':d.now(),'native_launches':0,
        'main_pid':main_process.pid,'main_created':main_process.create_time(),
        'supplement_pid':supplement.pid,'supplement_created':supplement.create_time(),
        'controller_pid':os.getpid(),'controller_created':psutil.Process().create_time(),
        'supplement_final':str(final),'deadline_epoch':time.time()+7200,
        'driver_sha256':d.sha(Path(__file__)),'psutil_version':psutil.__version__,
        'scope':'Pause owned delivery scheduler at 10 verified assets; in-flight curl children continue. Resume after supplemental attachments reconcile. No native/model work.'}
    d.save(LEASE,lease)
    with (FOLDER/'TRANSPORT_QUEUE_WATCHDOG.log').open('ab') as log:
        guardian=subprocess.Popen([sys.executable,str(Path(__file__)),'--watchdog'],stdout=log,stderr=log)
    print('QUEUE_COORDINATION_ARMED',guardian.pid,flush=True)
    paused=False
    try:
        while not final.exists():
            state=d.read(MAIN)
            if len(state['verified'])>=11:
                lease['status']='NO_PAUSE_NEEDED';d.save(LEASE,lease);return
            if len(state['verified'])>=10:
                main_process.suspend();paused=True
                lease.update({'status':'SUSPENDED','suspended_utc':d.now(),'native_launches':0})
                d.save(LEASE,lease)
                print('DELIVERY_SCHEDULER_PAUSED_CURL_CONTINUES',flush=True)
                break
            time.sleep(1)
        if not paused:
            lease['status']='NO_PAUSE_NEEDED';d.save(LEASE,lease);return
        while not final.exists():
            if time.time()>lease['deadline_epoch']-360:
                (FOLDER/'STOP_SUPPLEMENT').write_text('Queue coordination deadline\n')
            time.sleep(1)
    finally:
        if paused:resume(lease)
    print('QUEUE_COORDINATION_COMPLETE',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--watchdog',action='store_true')
    args=parser.parse_args()
    watchdog() if args.watchdog else main()
