"""One reconciled exact-byte attempt for three otherwise queued attachments."""
import concurrent.futures
from pathlib import Path
import re
import subprocess
import sys
import uuid
import supplement_remote_delivery_v2 as s
import resume_remote_evidence_v2 as d


def main():
    lease=d.read(s.FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json')
    assert lease['status']=='SUSPENDED'
    names=['RTX_CLOSEOUT_006.zip','RTX_CLOSEOUT_007.zip','RTX_CLOSEOUT_011.zip']
    run=s.FOLDER/('PARALLEL_TRANSPORT_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    expected={a['name']:a for a in d.read(s.FOLDER/'ARCHIVES.json')['archives']}
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    assert re.fullmatch(r'[A-Za-z0-9_.-]+',token)
    d.save(run/'AUTHORIZATION.json',{'utc':d.now(),'native_launches':0,'release_id':d.RELEASE_ID,
        'driver_sha256':d.sha(Path(__file__)),'original_archive_names':names,
        'scope':'Only original queued ZIPs while primary delivery scheduler is suspended. Other in-flight curl attachments continue. One attempt, reconciled by server size and SHA256.'})
    failures={}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            jobs={executor.submit(s.one,n,expected[n],token,run):n for n in names}
            for task in concurrent.futures.as_completed(jobs):
                try:task.result()
                except Exception as error:failures[jobs[task]]=repr(error)
    finally:
        result={'utc':d.now(),'native_launches':0,'failures':failures,'transport_run':str(run),
            'verified_names':[n for n in names if (run/(n+'.verified.json')).exists()]}
        d.save(run/'FINAL.json',result)
        d.save(s.FOLDER/'PARALLEL_TRANSPORT_FINAL.json',result)
    print('PARALLEL_QUEUED_UPLOADS_DONE',str(run),flush=True)


if __name__=='__main__':main()
