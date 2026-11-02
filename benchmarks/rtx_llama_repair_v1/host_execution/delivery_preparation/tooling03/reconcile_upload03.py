from pathlib import Path
import json,hashlib,subprocess,os,time,datetime,shutil
root=Path('E:/rtx160/transport01');out=root/'recovery03';out.mkdir();ops=Path('D:/rtx160/operations')
assert json.loads((ops/'UPLOAD03.json').read_text(encoding='utf-8'))['exit_code']==1
args=['gh','api','--paginate','--slurp','repos/leecdiang/HeteroSpec/releases/431658377/assets?per_page=100']
for attempt in range(1,4):
 r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,GODEBUG='http2client=0'),timeout=120)
 (out/('QUERY%02d.json'%attempt)).write_text(json.dumps({'argv':args,'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr},indent=2),encoding='utf-8')
 if r.returncode==0:break
 if attempt<3:time.sleep(5*attempt)
assert r.returncode==0
assets=[a for page in json.loads(r.stdout) for a in page];by={a['name']:a for a in assets};assert len(by)==len(assets)
prior=[json.loads(x) for x in (root/'upload03/UPLOADED_PARTS.jsonl').read_text(encoding='utf-8').splitlines()];known={p['name']:p for p in prior}
for line in (root/'upload03/COMMANDS.jsonl').read_text(encoding='utf-8').splitlines():
 e=json.loads(line)
 if all(k in e for k in ('name','bytes','sha256')):known[e['name']]={k:e[k] for k in ('name','bytes','sha256')}
assert set(by).issubset(known) and {p['name'] for p in prior}.issubset(by)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
pins=[]
for name,a in sorted(by.items()):
 p=known[name];f=Path('F:/rtx160/archive01')/name
 assert f.stat().st_size==p['bytes']==a['size'] and sha(f)==p['sha256'] and a['digest']=='sha256:'+p['sha256'] and a['state']=='uploaded'
 pins.append(p)
(out/'UPLOADED_PARTS.jsonl').write_text(''.join(json.dumps(p)+'\n' for p in pins),encoding='utf-8')
(out/'RECOVERY.json').write_text(json.dumps({'status':'ALL_REMOTE_ASSETS_LOCAL_AND_SERVER_SHA256_VERIFIED','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'asset_count':len(pins),'assets':assets,'failed_asset_absent':'evidence-031.zip' not in by,'prior_upload_receipt_sha256':sha(ops/'UPLOAD03.json'),'all_inflight_settled':True,'native_requests_added':0},indent=2),encoding='utf-8')
shutil.copy2(ops/'UPLOAD03.json',root/'UPLOAD03.json')
print('RECONCILED',len(pins))
