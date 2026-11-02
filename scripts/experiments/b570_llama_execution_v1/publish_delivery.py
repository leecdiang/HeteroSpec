"""Publish a dedicated evidence release, then fresh-download and verify all objects."""
from pathlib import Path
import argparse,concurrent.futures,json,subprocess,time,urllib.request,urllib.error,urllib.parse
from object_archive import read,write,sha,need,verify
from recover_exposure_index import SafeRedirect

def run(root,remote,tag,commit):
    root=Path(root).resolve();remote=Path(remote).resolve();need(not remote.exists(),'fresh remote readback directory');remote.mkdir(parents=True)
    local=verify(root);credential=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',capture_output=True,text=True,check=True);secret=dict(x.split('=',1) for x in credential.stdout.splitlines() if '=' in x)['password']
    opener=urllib.request.build_opener(SafeRedirect)
    def request(url,method='GET',data=None,headers=None):
        h={'Authorization':'Bearer '+secret,'User-Agent':'HeteroSpec-B570-evidence-delivery','Accept':'application/vnd.github+json'};h.update(headers or {});req=urllib.request.Request(url,data=data,headers=h,method=method);return opener.open(req,timeout=180)
    api='https://api.github.com/repos/leecdiang/HeteroSpec'
    try:
        with request(api+'/releases/tags/'+tag) as r:release=json.load(r)
        need(release['tag_name']==tag and release['name']=='B570 Llama companion native evidence','owned evidence release identity')
    except urllib.error.HTTPError as e:
        if e.code!=404:raise
        body={'tag_name':tag,'target_commitish':commit,'name':'B570 Llama companion native evidence','draft':True,'prerelease':True,'body':'Independent B570 PR163 raw evidence. Content-addressed objects preserve all included raw paths and bytes; INDEX.json and MEMBERS.json describe reconstruction. Model weights and explicitly documented duplicate upstream transport are excluded. Publication verification is in progress.'}
        with request(api+'/releases','POST',json.dumps(body).encode(),{'Content-Type':'application/json'}) as r:release=json.load(r)
    def all_assets():
        found=[];page=1
        while True:
            with request(api+f'/releases/{release["id"]}/assets?per_page=100&page={page}') as r:batch=json.load(r)
            found.extend(batch)
            if len(batch)<100:return found
            page+=1
    write(remote/'RELEASE_BEFORE.json',release);upload=release['upload_url'].split('{')[0];assets={a['name']:a for a in all_assets()};index=read(root/'INDEX.json');names=[p['name'] for p in index['parts']]+['INDEX.json','MEMBERS.json']
    pins=[{'name':n,'bytes':(root/n).stat().st_size,'sha256':sha(root/n)} for n in names];manifest=root/'DELIVERY_ASSETS.json'
    if manifest.exists():need(read(manifest)['assets']==pins,'delivery manifest changed')
    else:write(manifest,{'assets':pins,'release_tag':tag,'source_commit':commit,'local_verification':local})
    pins.append({'name':manifest.name,'bytes':manifest.stat().st_size,'sha256':sha(manifest)})
    def one(pin):
        name=pin['name'];asset=assets.get(name)
        if asset is None:
            for attempt in range(5):
                try:
                    with (root/name).open('rb') as f,request(upload+'?name='+urllib.parse.quote(name), 'POST',f,{'Content-Type':'application/octet-stream','Content-Length':str(pin['bytes'])}) as r:asset=json.load(r)
                    break
                except Exception as exc:
                    write(remote/(name+f'.upload-failure-{attempt}.json'),{'failure_type':type(exc).__name__,'http_status':getattr(exc,'code',None),'local_sha256':pin['sha256']})
                    current=all_assets()
                    asset=next((x for x in current if x['name']==name and x['state']=='uploaded' and x['size']==pin['bytes']),None)
                    if asset:break
            need(asset is not None,'upload attempts exhausted')
        need(asset['size']==pin['bytes'] and asset['state']=='uploaded','remote asset size/state')
        destination=remote/name
        for attempt in range(6):
            partial=remote/(name+f'.download-attempt-{attempt}')
            try:
                with request(asset['url']+'?fresh='+str(time.time_ns()),headers={'Accept':'application/octet-stream'}) as r,partial.open('xb') as f:
                    while b:=r.read(4*1024**2):f.write(b)
                need(partial.stat().st_size==pin['bytes'] and sha(partial)==pin['sha256'],'fresh remote bytes mismatch');partial.rename(destination);break
            except Exception as exc:write(remote/(name+f'.download-failure-{attempt}.json'),{'failure_type':type(exc).__name__,'http_status':getattr(exc,'code',None)})
        need(destination.exists(),'remote download attempts exhausted');print('REMOTE_VERIFIED',name,flush=True)
        return dict(pin,asset_id=asset['id'],download_url=asset['browser_download_url'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:verified=list(pool.map(one,pins))
    result=verify(remote);result.update(authenticated_same_host_fresh_download=True,external_reader_verified=False,anonymous_access_claimed=False,assets=verified,release_url=release['html_url'],source_commit=commit)
    write(remote/'REMOTE_READBACK.json',result)
    receipt=remote/'REMOTE_READBACK.json'
    with receipt.open('rb') as f,request(upload+'?name=REMOTE_READBACK.json','POST',f,{'Content-Type':'application/json','Content-Length':str(receipt.stat().st_size)}) as r:receipt_asset=json.load(r)
    with request(receipt_asset['url']+'?fresh='+str(time.time_ns()),headers={'Accept':'application/octet-stream'}) as r:data=r.read()
    need(data==receipt.read_bytes(),'published readback receipt download');write(remote/'READBACK_RECEIPT_VERIFIED.json',{'sha256':sha(receipt),'download_url':receipt_asset['browser_download_url']})
    body={'draft':False,'body':f'Independent B570 PR163 native evidence, source {commit}. All {result["files"]} logical files / {result["objects"]} unique raw objects were verified after authenticated fresh remote download on the B570 host. INDEX.json and MEMBERS.json map raw paths to SHA256 objects. REMOTE_READBACK.json records verification. No anonymous/private-repository access or independent external-reader claim. No model weights included.'}
    with request(api+f'/releases/{release["id"]}','PATCH',json.dumps(body).encode(),{'Content-Type':'application/json'}) as r:final=json.load(r)
    write(remote/'RELEASE_PUBLISHED.json',final);print(final['html_url'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('root','remote','tag','commit'):p.add_argument('--'+k,required=True)
    a=p.parse_args();run(a.root,a.remote,a.tag,a.commit)
