"""Upload only three late-queue assets while the primary driver handles earlier ones.

Stops before the primary queue can reach these names. Original bytes only;
no native/model processes. A one-shot transport attempt is reconciled by digest.
"""
import concurrent.futures
import json
from pathlib import Path
import re
import subprocess
import threading
import time
import urllib.parse
import uuid

import resume_remote_evidence_v2 as d

FOLDER = Path('D:/hs144-evidence-e5c03228')
MAIN = FOLDER/'REMOTE_RESUME_20261022_052cf8f1/PROGRESS.json'
NAMES = ['RTX_CLOSEOUT_010.zip','RTX_CLOSEOUT_012.zip','RTX_CLOSEOUT_005.zip']
STOP = threading.Event()
LOCK = threading.Lock()
CHILDREN = {}


def one(name, identity, token, run):
    local = FOLDER/name
    assert local.stat().st_size == identity['bytes'] and d.sha(local) == identity['sha256']
    old = d.find(name)
    if old:
        if d.verified_asset(old, identity):
            d.save(run/(name+'.verified.json'), d.receipt(old,identity))
            return
        raise RuntimeError('Supplement refuses an already present incomplete asset: '+name)
    if STOP.is_set(): return
    response = run/(name+'.response.json')
    stderr = run/(name+'.stderr.txt')
    url = f'https://uploads.github.com/repos/{d.REPO}/releases/{d.RELEASE_ID}/assets?name='+urllib.parse.quote(name)
    cmd = ['curl.exe','--config','-','--http1.1','--request','POST','--upload-file',str(local),
           '--header','Content-Type: application/zip','--header','Accept: application/vnd.github+json',
           '--connect-timeout','30','--speed-limit','131072','--speed-time','90','--max-time','5400',
           '--silent','--show-error','--output',str(response),'--write-out','%{json}','--url',url]
    start = time.monotonic()
    with stderr.open('xb') as errors:
        with LOCK:
            if STOP.is_set(): return
            process = subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors)
            CHILDREN[name] = process
        print('SUPPLEMENT_UPLOAD',name,'pid',process.pid,flush=True)
        try:
            out,_ = process.communicate(('header = "Authorization: Bearer '+token+'"\n').encode(), timeout=5500)
        except subprocess.TimeoutExpired:
            process.kill(); out,_ = process.communicate()
        finally:
            with LOCK: CHILDREN.pop(name,None)
    try: metrics=json.loads(out)
    except (ValueError,UnicodeDecodeError): metrics={}
    record={'name':name,'utc':d.now(),'curl_exit':process.returncode,'seconds':time.monotonic()-start,
            'controller_stop':STOP.is_set(),
            **{k:metrics.get(k) for k in ['http_code','size_upload','speed_upload','time_total','errormsg']}}
    d.save(run/(name+'.receipt.json'),record)
    remote=d.find(name)
    if remote and d.verified_asset(remote,identity):
        d.save(run/(name+'.verified.json'),d.receipt(remote,identity))
        print('SUPPLEMENT_VERIFIED',name,flush=True)
        return
    if remote:
        assert remote['state']=='starter' and remote['size']==identity['bytes'] and remote.get('digest') is None
        d.save(run/(name+'.incomplete.json'),remote)
        d.api(f'repos/{d.REPO}/releases/assets/{remote["id"]}','DELETE')
        print('SUPPLEMENT_INCOMPLETE_REMOVED',name,flush=True)
    print('SUPPLEMENT_NOT_COMPLETE',name,flush=True)


def main():
    state=d.read(MAIN)
    assert len(state['verified']) < 11
    assert not set(NAMES).intersection(state['active'])
    release=d.api(f'repos/{d.REPO}/releases/{d.RELEASE_ID}')
    assert release['draft'] and release['target_commitish']==d.EXECUTION
    run=FOLDER/('SUPPLEMENTAL_TRANSPORT_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    pins=d.read(MAIN.parent/'AUTHORIZATION.json')['unchanged_scientific_files']
    assert all(d.sha(d.HERE/n)==h for n,h in pins.items())
    d.save(run/'AUTHORIZATION.json',{'utc':d.now(),'release_id':d.RELEASE_ID,'native_launches':0,
        'original_archive_names':NAMES,'driver_sha256':d.sha(Path(__file__)),
        'main_progress':str(MAIN),'stop_before_main_verified_assets':11,
        'scientific_pins_unchanged':pins,'scope':'Independent late-queue exact-byte attachments only. One reconciled attempt each. Stop when primary completes the current three early-queue attachments, or STOP_SUPPLEMENT file appears.'})
    expected={a['name']:a for a in d.read(FOLDER/'ARCHIVES.json')['archives']}
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    assert re.fullmatch(r'[A-Za-z0-9_.-]+',token)
    done=threading.Event()
    def monitor():
        while not done.wait(1):
            current=d.read(MAIN)
            if (len(current['verified'])>=11 or set(NAMES).intersection(current['active'])
                or (FOLDER/'STOP_SUPPLEMENT').exists()):
                STOP.set()
                with LOCK:
                    for child in CHILDREN.values():
                        if child.poll() is None:child.kill()
                return
    watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
    failures={}
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            jobs={executor.submit(one,n,expected[n],token,run):n for n in NAMES}
            for task in concurrent.futures.as_completed(jobs):
                try:task.result()
                except Exception as error:failures[jobs[task]]=repr(error)
    finally:done.set();watcher.join(timeout=2)
    assert all(d.sha(d.HERE/n)==h for n,h in pins.items())
    d.save(run/'FINAL.json',{'utc':d.now(),'native_launches':0,'controller_stopped':STOP.is_set(),
        'failures':failures,'verified_names':[n for n in NAMES if (run/(n+'.verified.json')).exists()]})
    print('SUPPLEMENT_DONE',str(run),json.dumps(failures),flush=True)


if __name__=='__main__':main()
