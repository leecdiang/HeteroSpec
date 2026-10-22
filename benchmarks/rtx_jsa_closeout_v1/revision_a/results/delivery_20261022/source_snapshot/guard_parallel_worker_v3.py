"""Guard the actual parallel Python worker beneath the Windows venv launcher."""
import sys
import time
from pathlib import Path
WORK=Path(__file__).parent
sys.path.insert(0,str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')
REPAIR=FOLDER/'REPAIR_007_COORDINATION.json'
RECEIPT=FOLDER/'PARALLEL_WORKER_GUARD.json'


def main():
    lease=d.read(REPAIR)
    launcher=psutil.Process(lease['parallel_pid'])
    assert abs(launcher.create_time()-lease['parallel_created'])<0.01
    workers=[p for p in launcher.children() if any(Path(a).name=='parallel_remaining_delivery_v3.py' for a in p.cmdline())]
    assert len(workers)==1
    worker=workers[0]
    record={'status':'SUSPEND_REQUESTED','utc':d.now(),'native_launches':0,
        'launcher_pid':launcher.pid,'worker_pid':worker.pid,'worker_created':worker.create_time(),
        'guard_pid':psutil.Process().pid,'driver_sha256':d.sha(Path(__file__)),
        'scope':'Windows venv launcher indirection correction. Pause actual owned parallel metadata worker while its curl payloads continue; resume after 007 repair. No native study processes.'}
    d.save(RECEIPT,record)
    try:
        worker.suspend();record['status']='SUSPENDED';d.save(RECEIPT,record)
        launcher.resume()
        while d.read(REPAIR)['status']!='RESUMED':
            if time.time()>lease['deadline_epoch']+15:
                if psutil.pid_exists(lease['repair_pid']):
                    process=psutil.Process(lease['repair_pid'])
                    assert abs(process.create_time()-lease['repair_created'])<0.01
                    for child in process.children(recursive=True):
                        if child.name().lower()=='curl.exe':child.kill()
                    process.kill()
                time.sleep(3)
                break
            time.sleep(1)
    finally:
        worker.resume();launcher.resume()
        record.update({'status':'RESUMED','resumed_utc':d.now()});d.save(RECEIPT,record)
    print('ACTUAL_PARALLEL_WORKER_RESUMED',flush=True)


if __name__=='__main__':main()
