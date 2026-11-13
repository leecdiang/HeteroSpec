"""Resumable draft-release delivery. No scientific/native requests."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess
import threading

REPO='leecdiang/HeteroSpec'
TAG='rtx-closeout-e5c03228-raw'
COMMIT='87570e6ac4c3f5060b5086969dfc5214e7b17da2'

def read(p):return json.loads(p.read_bytes())
def save(p,v):p.write_bytes((json.dumps(v,indent=2)+'\n').encode())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def api(path,method='GET',body=None):
    cmd=['gh','api',path,'-X',method]
    if body:cmd+=['--input',str(body)]
    result=subprocess.run(cmd,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError(result.stderr.decode(errors='replace')[-2000:])
    return json.loads(result.stdout)
def pages(path):
    result=[]
    for page in range(1,100):
        rows=api(path+f'?per_page=100&page={page}');result+=rows
        if len(rows)<100:return result
    raise RuntimeError('Unexpected pagination limit')

def main(folder):
    index=read(folder/'ARCHIVES.json')
    assert index['status']=='PASS_LOSSLESS_FRESH_EXTRACTION'
    releases=[r for r in pages(f'repos/{REPO}/releases') if r['tag_name']==TAG]
    assert len(releases)<=1
    if releases:release=releases[0]
    else:
        request=folder/'RELEASE_CREATE_REQUEST.json'
        save(request,{'tag_name':TAG,'target_commitish':COMMIT,'name':'RTX PR140 amended closeout: complete raw evidence',
            'body':'Full finite-study raw evidence for PR144. Execution is pinned to '+COMMIT+'. Archive and file manifests include SHA256 identities and lossless fresh-extraction checks. No weights or third-party numerical DLL bytes are redistributed. Results and limitations: https://github.com/leecdiang/HeteroSpec/pull/144',
            'draft':True,'prerelease':False})
        release=api(f'repos/{REPO}/releases','POST',request)
    assert release['draft'] is True and release['tag_name']==TAG and release['target_commitish']==COMMIT
    save(folder/'DRAFT_RELEASE.json',release)
    expected={a['name']:{'bytes':a['bytes'],'sha256':a['sha256']} for a in index['archives']}
    for name in ['FILES.json','ARCHIVES.json']:
        expected[name]={'bytes':(folder/name).stat().st_size,'sha256':sha(folder/name)}
    receipts={};lock=threading.Lock()
    def deliver(name,identity):
        existing=[a for a in pages(f'repos/{REPO}/releases/{release["id"]}/assets') if a['name']==name]
        assert len(existing)<=1
        if not existing:
            result=subprocess.run(['gh','release','upload',TAG,str(folder/name),'--repo',REPO],capture_output=True,timeout=5400)
            if result.returncode:raise RuntimeError(name+': '+result.stderr.decode(errors='replace')[-2000:])
            existing=[a for a in pages(f'repos/{REPO}/releases/{release["id"]}/assets') if a['name']==name]
        assert len(existing)==1
        asset=api(f'repos/{REPO}/releases/assets/{existing[0]["id"]}')
        assert asset['name']==name and asset['size']==identity['bytes'] and asset['state']=='uploaded'
        digest=asset.get('digest')
        if digest is not None:
            assert digest=='sha256:'+identity['sha256'],name+' remote server digest differs'
            verification='AUTHENTICATED_METADATA_AND_SERVER_SHA256_MATCH; no full remote payload readback'
        else:
            process=subprocess.Popen(['gh','api',f'repos/{REPO}/releases/assets/{asset["id"]}','-H','Accept: application/octet-stream'],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            hasher=hashlib.sha256();count=0
            while True:
                block=process.stdout.read(1024*1024)
                if not block:break
                hasher.update(block);count+=len(block)
            error=process.stderr.read();code=process.wait(timeout=60)
            assert code==0 and count==identity['bytes'] and hasher.hexdigest()==identity['sha256'],name+' remote full payload verification failed '+error.decode(errors='replace')[-500:]
            verification='FULL_AUTHENTICATED_REMOTE_PAYLOAD_SHA256_MATCH'
        receipt={'asset_id':asset['id'],'api_url':asset['url'],'browser_download_url':asset['browser_download_url'],
            'bytes':asset['size'],'sha256':identity['sha256'],'server_digest':digest,'verification':verification}
        with lock:
            receipts[name]=receipt
            save(folder/'UPLOAD_PROGRESS.json',receipts)
        print('UPLOADED_VERIFIED',name,asset['size'],verification,flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        tasks=[executor.submit(deliver,n,v) for n,v in expected.items()]
        for task in concurrent.futures.as_completed(tasks):task.result()
    save(folder/'UPLOAD_RECEIPTS.json',{'status':'COMPLETE_DRAFT_RELEASE_ASSET_DELIVERY','release_id':release['id'],
        'release_url':release['html_url'],'tag':TAG,'draft':True,'target_commit':COMMIT,'assets':receipts})
    print('ALL_ASSETS_VERIFIED',len(receipts),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);main(p.parse_args().folder)
