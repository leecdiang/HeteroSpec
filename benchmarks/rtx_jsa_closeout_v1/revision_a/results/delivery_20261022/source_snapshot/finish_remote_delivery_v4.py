"""Finish original 010 with a larger buffer and conservative network stall limits.

Runs only after the other 16 assets are verified and queue guards have resumed.
Reconciles and retires only the owned legacy delivery driver, never study jobs.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

WORK=Path(__file__).parent
sys.path.insert(0,str(WORK/'transport_support'))
import psutil
import resume_remote_evidence_v2 as d

FOLDER=Path('D:/hs144-evidence-e5c03228')
OLD=FOLDER/'REMOTE_RESUME_20261022_052cf8f1'
NAME='RTX_CLOSEOUT_010.zip'
OriginalPopen=subprocess.Popen


class BufferedCurl(OriginalPopen):
    def __init__(self,args,*pos,**kw):
        args=list(args)
        self.is_payload=Path(args[0]).name.lower()=='curl.exe'
        if self.is_payload:
            args+=['--upload-buffer-size','1048576']
            for flag,value in [('--speed-limit','16384'),('--speed-time','300'),('--max-time','10800')]:
                args[args.index(flag)+1]=value
        super().__init__(args,*pos,**kw)

    def communicate(self,input=None,timeout=None):
        if self.is_payload and timeout==5500:timeout=10900
        return super().communicate(input=input,timeout=timeout)


def main():
    expected={a['name']:a for a in d.read(FOLDER/'ARCHIVES.json')['archives']}
    for name in ['ARCHIVES.json','FILES.json']:
        expected[name]={'bytes':(FOLDER/name).stat().st_size,'sha256':d.sha(FOLDER/name)}
    remote={a['name']:a for a in d.assets()}
    assert all(name in remote and d.verified_asset(remote[name],v) for name,v in expected.items() if name!=NAME)
    assert NAME not in remote or not d.verified_asset(remote[NAME],expected[NAME]), 'Legacy driver already completed 010; do not replace it'
    queue=d.read(FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json')
    assert queue['status']=='RESUMED'
    for name in ['PARALLEL_WORKER_GUARD.json','REPAIR_TRANSPORT_DEADLINE_EXTENSION.json','REPAIR_007_COORDINATION.json']:
        assert d.read(FOLDER/name)['status']=='RESUMED'
    authorization=d.read(OLD/'AUTHORIZATION.json')
    assert all(d.sha(d.HERE/n)==h for n,h in authorization['unchanged_scientific_files'].items())
    assert d.sha(FOLDER/'ARCHIVES.json')==authorization['archive_manifest_sha256']
    assert d.sha(FOLDER/'FILES.json')==authorization['file_manifest_sha256']
    primary=psutil.Process(queue['main_pid'])
    assert abs(primary.create_time()-queue['main_created'])<0.01
    assert any(Path(a).name=='resume_remote_evidence_v2.py' for a in primary.cmdline())
    primary.suspend()  # No child can be spawned between inventory and retirement.
    children=primary.children(recursive=True)
    captured=[]
    for child in children:
        if child.name().lower()=='curl.exe':
            args=child.cmdline()
            assert '--upload-file' in args
            file=Path(args[args.index('--upload-file')+1]).name
            if file not in ['RTX_CLOSEOUT_000.zip','RTX_CLOSEOUT_008.zip','RTX_CLOSEOUT_002.zip',NAME]:
                primary.resume()
                raise RuntimeError('Unexpected child; delivery driver was resumed unchanged')
            captured.append({'pid':child.pid,'created':child.create_time(),'archive':file})
    retirement={'utc':d.now(),'native_launches':0,'primary_pid':primary.pid,
        'primary_created':primary.create_time(),'owned_curl_children':captured,
        'verified_other_assets':{n:d.receipt(remote[n],v) for n,v in expected.items() if n!=NAME},
        'reason':'Replace the owned delivery wrapper after a late slow-link interruption. No experiment rerun or archive repacking. Other 16 assets remain verified. New 010 transport uses 1MiB buffer and 16KiB/s over300s stall detection.'}
    d.save(FOLDER/'PRIMARY_DELIVERY_RETIREMENT_V4.json',retirement)
    primary.kill();primary.wait(10)
    for child in children:
        try:
            if child.is_running() and child.name().lower() in ['curl.exe','gh.exe']:child.kill()
        except psutil.NoSuchProcess:pass
    psutil.wait_procs(children,timeout=5)
    print('LEGACY_DELIVERY_WRAPPER_RETIRED_NATIVE_LAUNCHES_0',flush=True)
    run=FOLDER/('REMOTE_FINISH_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    auth={**authorization,'utc':d.now(),'driver_source':Path(__file__).name,
        'driver_sha256':d.sha(Path(__file__)),'original_base_driver_sha256':d.sha(WORK/'resume_remote_evidence_v2.py'),
        'native_launches':0,'prior_transport_run':str(OLD),
        'method':'Exact same original 010 bytes. 1MiB curl upload buffer, network stall16KiB/s for300s, max10800s, reconciled retries. No frozen code or budgets changed.'}
    d.save(run/'AUTHORIZATION.json',auth)
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    assert re.fullmatch(r'[A-Za-z0-9_.-]+',token)
    subprocess.Popen=BufferedCurl
    d.deliver(NAME,expected[NAME],FOLDER,run,token)
    assets=d.assets()
    assert len(assets)==17 and {a['name'] for a in assets}==set(expected)
    verified={a['name']:d.receipt(a,expected[a['name']]) for a in assets}
    release=d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}')
    assert release['draft'] and release['target_commitish']==d.EXECUTION
    assert all(d.sha(d.HERE/n)==h for n,h in auth['unchanged_scientific_files'].items())
    output={'status':'COMPLETE_DRAFT_RELEASE_ASSET_DELIVERY','study_uuid':d.STUDY,
        'release_id':d.RELEASE_ID,'release_url':release['html_url'],'tag':release['tag_name'],
        'draft':True,'target_commit':d.EXECUTION,'assets':verified,
        'verified_archive_shards':15,'total_archive_shards':15,'not_remotely_verified':[],
        'complete_local_access':True,'native_launches':0,'scientific_pins_unchanged':auth['unchanged_scientific_files'],
        'local_archive_manifest_sha256':d.sha(FOLDER/'ARCHIVES.json'),
        'local_file_manifest_sha256':d.sha(FOLDER/'FILES.json'),'transport_run':str(run),
        'prior_transport_run':str(OLD),'verification_scope':'Authenticated metadata and server-reported full SHA256; no full remote ZIP payload readback or remote re-extraction.'}
    d.save(run/'COMPLETE_UPLOAD_RECEIPTS.json',output)
    d.save(FOLDER/'REMOTE_RESUME_COMPLETE.json',output)
    d.save(FOLDER/'DRAFT_RELEASE.json',release)
    print('ALL_REMOTE_ASSETS_VERIFIED',len(verified),str(run),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--wait-ready',action='store_true');args=parser.parse_args()
    if args.wait_ready:
        print('WAITING_FOR_ALL_EXISTING_TRANSFERS_AND_GUARDS',flush=True)
        names=['TRANSPORT_QUEUE_COORDINATION_V3.json','PARALLEL_WORKER_GUARD.json','REPAIR_TRANSPORT_DEADLINE_EXTENSION.json','REPAIR_007_COORDINATION.json']
        while not all((FOLDER/n).exists() and d.read(FOLDER/n)['status']=='RESUMED' for n in names):time.sleep(2)
    main()
