"""Exact-byte GitHub release delivery only. Never launches model/native experiments.

Uses release ID, curl streaming with low-speed detection, and reconciled retries.
Credentials are passed to curl over stdin, never argv, disk, or logs.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import urllib.parse
import uuid

REPO='leecdiang/HeteroSpec'
RELEASE_ID=419851832
EXECUTION='87570e6ac4c3f5060b5086969dfc5214e7b17da2'
STUDY='e5c03228-9eb9-4198-8f14-a7d279d08afa'
WORK=Path(__file__).parent
HERE=WORK/'HeteroSpec/benchmarks/rtx_jsa_closeout_v1/revision_a'
os.environ['GODEBUG']='http2client=0'
LOCK=threading.Lock()
STATE={'active':{},'verified':{},'failed':{}}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(p,value):
    data=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    temporary=p.with_name(p.name+'.tmp');temporary.write_bytes(data);temporary.replace(p)
def api(path,method='GET',body=None):
    cmd=['gh','api',path,'-X',method,'-H','Cache-Control: no-cache']
    if body is not None:cmd+=['--input',str(body)]
    for attempt in range(5 if method=='GET' else 1):
        result=subprocess.run(cmd,capture_output=True,timeout=100)
        if result.returncode==0:return json.loads(result.stdout) if result.stdout.strip() else None
        error=result.stderr.decode(errors='replace')[-2000:]
        if method!='GET' or 'HTTP 404' in error or attempt==4:raise RuntimeError(error)
        time.sleep(min(2**attempt,8))
def assets():
    rows=[]
    for page in range(1,20):
        part=api(f'repos/{REPO}/releases/{RELEASE_ID}/assets?per_page=100&page={page}')
        rows+=part
        if len(part)<100:return rows
    raise RuntimeError('Unexpected asset pagination')
def find(name):
    rows=[a for a in assets() if a['name']==name]
    if len(rows)>1:raise RuntimeError('Duplicate remote asset name: '+name)
    return rows[0] if rows else None
def verified_asset(asset,identity):
    return (asset['state']=='uploaded' and asset['size']==identity['bytes']
        and asset.get('digest')=='sha256:'+identity['sha256'])
def receipt(asset,identity):
    if not verified_asset(asset,identity):raise RuntimeError('Remote identity mismatch: '+asset['name'])
    return {'asset_id':asset['id'],'api_url':asset['url'],'browser_download_url':asset['browser_download_url'],
        'bytes':asset['size'],'sha256':identity['sha256'],'server_digest':asset['digest'],
        'created_at':asset['created_at'],'updated_at':asset['updated_at'],'checked_utc':now(),
        'verification':'AUTHENTICATED_METADATA_AND_SERVER_SHA256_MATCH; no full remote payload readback'}
def progress(run):
    save(run/'PROGRESS.json',{'utc':now(),**STATE})

def deliver(name,identity,folder,run,token):
    path=folder/name
    if path.stat().st_size!=identity['bytes'] or sha(path)!=identity['sha256']:
        raise RuntimeError('Local archive bytes drift: '+name)
    with LOCK:STATE['active'][name]={'phase':'reconcile','started_utc':now()};progress(run)
    for attempt in range(1,7):
        asset=find(name)
        if asset and asset['state']=='uploaded':
            answer=receipt(api(f'repos/{REPO}/releases/assets/{asset["id"]}'),identity)
            with LOCK:
                STATE['verified'][name]=answer;STATE['active'].pop(name,None);progress(run)
            print('VERIFIED',name,identity['bytes'],flush=True)
            return answer
        if asset:
            if asset['state']!='starter' or asset['size']!=identity['bytes'] or asset.get('digest') is not None:
                raise RuntimeError('Unexpected incomplete asset: '+name)
            save(run/f'{name}.attempt{attempt}.orphan.json',asset)
            api(f'repos/{REPO}/releases/assets/{asset["id"]}','DELETE')
        response=run/f'{name}.attempt{attempt}.response.json'
        stderr=run/f'{name}.attempt{attempt}.stderr.txt'
        url=f'https://uploads.github.com/repos/{REPO}/releases/{RELEASE_ID}/assets?name='+urllib.parse.quote(name)
        cmd=['curl.exe','--config','-','--http1.1','--request','POST','--upload-file',str(path),
            '--header','Content-Type: application/zip' if name.endswith('.zip') else 'Content-Type: application/json',
            '--header','Accept: application/vnd.github+json','--connect-timeout','30',
            '--speed-limit','131072','--speed-time','90','--max-time','5400',
            '--silent','--show-error','--output',str(response),'--write-out','%{json}','--url',url]
        secret_config='header = "Authorization: Bearer '+token+'"\n'
        with LOCK:
            STATE['active'][name]={'phase':'upload','attempt':attempt,'started_utc':now()};progress(run)
        print('UPLOAD',name,'attempt',attempt,flush=True)
        start=time.monotonic()
        with stderr.open('xb') as errors:
            process=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors)
            try:stdout,_=process.communicate(secret_config.encode(),timeout=5500)
            except subprocess.TimeoutExpired:
                process.kill();stdout,_=process.communicate()
        try:metrics=json.loads(stdout)
        except (json.JSONDecodeError,UnicodeDecodeError):metrics={}
        summary={'utc':now(),'name':name,'attempt':attempt,'curl_exit':process.returncode,
            'seconds':time.monotonic()-start,
            **{k:metrics.get(k) for k in ['http_code','size_upload','speed_upload','time_total','errormsg']}}
        save(run/f'{name}.attempt{attempt}.receipt.json',summary)
        # Every outcome is reconciled by name, including ambiguous response/network failures.
        for wait in [0,2,5]:
            if wait:time.sleep(wait)
            remote=find(name)
            if remote and remote['state']=='uploaded':
                answer=receipt(api(f'repos/{REPO}/releases/assets/{remote["id"]}'),identity)
                with LOCK:
                    STATE['verified'][name]=answer;STATE['active'].pop(name,None);progress(run)
                print('VERIFIED',name,identity['bytes'],flush=True)
                return answer
        print('RETRY_TRANSPORT',name,'curl',process.returncode,'http',summary.get('http_code'),flush=True)
        time.sleep(min(attempt*3,15))
    raise RuntimeError('Six transport attempts exhausted: '+name)

def main(folder):
    index=read(folder/'ARCHIVES.json');baseline=read(folder/'UPLOAD_RECEIPTS.json')
    if index['status']!='PASS_LOSSLESS_FRESH_EXTRACTION':raise RuntimeError('Unverified local archives')
    if sha(folder/'ARCHIVES.json')!=baseline['local_archive_manifest_sha256']:raise RuntimeError('Archive manifest drift')
    if sha(folder/'FILES.json')!=baseline['local_file_manifest_sha256']:raise RuntimeError('File manifest drift')
    release=api(f'repos/{REPO}/releases/{RELEASE_ID}')
    if not release['draft'] or release['target_commitish']!=EXECUTION:raise RuntimeError('Release freeze differs')
    run=folder/('REMOTE_RESUME_20261022_'+uuid.uuid4().hex[:8]);run.mkdir()
    shutil.copyfile(folder/'UPLOAD_RECEIPTS.json',run/'PRIOR_UPLOAD_RECEIPTS.json')
    expected={a['name']:{'bytes':a['bytes'],'sha256':a['sha256']} for a in index['archives']}
    for name in ['FILES.json','ARCHIVES.json']:expected[name]={'bytes':(folder/name).stat().st_size,'sha256':sha(folder/name)}
    pins={name:sha(HERE/name) for name in ['F0B_EXECUTION.json','INPUT_MANIFEST.json','finalize.py','audit_raw.py','execute_panel.py','runner.py','RESULT.md','PAPER_ADDENDUM.md','results/ESTIMATES.json']}
    save(run/'AUTHORIZATION.json',{'study_uuid':STUDY,'execution_commit':EXECUTION,'release_id':RELEASE_ID,
        'observed_tag_name':release['tag_name'],'utc':now(),'native_launches':0,'driver_sha256':sha(Path(__file__)),
        'author_request':'继续把剩余13个原始证据分片上传到GitHub，补齐PR144的远端访问和校验回执，不重跑实验，保留其余约束。',
        'unchanged_scientific_files':pins,'archive_manifest_sha256':sha(folder/'ARCHIVES.json'),
        'file_manifest_sha256':sha(folder/'FILES.json'),'method':'curl streaming POST by release ID, bounded low-speed detection and reconciled exact-byte retries; TLS and authentication enabled.'})
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.DEVNULL).decode().strip()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+',token):raise RuntimeError('Unexpected credential format')
    stop=threading.Event()
    def heartbeat():
        while not stop.wait(30):
            with LOCK:
                progress(run);print('STATUS',len(STATE['verified']),'of',len(expected),'active',','.join(STATE['active']),flush=True)
    monitor=threading.Thread(target=heartbeat,daemon=True);monitor.start()
    failures={}
    try:
        # Completed assets are checked first; small remaining archive first validates the transfer route.
        existing={a['name']:a for a in assets()}
        ordered=sorted(expected.items(),key=lambda item:(0 if item[0] in existing and existing[item[0]]['state']=='uploaded' else 1,item[1]['bytes']))
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            jobs={executor.submit(deliver,n,i,folder,run,token):n for n,i in ordered}
            for future in concurrent.futures.as_completed(jobs):
                name=jobs[future]
                try:future.result()
                except Exception as error:
                    failures[name]=repr(error)
                    with LOCK:STATE['failed'][name]=repr(error);STATE['active'].pop(name,None);progress(run)
                    print('FAILED_TRANSPORT',name,str(error),flush=True)
    finally:stop.set();monitor.join(timeout=2)
    if failures:raise RuntimeError('Unfinished remote assets: '+json.dumps(failures))
    current=api(f'repos/{REPO}/releases/{RELEASE_ID}')
    if not current['draft'] or current['target_commitish']!=EXECUTION:raise RuntimeError('Release identity drift')
    if any(sha(HERE/name)!=value for name,value in pins.items()):raise RuntimeError('Scientific artifact changed during delivery')
    output={'status':'COMPLETE_DRAFT_RELEASE_ASSET_DELIVERY','study_uuid':STUDY,'release_id':RELEASE_ID,
        'release_url':current['html_url'],'tag':current['tag_name'],'draft':True,'target_commit':EXECUTION,
        'assets':STATE['verified'],'verified_archive_shards':len(index['archives']),'total_archive_shards':len(index['archives']),
        'not_remotely_verified':[],'complete_local_access':True,'native_launches':0,'scientific_pins_unchanged':pins,
        'local_archive_manifest_sha256':sha(folder/'ARCHIVES.json'),'local_file_manifest_sha256':sha(folder/'FILES.json'),
        'transport_run':str(run),'verification_scope':'Authenticated metadata and server-reported SHA256, not full remote payload readback/re-extraction.'}
    save(run/'COMPLETE_UPLOAD_RECEIPTS.json',output)
    save(folder/'REMOTE_RESUME_COMPLETE.json',output)
    save(folder/'DRAFT_RELEASE.json',current)
    print('ALL_REMOTE_ASSETS_VERIFIED',len(output['assets']),str(run),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('D:/hs144-evidence-e5c03228'));main(p.parse_args().folder)
