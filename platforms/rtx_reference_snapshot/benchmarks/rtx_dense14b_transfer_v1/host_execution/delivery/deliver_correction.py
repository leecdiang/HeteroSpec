import datetime,hashlib,json,os,subprocess,time,zipfile
from pathlib import Path
base=Path('D:/rtx155');out=base/'correction_remote_readback';out.mkdir(exist_ok=False)
env=dict(os.environ,GODEBUG='http2client=0');tag='rtx-dense14b-transfer-v1-evidence-20261101';repo='leecdiang/HeteroSpec'
names=['CLOSEOUT_CORRECTION_V2.zip','CLOSEOUT_CORRECTION_V2_MANIFEST.json'];commands=[]
def run(args):
    start=time.monotonic();p=subprocess.Popen(args,env=env);code=p.wait();commands.append({'argv':args,'pid':p.pid,'seconds':time.monotonic()-start,'exit_code':code});assert code==0
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
run(['gh','release','upload',tag,*[str(base/n) for n in names],'--repo',repo])
args=['gh','release','download',tag,'--repo',repo,'--dir',str(out)]
for n in names:args+=['--pattern',n]
run(args)
for n in names:assert digest(out/n)==digest(base/n)
m=json.loads((out/names[1]).read_text());assert digest(out/m['archive'])==m['sha256']
with zipfile.ZipFile(out/m['archive']) as z:
    assert sorted(z.namelist())==sorted(f['path'] for f in m['files'])
    for f in m['files']:
        data=z.read(f['path']);assert len(data)==f['bytes'] and hashlib.sha256(data).hexdigest()==f['sha256']
r={'status':'CORRECTION_V2_REMOTE_READBACK_PASS','verification_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':commands,'files':[{'name':n,'sha256':digest(out/n),'bytes':(out/n).stat().st_size} for n in names],'members_verified':len(m['files']),'native_requests_added':0,'method':'Fresh authenticated remote download on same physical host, hash and every member verified; no local substitution.'}
(base/'CORRECTION_REMOTE_READBACK.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
