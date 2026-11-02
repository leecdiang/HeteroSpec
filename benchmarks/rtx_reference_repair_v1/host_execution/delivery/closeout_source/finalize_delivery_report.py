"""Write final report only from completed publication and remote readback receipts."""
import datetime,hashlib,json,pathlib,shutil
base=pathlib.Path('D:/rtx158');repo=pathlib.Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr158')
report=repo/'benchmarks/rtx_reference_repair_v1/host_execution';out=report/'delivery'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
public=read(base/'publication03/PUBLISHED_ACCESS_READBACK.json')
assert public['status']=='AUTHENTICATED_PUBLISHED_INDEX_READBACK_PASS'
index=read(base/'archive01/RAW_ACCESS.json');remote=read(base/'remote01/REMOTE_READBACK.json')
assert remote['status']=='REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS'
assert sha(base/'archive01/RAW_ACCESS.json')==public['index_sha256']==remote['raw_index_sha256']
assert not out.exists(),'fresh final delivery records';out.mkdir()
sources=[base/'upload02/UPLOAD.json',base/'remote01/REMOTE_READBACK.json',base/'delivery01/DELIVERY_ASSETS.json',base/'delivery01/METADATA_MEMBERS.json',base/'delivery_remote01/DELIVERY_METADATA_READBACK.json',base/'receipt_remote01/RECEIPT_ASSET_READBACK.json',base/'publication03/PUBLISHED_ACCESS_READBACK.json']
for name in ('UPLOAD_HANDOFF01','UPLOAD_HANDOFF01_COMPLETE','STREAM_UPLOAD01','ARCHIVE01','PARALLEL_UPLOAD02','REMOTE_VERIFY01','DELIVERY_METADATA01','DELIVERY_METADATA_UPLOAD01','DELIVERY_METADATA_VERIFY01','DELIVERY_RECEIPT_UPLOAD01','DELIVERY_RECEIPT_VERIFY01','FINISH_TRANSPORT01','PUBLISH_DELIVERY01','PUBLIC_ACCESS02','PUBLISHED_ACCESS03'):
    p=base/'operations'/(name+'.json');assert p.exists(),p;sources.append(p)
for p in sources:shutil.copy2(p,out/p.name)
save(report/'RAW_ACCESS.json',{'status':'PUBLISHED_REMOTE_ALL_MEMBERS_VERIFIED','release_url':public['release_url'],'full_index_url':public['index_url'],'full_index_sha256':public['index_sha256'],'full_index_bytes':public['index_bytes'],'file_count':len(index['files']),'uncompressed_bytes':sum(e['bytes'] for e in index['files']),'archive_bytes':sum(e['bytes'] for e in index['parts']),'parts':index['parts'],'remote_uploaded':True,'same_host_fresh_remote_readback':True,'authenticated_published_index_readback':True,'anonymous_public_index_readback':False,'repository_visibility':'private','external_reader_verified':False,'native_source_snapshot':'0ccedc064214c7a758564bd6be1aa9a0c81bcb99','note':'Existing private repository access is required; permissions unchanged. The immutable packaging index retains remote_uploaded=false as its packaging-time status. Later receipts establish delivery. No third-party replication is claimed.'})
status=read(report/'STATUS.json');status.update(status='COMPLETE_NATIVE_AUDIT_AND_REMOTE_DELIVERY',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),result_pr=159,result_pr_url='https://github.com/leecdiang/HeteroSpec/pull/159',delivery='PUBLISHED_ALL_MEMBERS_REMOTE_VERIFIED',release_url=public['release_url'],repository_visibility='private',notes='Native gates and all576 timing/warmups complete; independent audit complete; all raw shards and members freshly downloaded and verified, transport metadata separately verified, published index freshly verified with repository authorization. Existing private access unchanged; anonymous404 and stale draft-URL assertion retained. Practical QB/PQ layout screen remains false. All failures and1140/1200 cumulative charges retained. No further experiments queued.')
status.pop('planned_confirmation',None);status.pop('projected_total',None);save(report/'STATUS.json',status)
delivery=(report/'DELIVERY.md').read_text(encoding='utf-8')
old='Native execution and independent raw reconstruction are complete. Transport\nverification is pending at this source snapshot. The final result PR will replace\nthis status with the actual release, access index and fresh remote readback receipts.'
assert old in delivery
new=f'''Native execution, independent raw reconstruction and remote delivery are complete.
The [published evidence release]({public['release_url']}) accompanies
[Draft result PR159](https://github.com/leecdiang/HeteroSpec/pull/159).
There are {len(index['parts'])} raw ZIP shards containing {len(index['files'])} files
({sum(e['bytes'] for e in index['files'])} uncompressed bytes;
{sum(e['bytes'] for e in index['parts'])} archive bytes). Every shard was freshly
downloaded; archive size/SHA256, exact inventory and every decompressed member's
size/SHA256 passed. All separate transport metadata assets and ZIP members also
passed fresh remote readback. After publication the raw index was additionally
downloaded with repository authorization and normal HTTPS certificate verification.
The repository is private: authorized readers are required, and its permissions
were not changed. Anonymous availability is not claimed.

[RAW_ACCESS.json](RAW_ACCESS.json) pins the full remote index and every shard.
Full index SHA256: `{public['index_sha256']}`.
The immutable full index retains its packaging-time `remote_uploaded=false`;
[UPLOAD.json](delivery/UPLOAD.json) and
[REMOTE_READBACK.json](delivery/REMOTE_READBACK.json) establish subsequent success.
See [metadata readback](delivery/DELIVERY_METADATA_READBACK.json),
[receipt readback](delivery/RECEIPT_ASSET_READBACK.json), and
[published access verification](delivery/PUBLISHED_ACCESS_READBACK.json).
TRANSPORT_METADATA.zip, METADATA_MEMBERS.json and DELIVERY_ASSETS.json on the release
retain and pin the transfer sources, handoff and per-part receipts. The native/source
archive is pinned to commit `0ccedc064214c7a758564bd6be1aa9a0c81bcb99`; later transport
code and delivery reports are separate commits in the result PR. No native request
was added during transport.

Two closeout failures are retained: publication succeeded, but the first checker
asserted against a cached draft asset URL; the next anonymous download returned404
because the repository is private. A fresh post-publication authenticated index
download passed. These are access/reporting corrections, not missing raw evidence
or scientific retries. Logs, receipts and corrected closeout source accompany this PR.'''
delivery=delivery.replace(old,new).replace('with512MiB','with 512MiB')
(report/'DELIVERY.md').write_text(delivery,encoding='utf-8')
p=report/'RESULTS.md';text=p.read_text(encoding='utf-8');text=text.replace('Remote release/access and fresh all-member readback receipts are documented in\n[DELIVERY.md](DELIVERY.md) after delivery completes.','The published release, raw access index and successful fresh all-member remote\nreadback receipts are documented in [DELIVERY.md](DELIVERY.md).');p.write_text(text,encoding='utf-8')
body=read(base/'operations/RESULT_PR_CREATED.json')['body'];before=body.index('Evidence delivery is in progress:')
body=body[:before]+f'''Evidence delivery is complete: [published raw evidence]({public['release_url']}) contains {len(index['parts'])} raw ZIP shards / {len(index['files'])} files. Every archive and decompressed member passed local and fresh remote size/SHA256 checks. Separate transport metadata and its members were freshly downloaded and verified; published RAW_ACCESS.json was freshly downloaded with authorization and hash-checked. The repository remains private and requires authorized reader access. The stale draft-URL assertion and anonymous404 closeout attempts are retained. Raw native/source snapshot is0ccedc064214c7a758564bd6be1aa9a0c81bcb99; later transport receipts are separately pinned in the release and this PR. Same-host readback is not third-party scientific replication. No further model experiments are queued.'''
(base/'operations/RESULT_PR_FINAL_BODY.md').write_text(body,encoding='utf-8')
print('FINAL_DELIVERY_REPORT_WRITTEN',len(index['parts']),len(index['files']))
