from pathlib import Path
import json,hashlib,subprocess,os,datetime
root=Path('E:/rtx160/transport01');out=root/'incomplete_asset01';out.mkdir();ops=Path('D:/rtx160/operations');env=dict(os.environ,GODEBUG='http2client=0')
assert json.loads((ops/'UPLOAD05.json').read_text(encoding='utf-8'))['exit_code']==1
args=['gh','api','repos/leecdiang/HeteroSpec/releases/assets/703257477']
r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=env,timeout=120);(out/'BEFORE.json').write_text(json.dumps({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf-8');assert r.returncode==0
asset=json.loads(r.stdout);name='evidence-169.zip';assert asset['id']==703257477 and asset['name']==name and asset['state']=='starter' and asset.get('digest') is None
index=json.loads(Path('F:/rtx160/archive01/RAW_ACCESS.json').read_text(encoding='utf-8'));pin=next(x for x in index['parts'] if x['name']==name);local=Path('F:/rtx160/archive01')/name;h=hashlib.sha256()
with local.open('rb') as f:
 for block in iter(lambda:f.read(4194304),b''):h.update(block)
assert local.stat().st_size==pin['bytes']==asset['size'] and h.hexdigest()==pin['sha256']
receipt={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'action':'Remove only the bound incomplete starter upload so the immutable complete local shard can be uploaded. No completed asset is removed.','asset':asset,'local_pin':pin,'all_previous_uploads_settled':True,'original_raw_and_archive_retained':True,'native_requests_added':0}
(out/'AUTHORIZATION_AND_BINDING.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
args=['gh','api','--method','DELETE','repos/leecdiang/HeteroSpec/releases/assets/703257477'];r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=env,timeout=120);(out/'DELETE.json').write_text(json.dumps({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf-8');assert r.returncode==0
print('ONLY_BOUND_STARTER_ASSET_REMOVED_COMPLETE_LOCAL_BYTES_RETAINED')
