from pathlib import Path
import hashlib,json,subprocess,time
HERE=Path(__file__).resolve().parent
OLD=HERE/'actual-trace-v1'
OUT=HERE/'actual-trace-link-v2';OUT.mkdir(exist_ok=False)
old=json.loads((OLD/'link-PRE.json').read_bytes())
argv=[x for x in old['argv'] if x.lower()!='/verbose:lib']
argv=[('/map:'+str(OUT/'fixture.map')) if x.lower().startswith('/map:') else ('/out:'+str(OUT/'never-executed.exe')) if x.lower().startswith('/out:') else x for x in argv]
argv.insert(2,'/verbose')
def record(path):
    p=Path(path).resolve();d=p.read_bytes();return {'path':str(p),'bytes':len(d),'sha256':hashlib.sha256(d).hexdigest()}
inputs=[record(x['path']) for x in old['inputs']]+[record(__file__)]
(OUT/'PRE.json').write_text(json.dumps({'argv':argv,'inputs':inputs,'scope':'fresh link-only CPU trace fixture; prior compile/archive inputs retained'},indent=2),encoding='utf8')
start=time.monotonic();r=subprocess.run(argv,cwd=OUT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);(OUT/'link.log').write_bytes(r.stdout)
after=[record(x['path']) for x in inputs]
(OUT/'POST.json').write_text(json.dumps({'returncode':r.returncode,'seconds':time.monotonic()-start,'inputs_equal':inputs==after,'log_sha256':hashlib.sha256(r.stdout).hexdigest(),'models':0,'GPU_launches':0,'EXE_execution':False},indent=2),encoding='utf8')
print(json.dumps({'returncode':r.returncode,'trace':r.stdout.decode('utf8',errors='replace')},indent=2))
if r.returncode or inputs!=after:raise SystemExit(1)
