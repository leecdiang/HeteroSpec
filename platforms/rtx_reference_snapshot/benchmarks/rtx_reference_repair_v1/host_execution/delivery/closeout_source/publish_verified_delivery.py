"""Publish only after full fresh remote and metadata readback, then test anonymous access."""
import datetime,hashlib,json,os,pathlib,subprocess,urllib.request
base=pathlib.Path('D:/rtx158');ops=base/'operations';out=base/'publication01'
tag='rtx-reference-repair-v1-evidence-20261102';repo='leecdiang/HeteroSpec'
env=dict(os.environ,GODEBUG='http2client=0');release_id=430960706
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
assert not out.exists(),'fresh publication evidence';out.mkdir()
assert read(ops/'FINISH_TRANSPORT01.json')['exit_code']==0
raw=base/'archive01/RAW_ACCESS.json';index=read(raw);remote=read(base/'remote01/REMOTE_READBACK.json')
assert remote['status']=='REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS' and remote['raw_index_sha256']==sha(raw)
assert read(base/'receipt_remote01/RECEIPT_ASSET_READBACK.json')['status']=='RECEIPT_ASSET_FRESH_REMOTE_READBACK_PASS'
def command(name,args):
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=env,timeout=180)
    save(out/(name+'.json'),{'argv':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    assert p.returncode==0,name+' failed; no retry'
    return p.stdout
release= json.loads(command('BEFORE',['gh','api',f'repos/{repo}/releases/{release_id}']))
assert release['draft'] and release['tag_name']==tag and release['target_commitish']=='0ccedc064214c7a758564bd6be1aa9a0c81bcb99'
pages=json.loads(command('ASSETS',['gh','api','--paginate','--slurp',f'repos/{repo}/releases/{release_id}/assets?per_page=100']))
assets=[e for page in pages for e in page];byname={e['name']:e for e in assets};assert len(assets)==len(byname)
expected=list(index['parts'])
for p in [raw,*[base/'delivery01'/e['name'] for e in read(base/'delivery01/DELIVERY_ASSETS.json')['assets']],base/'delivery01/DELIVERY_ASSETS.json',base/'delivery_remote01/DELIVERY_METADATA_READBACK.json']:
    expected.append({'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)})
assert set(byname)=={e['name'] for e in expected},'Unexpected or absent remote assets'
for e in expected:
    a=byname[e['name']];assert a['state']=='uploaded' and a['size']==e['bytes'] and a['digest']=='sha256:'+e['sha256'],'Remote metadata mismatch: '+e['name']
notes=f'''Native Qwen3-14B Q8 reference repair and complete paired cost evidence for [Draft result PR #159](https://github.com/{repo}/pull/159), stacked on unchanged PR158.

Original R/model/panels are fixed. Qualification:120 requests; timing:288 measured +288 warmups. C_QB/R=0.3204513415. QB/PQ reduction2.611% is below the3.384% A/A threshold: practical layout benefit did not pass. All failures and slow blocks remain. Budget1140/1200, development420/480; original PR156's40 separate.

Raw evidence: {len(index['parts'])} ZIP shards, {len(index['files'])} files, {sum(e['bytes'] for e in index['files'])} uncompressed bytes. Every local archive member was checked; every remote ZIP was freshly downloaded and all members rehashed. RAW_ACCESS.json SHA256: `{sha(raw)}`. The immutable index's remote_uploaded=false describes packaging time; later UPLOAD.json and REMOTE_READBACK.json establish completed transport.

TRANSPORT_METADATA.zip retains transport sources, handoff records and upload/readback receipts. METADATA_MEMBERS.json and DELIVERY_ASSETS.json pin it; DELIVERY_METADATA_READBACK.json records fresh remote checks of all small assets and all metadata members. Same-host transport verification is not third-party scientific replication. Native/source snapshot:0ccedc064214c7a758564bd6be1aa9a0c81bcb99; final delivery records and source are in PR159. No weights, EXEs or DLLs are distributed. Existing papers and old PRs are not merged or rewritten.
'''
notesfile=out/'RELEASE_NOTES.md';notesfile.write_text(notes,encoding='utf-8')
command('PUBLISH',['gh','release','edit',tag,'--repo',repo,'--draft=false','--latest=false','--notes-file',str(notesfile)])
published=json.loads(command('AFTER',['gh','api',f'repos/{repo}/releases/{release_id}']))
assert not published['draft'] and published['tag_name']==tag
url=byname['RAW_ACCESS.json']['browser_download_url']
assert url==f'https://github.com/{repo}/releases/download/{tag}/RAW_ACCESS.json'
request=urllib.request.Request(url,headers={'User-Agent':'HeteroSpec-evidence-readback'})
dest=out/'RAW_ACCESS.json'
with urllib.request.urlopen(request,timeout=300) as response,dest.open('xb') as f:
    final_url=response.url;status=response.status
    while True:
        block=response.read(4*1024*1024)
        if not block:break
        f.write(block)
assert status==200 and dest.stat().st_size==raw.stat().st_size and sha(dest)==sha(raw),'Anonymous index readback mismatch'
save(out/'PUBLIC_ACCESS_READBACK.json',{'status':'ANONYMOUS_PUBLIC_INDEX_READBACK_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'release_url':published['html_url'],'release_id':release_id,'asset_count':len(expected),'index_url':url,'index_bytes':dest.stat().st_size,'index_sha256':sha(dest),'http_status':status,'method':'Fresh anonymous HTTPS download with normal certificate verification; no authorization header or local copy. Full raw/metadata remote readback preceded publication.','native_requests_added':0})
print('PUBLISHED_AND_ANONYMOUS_INDEX_VERIFIED',len(expected),flush=True)
