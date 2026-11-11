"""Bounded37-request supervisor. Default is offline verification, never inference."""
import argparse,collections,ctypes,datetime,json,os,shutil,sqlite3,subprocess,time,traceback
from pathlib import Path
from common import HERE,RUNTIME,OLD,ORIGINAL,LOCK,read,put,sha,canonical,now,inherit,source_check
from check_output import Check

UUID='GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd'
SCHEME=b'381b4222-f694-41f0-9685-ff5bb260df2e'

class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
class Power(ctypes.Structure):
    _fields_=[('ac',ctypes.c_ubyte),('flag',ctypes.c_ubyte),('percent',ctypes.c_ubyte),('status',ctypes.c_ubyte),('life',ctypes.c_ulong),('full',ctypes.c_ulong)]
def sample():
    m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    p=Power();assert ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(p))
    raw=subprocess.check_output(['nvidia-smi','--query-gpu=uuid,memory.free,temperature.gpu,clocks.current.graphics,power.draw,utilization.gpu','--format=csv,noheader,nounits'],text=True,timeout=10).strip();x=[v.strip() for v in raw.split(',')];assert len(x)==6
    return dict(utc=now(),uuid=x[0],gpu_free=int(x[1])*1024**2,temperature_C=x[2],clock_MHz=x[3],power_W=x[4],utilization_pct=x[5],
        ram_free=m.available,C_free=shutil.disk_usage('C:/').free,D_free=shutil.disk_usage('D:/').free,ac=p.ac,raw_gpu_query=raw)
def resource(s):
    assert s['uuid']==UUID and s['ac']==1,'GPU identity/AC admission failed'
    assert s['gpu_free']>=128*1024**2 and s['ram_free']>=4*1024**3 and s['C_free']>=10*1024**3 and s['D_free']>=20*1024**3,'Resource floor failed'
def power_mode():assert SCHEME in subprocess.check_output(['powercfg','/getactivescheme']),'Existing power mode changed; do not change it automatically'
def competing():
    s=subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name','--format=csv,noheader'],text=True,timeout=10).strip()
    assert not s,('Competing GPU compute process; no launch or foreign process interruption',s)

def identity(j):
    inherit();source_check();assert sha(j['exe'])==j['exe_sha256'] and sha(j['build'])==j['build_sha256']
    b=read(j['build'])
    for name,h in b['modules'].items():assert sha(Path(j['exe']).parent/name)==h
    for role in ('target','draft'):assert sha(j['job'][role+'_model'])==j['job'][role+'_sha256']
    assert canonical(j['job'])==j['native_job_sha256']

def module_check(j,meta):
    expected={n.lower():h for n,h in read(j['build'])['modules'].items()};drivers=read(ORIGINAL/'DRIVER_MODULE_PINS.json')['pins'];rows={}
    for phase in ('modules_before','modules_after'):
        assert phase in meta
        for x in meta[phase]:
            name=Path(x['path']).name.lower();want=expected.get(name)
            if name in drivers:want=drivers[name]['sha256']
            if name=='worker.exe':want=j['exe_sha256']
            if want:assert x['sha256']==want and sha(x['path'])==want,('Loaded numerical module changed',x)
        rows[phase]=meta[phase]
    assert any(Path(x['path']).name.lower()=='ggml-cuda.dll' for x in meta['modules_after'])
    assert meta['GPU_device']=='NVIDIA GeForce RTX 5070 Ti Laptop GPU'
    return rows

def reserve(db,j):
    inherit();db.execute('BEGIN IMMEDIATE')
    try:
        req,rows,count=db.execute('SELECT COALESCE(SUM(requests),0),COALESCE(SUM(rows),0),COUNT(*) FROM attempts').fetchone()
        assert count<16 and req+j['requests']<=37 and rows+j['rows']<=18543
        assert 463+req+j['requests']<=512 and 1775+req+j['requests']<=2048
        assert 2679+req+j['requests']<=3072 and 2854298+rows+j['rows']<=4000000
        db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?,?,?)',(j['id'],'qualification',j['requests'],j['rows'],'RESERVED',time.time(),None,None));db.commit()
    except BaseException:db.rollback();raise

def execute(db,j):
    start=time.monotonic();folder=RUNTIME/'runs'/j['id'];folder.mkdir(parents=True,exist_ok=False);reserve(db,j)
    put(folder/'JOB.json',j);put(folder/'JOB_NATIVE.json',j['job']);proc=None;status='FAILED';code=None;launch=None;end=None
    try:
        identity(j);power_mode();resource(sample());competing()
        env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))};env.update(TEMP=str(RUNTIME/'temp'),TMP=str(RUNTIME/'temp'))
        with (folder/'stdout.log').open('xb') as out,(folder/'stderr.log').open('xb') as err,(folder/'resources.jsonl').open('x',encoding='utf8') as telemetry:
            launch=time.monotonic();proc=subprocess.Popen([j['exe'],str(folder/'JOB_NATIVE.json'),str(folder/'native')],stdout=out,stderr=err,env=env,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
            put(folder/'OWNED_PROCESS.json',dict(pid=proc.pid,exe=j['exe'],job=j['id'],utc=now()))
            while proc.poll() is None:
                assert time.monotonic()-launch<900,'Native worker timeout900s'
                s=sample();telemetry.write(json.dumps(s)+'\n');telemetry.flush();resource(s);time.sleep(2)
            end=time.monotonic();code=proc.returncode;assert code==0,('Native worker failed',code)
        meta=read(folder/'native/result.json');assert meta['status']=='COMPLETE' and meta['trajectories']==j['requests'] and meta['token_rows']<=j['rows']
        modules=module_check(j,meta);put(folder/'ACTUAL_MODULES.json',modules)
        put(folder/'COMPLETE.json',dict(actual_requests=meta['trajectories'],actual_rows=meta['token_rows'],reserved_requests=j['requests'],reserved_rows=j['rows'],refunds=0))
        status='COMPLETE';return folder/'native'
    except BaseException as e:
        if proc is not None and proc.poll() is None:proc.kill();proc.wait(timeout=30);end=time.monotonic();code=proc.returncode
        put(folder/'SUPERVISOR_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc(),new_references_or_retry_allowed=False,owned_process_only=True));raise
    finally:
        put(folder/'HOST.json',dict(status=status,code=code,wrapper_seconds=time.monotonic()-start,worker_observed_seconds=end-launch if end is not None and launch is not None else None,
            timeout_seconds=900,reservations_refunded=False,clock_scope='Inclusive overlapping windows; not clean performance data'))
        db.execute('UPDATE attempts SET status=?,ended=?,code=? WHERE id=?',(status,time.time(),code,j['id']));db.commit()

def preflight():
    plan=read(HERE/'EXECUTION_PLAN.json');auth=read(HERE/'EXECUTION_AUTHORIZATION.json');receipt=read(HERE/'FREEZE_READBACK.json')
    assert auth['GPU_requests_authorized']==37 and auth['formal_timing_rerun_authorized'] is False and receipt['passed']
    assert plan['status']=='AUTHORIZED_EXACT_37_NOT_EXECUTED' and plan['budget']['new_logical_requests']==37
    assert receipt['execution_source_binding_sha256']==sha(HERE/'EXECUTION_SOURCE_BINDINGS.json')
    inherit();source_check();assert not RUNTIME.exists(),'Existing supplemental output must be retained; no automatic reuse/retry'
    assert not LOCK.exists(),'Cooperative mutex occupied; wait without disturbing owner'
    s=sample();resource(s);power_mode();competing();assert s['C_free']>=read(HERE/'RESOURCE_DRAFT.json')['conservative_C_admission_free_bytes']
    return plan,s

def run():
    plan,s=preflight();RUNTIME.mkdir();(RUNTIME/'temp').mkdir();put(RUNTIME/'ADMISSION.json',dict(passed=True,utc=now(),initial_resource=s,
        source_binding_sha256=sha(HERE/'EXECUTION_SOURCE_BINDINGS.json'),freeze_readback=read(HERE/'FREEZE_READBACK.json'),exact_plan_sha256=sha(HERE/'EXECUTION_PLAN.json'),old_ledgers_read_only=True))
    owned=False;db=None;started=time.monotonic()
    try:
        with LOCK.open('x',encoding='utf8') as f:json.dump(dict(pid=os.getpid(),epoch='rtx213-supplement-s1',work=str(RUNTIME)),f)
        owned=True;db=sqlite3.connect(RUNTIME/'ledger.sqlite');db.execute('PRAGMA synchronous=FULL');db.execute('CREATE TABLE attempts(id TEXT PRIMARY KEY,stage TEXT,requests INTEGER,rows INTEGER,status TEXT,started REAL,ended REAL,code INTEGER)');db.commit()
        check=Check()
        for j in plan['jobs'][:8]:execute(db,j);print('REFERENCE_WORKER_COMPLETE',j['id'],flush=True)
        check.bank_ready();print('REFERENCE_BANK_COMPLETE vectors257 states40',flush=True)
        proofs=[]
        for j in plan['jobs'][8:]:
            execute(db,j);proof=check.candidate(j);proofs.append(proof);print('CANDIDATE_CHECKED',j['id'],'boundary_cycles',len(proof['boundary_cycles']),flush=True)
        assert len(proofs)==8
        put(RUNTIME/'COMPLETE_QUALIFICATION.json',dict(passed=True,new_reference_cases=29,new_heavy_requests=8,new_logical_requests=37,
            all_eight_arms=True,all_prebound_vectors_and_states=True,counts=dict(check.counts),wall_seconds=time.monotonic()-started,
            original_performance_data_unchanged=True,old_clean_state_recovered=False,blind_confirmation=False))
        put(RUNTIME/'RAW_FILES_READ.json',check.reader.seen)
        print('SUPPLEMENT_COMPLETE37 all8 native/state checks passed',flush=True)
    except BaseException as e:
        put(RUNTIME/'STOPPED.json',dict(utc=now(),error=repr(e),traceback=traceback.format_exc(),no_automatic_retry=True,remaining_slots_not_filled=True,wall_seconds=time.monotonic()-started));raise
    finally:
        if db:db.close()
        if owned:
            token=read(LOCK);assert token['pid']==os.getpid() and token['work']==str(RUNTIME);LOCK.unlink()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',action='store_true');a=p.parse_args()
    if a.run:run()
    else:print('Offline-only entry point. --run requires explicit authorization, published freeze/readback and resource admission; no model launched.',flush=True)
