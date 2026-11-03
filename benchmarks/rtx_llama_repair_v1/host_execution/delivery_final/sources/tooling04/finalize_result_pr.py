"""Finalize result docs and draft PR only after authenticated published evidence passes."""
import datetime,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
root=Path('E:/rtx160/transport01');ops=Path('D:/rtx160/operations');repo=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160');code=repo/'benchmarks/rtx_llama_repair_v1/host_execution';env=dict(os.environ,GODEBUG='http2client=0',PYTHONUTF8='1')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,j):
 with p.open('x',encoding='utf-8') as f:json.dump(j,f,indent=2)
def run(name,args):
 subprocess.run([sys.executable,'-B',str(ops/'run_logged.py'),name,*map(str,args)],cwd=repo,env=env,check=True)
deadline=datetime.datetime.fromisoformat(read(root/'TRANSPORT_RESOURCE_POLICY02.json')['overall_deadline_utc'])
receipt=ops/'DELIVERY_AUTO_PUBLISH02.json'
while not receipt.exists():
 assert datetime.datetime.now(datetime.timezone.utc)<deadline,'finite cumulative final delivery wait expired'
 time.sleep(5)
assert read(receipt)['exit_code']==0,'Publication gate failed; no final PASS or PR edit'
publication=read(root/'publication01/PUBLICATION.json');assert publication['status']=='PUBLISHED_PRIVATE_RELEASE_AND_AUTHENTICATED_INDEX_READBACK_PASS'
index_path=Path('F:/rtx160/archive01/RAW_ACCESS.json');index=read(index_path);index_sha=sha(index_path)
assert publication['raw_index_sha256']==index_sha
assert read(root/'remote01/REMOTE_READBACK.json')['status']=='REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS'
assert read(root/'delivery_remote01/DELIVERY_METADATA_READBACK.json')['status']=='DELIVERY_METADATA_FRESH_REMOTE_READBACK_PASS'
assert read(root/'receipt_remote01/RECEIPT_ASSET_READBACK.json')['status']=='RECEIPT_ASSET_FRESH_REMOTE_READBACK_PASS'
final=code/'delivery_final';final.mkdir(exist_ok=False);records=final/'records';records.mkdir();sources=final/'sources';sources.mkdir()
for folder in sorted(root.glob('tooling*')):shutil.copytree(folder,sources/folder.name)
for foldername in ['delivery01','delivery_remote01','receipt_remote01','publication01']:
 folder=root/foldername
 for f in sorted(folder.iterdir()):
  if f.is_file() and f.suffix in ('.json','.log') and f.name!='RAW_ACCESS.json':
   target=records/foldername/f.name;target.parent.mkdir(exist_ok=True);shutil.copy2(f,target)
for relative in ['upload05/UPLOAD.json','remote01/REMOTE_READBACK.json']:
 f=root/relative;target=records/relative;target.parent.mkdir(exist_ok=True);shutil.copy2(f,target)
for f in sorted(root.iterdir()):
 if f.is_file() and f.suffix in ('.json','.log','.md'):shutil.copy2(f,records/f.name)
for f in sorted(ops.glob('*.json')):
 if not f.name.startswith(('PACK','UPLOAD','REMOTE','DELIVERY','TRANSPORT','PUBLISH','GIT_BYTE','RESULT_PR')):continue
 if 'exit_code' not in read(f):continue
 for source in [f,f.with_suffix('.log')]:
  if source.exists():
   target=records/'operations'/source.name;target.parent.mkdir(exist_ok=True);shutil.copy2(source,target)
report={'status':'COMPLETE_RAW_SOURCE_AND_METADATA_REMOTE_READBACK_AND_PUBLICATION_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'result_pr':'https://github.com/leecdiang/HeteroSpec/pull/162','release_url':publication['release_url'],'release_id':431658377,'scientific_snapshot':'70086c63af202cd844a3062eff3929218152f73c','git_byte_fidelity_successor':'e11d2b75d82422409ba2b701aa38c59f36acc50b','raw_index_sha256':index_sha,'part_count':len(index['parts']),'file_count':len(index['files']),'archive_bytes':sum(p['bytes'] for p in index['parts']),'asset_count':publication['asset_count'],'repository_private':True,'native_requests_added':0,'pr_remains_draft':True,'merge_performed':False,'manuscript_edited':False,'scope':'Final delivery attestation supersedes only creation-time pending-delivery flags in the immutable scientific snapshot. Scientific results and the negative performance screen remain unchanged. Same-host transport verification is not third-party scientific replication.'}
save(code/'FINAL_DELIVERY.json',report)
entries=[{'path':f.relative_to(final).as_posix(),'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(final.rglob('*')) if f.is_file()];save(final/'FILES.json',entries)
release=publication['release_url'];assets='https://github.com/leecdiang/HeteroSpec/releases/download/rtx-llama-repair-v1-evidence-20261102/'
p=code/'RESULTS.md';text=p.read_text(encoding='utf-8');assert text.count('## Delivery')==1
text=text[:text.index('## Delivery')]+f"""## Delivery

Independent draft result PR: https://github.com/leecdiang/HeteroSpec/pull/162. [Complete evidence release]({release}) is published in the unchanged private repository. All **{len(index['parts'])} shards and {len(index['files']):,} members** passed local readback and fresh authenticated remote download with exact archive/member inventory, byte counts and SHA-256 checks. Separate transport metadata and its final receipt were also uploaded, freshly downloaded and verified.

[RAW_ACCESS.json]({assets}RAW_ACCESS.json) SHA-256: `{index_sha}`. Compressed raw/source archive size: **{report['archive_bytes']:,} bytes**. [REMOTE_READBACK.json]({assets}REMOTE_READBACK.json), [delivery metadata readback]({assets}DELIVERY_METADATA_READBACK.json), FINAL_DELIVERY.json and delivery_final/ provide the final attestations. RESTORE.md gives independent reconstruction commands. No model weights are redistributed.

The sealed scientific snapshot remains `70086c63af202cd844a3062eff3929218152f73c`; its raw index binds actual executed source bytes. The later Git byte-fidelity commit `e11d2b75d82422409ba2b701aa38c59f36acc50b` disables EOL conversion and restores three tokenizer evidence receipts hidden by the pre-existing token* ignore rule. All 202 scientific receipts and staged study source bytes were checked. This changed no working numerical source, frozen candidate, original reference, panel, raw capsule or scientific result. Earlier commits, failed delivery checks and network attempts remain retained in the transport metadata and delivery records.

FINAL_EXECUTION_SUMMARY.json remains an immutable creation-time scientific report; FINAL_DELIVERY.json supersedes its then-pending delivery field. Same-host upload/download checks establish byte delivery, not third-party scientific replication. No merge or manuscript edit is performed. PAPER_ADDENDUM.md retains the supported scope and limitations, including the failed practical performance screen.
"""
p.write_text(text,encoding='utf-8')
p=code/'RESTORE.md';text=p.read_text(encoding='utf-8');old='The final release index and transport receipts will be linked in RESULTS.md after upload and fresh remote verification. Until then, no remote delivery is claimed.';assert text.count(old)==1
text=text.replace(old,f'Complete evidence is published at [the Llama repair release]({release}). All {len(index["parts"])} shards / {len(index["files"]):,} members and separate transport metadata passed fresh authenticated remote readback. Start with [RAW_ACCESS.json]({assets}RAW_ACCESS.json), SHA-256 `{index_sha}`; RESULTS.md and FINAL_DELIVERY.json link the attestations. Repository access controls are unchanged.');p.write_text(text,encoding='utf-8')
run('DELIVERY_FINAL_STAGE01',['git','add','--',str(final),str(code/'FINAL_DELIVERY.json'),str(code/'RESULTS.md'),str(code/'RESTORE.md')])
for e in entries:
 path=final/e['path'];b=subprocess.run(['git','show',':'+path.relative_to(repo).as_posix()],cwd=repo,capture_output=True,check=True).stdout;assert len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256']
run('DELIVERY_FINAL_DIFF01',['git','diff','--cached','--check'])
run('DELIVERY_FINAL_COMMIT01',['git','-c','user.name=leecdiang','-c','user.email=162876606+leecdiang@users.noreply.github.com','commit','-m','Complete evidence delivery and fresh all-member remote verification'])
run('DELIVERY_FINAL_PUSH01',['git','-c','http.version=HTTP/1.1','push','origin','codex/pr160-llama-repair'])
head=subprocess.run(['git','rev-parse','HEAD'],cwd=repo,capture_output=True,text=True,check=True).stdout.strip()
old=read(ops/'RESULT_PR_FETCH02.log')['body'];assert '**Delivery in progress:**' in old
body=old[:old.index('**Delivery in progress:**')]+f"""**Delivery complete:** [Full raw/source evidence release]({release}), {len(index['parts'])} shards / {len(index['files']):,} members, {report['archive_bytes']:,} compressed bytes. Every raw shard/member, separate transport metadata and final receipt passed fresh authenticated remote download/readback. [Raw index]({assets}RAW_ACCESS.json) SHA-256 `{index_sha}`; [remote readback]({assets}REMOTE_READBACK.json); [metadata readback]({assets}DELIVERY_METADATA_READBACK.json). FINAL_DELIVERY.json and delivery_final/ bind final receipts and sources. Access remains private; this is same-host delivery verification, not third-party replication.

The immutable raw capsule binds actual executed bytes. Git byte-fidelity successor e11d2b75d82422409ba2b701aa38c59f36acc50b disables EOL filtering and includes three tokenizer evidence receipts previously hidden by token* ignore. Original working numerical sources, references, frozen panel and scientific results are unchanged. All earlier failures/commits and network recovery attempts remain preserved. This PR remains draft; no merge or manuscript edit.
"""
request=root/'FINAL_PR_UPDATE.json';save(request,{'body':body})
run('RESULT_PR_FINAL_UPDATE01',['gh','api','repos/leecdiang/HeteroSpec/pulls/162','--method','PATCH','--input',str(request)])
run('RESULT_PR_FINAL_VERIFY01',['gh','api','repos/leecdiang/HeteroSpec/pulls/162'])
pr=read(ops/'RESULT_PR_FINAL_VERIFY01.log');assert pr['draft'] and pr['state']=='open' and pr['head']['sha']==head and pr['body']==body
save(root/'FINAL_CLOSEOUT.json',{'status':'COMPLETE_DELIVERY_AND_DRAFT_RESULT_PR_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':head,'result_pr':pr['html_url'],'release_url':release,'raw_index_sha256':index_sha,'native_requests_added':0,'merged':False})
print('COMPLETE_DELIVERY_AND_DRAFT_RESULT_PR_VERIFIED',flush=True)
