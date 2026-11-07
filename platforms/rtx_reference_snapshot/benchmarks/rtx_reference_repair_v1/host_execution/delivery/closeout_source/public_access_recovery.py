"""Retain post-publication stale-draft-URL failure; verify current public asset."""
import datetime,hashlib,json,os,pathlib,shutil,subprocess,urllib.request
base=pathlib.Path('D:/rtx158');out=base/'publication02';assert not out.exists();out.mkdir()
tag='rtx-reference-repair-v1-evidence-20261102';repo='leecdiang/HeteroSpec'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
assert read(base/'operations/FINISH_TRANSPORT01.json')['exit_code']==0
assert read(base/'publication01/PUBLISH.json')['exit_code']==0
assert read(base/'operations/PUBLISH_DELIVERY01.json')['exit_code']==1
args=['gh','api',f'repos/{repo}/releases/430960706']
p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,GODEBUG='http2client=0'),timeout=120)
save(out/'RELEASE.json',{'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0
r=json.loads(p.stdout);assert not r['draft'] and r['tag_name']==tag
asset=next(e for e in r['assets'] if e['name']=='RAW_ACCESS.json');raw=base/'archive01/RAW_ACCESS.json'
assert asset['state']=='uploaded' and asset['size']==raw.stat().st_size and asset['digest']=='sha256:'+sha(raw)
url=asset['browser_download_url'];assert url==f'https://github.com/{repo}/releases/download/{tag}/RAW_ACCESS.json'
dest=out/'RAW_ACCESS.json'
with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'HeteroSpec-evidence-readback'}),timeout=300) as response,dest.open('xb') as f:
    status=response.status
    while True:
        block=response.read(4*1024*1024)
        if not block:break
        f.write(block)
assert status==200 and dest.stat().st_size==raw.stat().st_size and sha(dest)==sha(raw)
result={'status':'ANONYMOUS_PUBLIC_INDEX_READBACK_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release_url':r['html_url'],'release_id':r['id'],'asset_count':len(r['assets']),'index_url':url,'index_bytes':dest.stat().st_size,'index_sha256':sha(dest),'http_status':status,'method':'Fresh anonymous HTTPS download using the published release current asset URL, normal certificate verification, no authorization header or local substitution. Full raw and metadata readback preceded publication.','native_requests_added':0,'recovery':'Publication01 PUBLISH succeeded; subsequent URL assertion used a cached draft /untagged- URL and failed before anonymous download. All failure records retained. This fresh attempt fetches current published metadata; no release or asset mutation.','source_sha256':sha(pathlib.Path(__file__))}
save(out/'PUBLIC_ACCESS_READBACK.json',result)
target=base/'publication01/PUBLIC_ACCESS_READBACK.json';assert not target.exists();shutil.copy2(out/'PUBLIC_ACCESS_READBACK.json',target)
save(out/'RECEIPT_LOCATION.json',{'derived_copy':str(target),'source':str(out/'PUBLIC_ACCESS_READBACK.json'),'sha256':sha(target),'note':'New receipt only; initial failed publication records are unchanged.'})
print('ANONYMOUS_PUBLIC_INDEX_READBACK_PASS',len(r['assets']),sha(dest))
