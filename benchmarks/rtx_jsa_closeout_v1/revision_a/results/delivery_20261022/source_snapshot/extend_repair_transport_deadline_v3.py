"""Extend only the network repair lease while retaining bounded queue recovery."""
import sys
import time
from pathlib import Path
WORK=Path(__file__).parent
sys.path.insert(0,str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')
REPAIR=FOLDER/'REPAIR_007_COORDINATION.json'
RECEIPT=FOLDER/'REPAIR_TRANSPORT_DEADLINE_EXTENSION.json'


def main():
    lease=d.read(REPAIR)
    guard_data=d.read(FOLDER/'PARALLEL_WORKER_GUARD.json')
    assert lease['status']=='SUSPENDED' and guard_data['status']=='SUSPENDED'
    guard=psutil.Process(guard_data['guard_pid'])
    assert any(Path(a).name=='guard_parallel_worker_v3.py' for a in guard.cmdline())
    queue=d.read(FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json')
    old=lease['deadline_epoch']
    lease['deadline_epoch']=min(old+3600,queue['deadline_epoch']-300)
    assert lease['deadline_epoch']>old
    record={'status':'SUSPEND_REQUESTED','utc':d.now(),'native_launches':0,
        'guard_pid':guard.pid,'guard_created':guard.create_time(),'old_network_deadline_epoch':old,
        'new_network_deadline_epoch':lease['deadline_epoch'],'driver_sha256':d.sha(Path(__file__)),
        'scope':'Network-only lease extension. Hold owned metadata guard until 007 repair completes, then resume it. Independent repair/primary watchdogs remain active. Frozen experiment/worker budgets unchanged.'}
    d.save(RECEIPT,record)
    try:
        guard.suspend();record['status']='SUSPENDED';d.save(RECEIPT,record)
        d.save(REPAIR,lease)
        while d.read(REPAIR)['status']!='RESUMED':time.sleep(1)
    finally:
        guard.resume();record.update({'status':'RESUMED','resumed_utc':d.now()});d.save(RECEIPT,record)
    print('NETWORK_REPAIR_GUARD_RESUMED',flush=True)


if __name__=='__main__':main()
