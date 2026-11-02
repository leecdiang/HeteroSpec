"""Verify published evidence within the repository's existing private access policy."""
import datetime,hashlib,json,os,pathlib,subprocess
base=pathlib.Path('D:/rtx158');out=base/'publication03';assert not out.exists();out.mkdir()
repo='leecdiang/HeteroSpec';tag='rtx-reference-repair-v1-evidence-20261102';env=dict(os.environ,GODEBUG='http2client=0')
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def run(name,args):
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=env,timeout=600)
    save(out/(name+'.json'),{'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0,name
    return p.stdout
assert read(base/'operations/FINISH_TRANSPORT01.json')['exit_code']==0
assert read(base/'publication01/PUBLISH.json')['exit_code']==0
repository=json.loads(run('REPOSITORY',['gh','api',f'repos/{repo}']))
assert repository['private'] and repository['visibility']=='private'
release=json.loads(run('RELEASE',['gh','api',f'repos/{repo}/releases/430960706']))
assert not release['draft'] and release['tag_name']==tag
raw=base/'archive01/RAW_ACCESS.json';asset=next(e for e in release['assets'] if e['name']==raw.name)
assert asset['state']=='uploaded' and asset['size']==raw.stat().st_size and asset['digest']=='sha256:'+sha(raw)
run('DOWNLOAD',['gh','release','download',tag,'--repo',repo,'--dir',str(out),'--pattern',raw.name])
download=out/raw.name;assert download.stat().st_size==raw.stat().st_size and sha(download)==sha(raw)
failure=base/'operations/PUBLIC_ACCESS02.log'
assert 'HTTP Error 404: Not Found' in failure.read_text(encoding='utf-8') and read(base/'operations/PUBLIC_ACCESS02.json')['exit_code']==1
save(out/'PUBLISHED_ACCESS_READBACK.json',{'status':'AUTHENTICATED_PUBLISHED_INDEX_READBACK_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release_url':release['html_url'],'release_id':release['id'],'asset_count':len(release['assets']),'index_url':asset['browser_download_url'],'index_bytes':download.stat().st_size,'index_sha256':sha(download),'repository_private':True,'repository_visibility':'private','anonymous_access':False,'anonymous_attempt_http_status':404,'anonymous_attempt_log_sha256':sha(failure),'native_requests_added':0,'source_sha256':sha(pathlib.Path(__file__)),'method':'Fresh authenticated download after publication, normal TLS, size/SHA256 equal to immutable index. Earlier full raw and metadata fresh remote readback passed. Repository visibility and permissions were not changed. Authorized repository readers are required; no anonymous/public availability or third-party replication claimed.','retained_closeout_failures':['PUBLISH_DELIVERY01: publish succeeded; cached draft-URL assertion failed before download.','PUBLIC_ACCESS02: actual published URL returned anonymous404 because repository is private.']})
print('AUTHENTICATED_PUBLISHED_INDEX_READBACK_PASS',len(release['assets']),sha(download))
