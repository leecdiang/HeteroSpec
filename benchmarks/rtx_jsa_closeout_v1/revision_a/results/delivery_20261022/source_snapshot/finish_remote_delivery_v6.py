"""Finish original 007 and010 with proven flags and bounded whole-transfer waits.

Runs only after the other 15 assets are verified and queue guards have resumed.
Legacy delivery drivers have already been retired; never launches study jobs.
"""
import argparse
import concurrent.futures
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
TARGETS=['RTX_CLOSEOUT_007.zip','RTX_CLOSEOUT_010.zip']
OriginalPopen=subprocess.Popen


class WholeTransferCurl(OriginalPopen):
    def __init__(self,args,*pos,**kw):
        args=list(args)
        self.is_payload=Path(args[0]).name.lower()=='curl.exe'
        if self.is_payload:
            for flag in ['--speed-limit','--speed-time']:
                index=args.index(flag);del args[index:index+2]
            args[args.index('--max-time')+1]='10800'
        super().__init__(args,*pos,**kw)

    def communicate(self,input=None,timeout=None):
        if self.is_payload and timeout==5500:timeout=10900
        return super().communicate(input=input,timeout=timeout)


def main():
    expected={a['name']:a for a in d.read(FOLDER/'ARCHIVES.json')['archives']}
    for name in ['ARCHIVES.json','FILES.json']:
        expected[name]={'bytes':(FOLDER/name).stat().st_size,'sha256':d.sha(FOLDER/name)}
    remote={a['name']:a for a in d.assets()}
    assert all(name in remote and d.verified_asset(remote[name],v) for name,v in expected.items() if name not in TARGETS)
    assert any(n not in remote or not d.verified_asset(remote[n],expected[n]) for n in TARGETS)
    queue=d.read(FOLDER/'TRANSPORT_QUEUE_COORDINATION_V3.json')
    assert queue['status']=='RESUMED'
    for name in ['PARALLEL_WORKER_GUARD.json','REPAIR_TRANSPORT_DEADLINE_EXTENSION.json','REPAIR_007_COORDINATION.json']:
        assert d.read(FOLDER/name)['status']=='RESUMED'
    authorization=d.read(OLD/'AUTHORIZATION.json')
    assert all(d.sha(d.HERE/n)==h for n,h in authorization['unchanged_scientific_files'].items())
    assert d.sha(FOLDER/'ARCHIVES.json')==authorization['archive_manifest_sha256']
    assert d.sha(FOLDER/'FILES.json')==authorization['file_manifest_sha256']
    retirement=d.read(FOLDER/'PRIMARY_DELIVERY_RETIREMENT_V5.json')
    assert retirement['native_launches']==0
    if psutil.pid_exists(retirement['primary_pid']):
        assert abs(psutil.Process(retirement['primary_pid']).create_time()-retirement['primary_created'])>0.01
    print('RESUMING_TWO_ORIGINAL_ASSETS_LEGACY_DRIVERS_CLOSED',flush=True)
    run=FOLDER/('REMOTE_FINISH_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    auth={**authorization,'utc':d.now(),'driver_source':Path(__file__).name,
        'driver_sha256':d.sha(Path(__file__)),'original_base_driver_sha256':d.sha(WORK/'resume_remote_evidence_v2.py'),
        'native_launches':0,'prior_transport_run':str(OLD),
        'method':'Exact same original 007/010 bytes. Previously proven curl flags only; no low-speed abort; max10800s plus reconciled retries. No frozen code, experimental timeouts or worker budgets changed.'}
    d.save(run/'AUTHORIZATION.json',auth)
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    assert re.fullmatch(r'[A-Za-z0-9_.-]+',token)
    subprocess.Popen=WholeTransferCurl
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        tasks=[executor.submit(d.deliver,n,expected[n],FOLDER,run,token) for n in TARGETS]
        for task in tasks:task.result()
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
