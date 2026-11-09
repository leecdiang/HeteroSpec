"""Windows serial supervisor with durable cumulative, nonrefundable reservations."""
from pathlib import Path
import ctypes, datetime, hashlib, json, os, shutil, sqlite3, subprocess, time
from admission import HERE, ROOT, sha, put

WORK=Path('D:/rtx211-q8-20261109')
BASE=Path('D:/rtx192-review-v2')
LOCK=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock')
CEILINGS={'qualification':512,'diagnostic':160,'profiling':32,'live':1152,'closure':192}

class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]

class Power(ctypes.Structure):
    _fields_=[('ac',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('status',ctypes.c_ubyte),('life',ctypes.c_ulong),('full',ctypes.c_ulong)]

def sample():
    m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    p=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.free,temperature.gpu,clocks.current.graphics,power.draw,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip().split(',')
    return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),uuid=raw[0].strip(),gpu_free=int(raw[1])*1024**2,
        temperature_C=raw[2].strip(),clock_MHz=raw[3].strip(),power_W=raw[4].strip(),utilization_pct=raw[5].strip(),
        ram_free=m.available,output_free=shutil.disk_usage(WORK).free,system_free=shutil.disk_usage('C:/').free,ac=p.ac)

def resources(s):
    assert s['uuid']=='GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd'
    assert s['ac']==1,'AC power lost'
    assert s['gpu_free']>=128*1024**2 and s['ram_free']>=4*1024**3 and s['output_free']>=20*1024**3 and s['system_free']>=10*1024**3,'Resource reserve violation'

def execute(spec,manifest_name='JOB_MANIFEST_GEOMETRY.json'):
    stage=spec['stage'];assert stage in CEILINGS
    manifest_path=(ROOT/manifest_name).resolve();assert manifest_path.is_relative_to(ROOT.resolve())
    manifest=json.loads(manifest_path.read_bytes())
    assert spec in manifest['jobs'],'Job not frozen in admitted manifest'
    assert json.loads((ROOT/'WINDOWS_CLOSURE_AUDIT.json').read_bytes())['passed']
    inherited=json.loads((ROOT/'CUMULATIVE_LEDGER_INITIAL.json').read_bytes())
    assert sha(BASE/'ledger.sqlite')==inherited['sha256'],'RTX predecessor ledger changed'
    folder=WORK/'runs'/spec['id'];folder.mkdir(parents=True,exist_ok=False)
    db=sqlite3.connect(WORK/'ledger.sqlite');db.execute('PRAGMA synchronous=FULL');db.execute('CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY,stage TEXT,requests INTEGER,rows INTEGER,status TEXT,started REAL,ended REAL,code INTEGER)')
    try:
        db.execute('BEGIN IMMEDIATE')
        req,rows=db.execute('SELECT COALESCE(SUM(requests),0),COALESCE(SUM(rows),0) FROM attempts').fetchone()
        used=db.execute('SELECT COALESCE(SUM(requests),0) FROM attempts WHERE stage=?',(stage,)).fetchone()[0]
        assert req+spec['requests']<=2048 and used+spec['requests']<=CEILINGS[stage]
        assert inherited['totals']['requests']+req+spec['requests']<=3072
        assert inherited['totals']['token_rows']+rows+spec['rows']<=4000000
        db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)',(spec['id'],stage,spec['requests'],spec['rows'],'RESERVED',time.time(),None,None));db.commit()
    except BaseException:db.rollback();db.close();raise
    owned=False;proc=None;status='FAILED';code=None;started=time.monotonic()
    try:
        build=json.loads(Path(spec['build']).read_bytes());exe=Path(spec['exe'])
        assert sha(exe)==build['exe']==spec['exe_sha256']
        for name,digest in build['modules'].items():assert sha(exe.parent/name)==digest
        source=Path(manifest.get('source_binding',WORK/'SOURCE.json'));front=Path(manifest.get('frontend_root',WORK/'frontend'))
        assert sha(source)==manifest['source_sha256']
        sources=json.loads(source.read_bytes())['frontend']
        for name,digest in sources.items():assert sha(front/name)==digest
        for role in ('target','draft'):assert sha(spec['job'][role+'_model'])==spec['job'][role+'_sha256']
        resources(sample())
        competing=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True,timeout=10).strip()
        assert not competing,('Competing GPU compute process; no launch',competing)
        with LOCK.open('x',encoding='utf8') as f:json.dump(dict(pid=os.getpid(),job=spec['id'],work=str(WORK)),f)
        owned=True;put(folder/'JOB.json',spec);put(folder/'BUILD.json',build)
        cmd=[str(exe),str(folder/'JOB_NATIVE.json'),str(folder/'native')];put(folder/'JOB_NATIVE.json',spec['job'])
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))};env.update(TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'))
        with (folder/'stdout.log').open('xb') as out,(folder/'stderr.log').open('xb') as err,(folder/'resources.jsonl').open('x',encoding='utf8') as telemetry:
            proc=subprocess.Popen(cmd,stdout=out,stderr=err,env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            while proc.poll() is None:
                assert time.monotonic()-started<900,'Worker timeout900s'
                s=sample();telemetry.write(json.dumps(s)+'\n');telemetry.flush();resources(s);time.sleep(2)
            code=proc.returncode
        if 'expect_error' in spec:
            failure=json.loads((folder/'native/failure.json').read_bytes())
            assert code!=0 and spec['expect_error'] in failure['error'],('Expected native rejection failed',code,failure)
            put(folder/'EXPECTED_REJECT.json',dict(error=failure,expected=spec['expect_error'],logical_request_charged=True))
            status='EXPECTED_REJECT'
            return folder/'native'
        assert code==0,('Native failure retained',code)
        native=json.loads((folder/'native/result.json').read_bytes());assert native['status']=='COMPLETE'
        assert native['trajectories']==spec['requests'] and native['token_rows']<=spec['rows']
        modules={}
        for key in ('modules_before','modules_after'):
            modules[key]=[]
            for value in native[key]:
                p=Path(value['path'] if isinstance(value,dict) else value);h=sha(p);modules[key].append(dict(path=str(p),sha256=h))
                if p.name in build['modules']:assert h==build['modules'][p.name]
                elif p.name.lower().startswith(('ggml','cublas','cudart')):raise RuntimeError('Unbound numerical module '+str(p))
        put(folder/'ACTUAL_MODULES.json',modules)
        put(folder/'COMPLETE.json',dict(actual_requests=native['trajectories'],actual_rows=native['token_rows'],qualified=False))
        status='COMPLETE'
    except BaseException as e:
        put(folder/'FAILURE.json',dict(error=repr(e)));raise
    finally:
        if proc is not None and proc.poll() is None:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);proc.wait(timeout=30)
        if owned:LOCK.unlink()
        put(folder/'HOST.json',dict(status=status,code=code,wall_seconds=time.monotonic()-started,timeout_seconds=900,reservations_refunded=False))
        db.execute('UPDATE attempts SET status=?,ended=?,code=? WHERE id=?',(status,time.time(),code,spec['id']));db.commit();db.close()
    print(spec['id'],status,flush=True)
    return folder/'native'
