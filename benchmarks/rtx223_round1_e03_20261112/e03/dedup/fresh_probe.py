from pathlib import Path
import ctypes as C,struct,json,datetime,hashlib,sqlite3,shutil,subprocess
HERE=Path(__file__).resolve().parent
BASE=HERE.parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
nt=C.WinDLL('ntdll',use_last_error=True)
f=nt.NtQuerySystemInformation
f.argtypes=[C.c_ulong,C.c_void_p,C.c_ulong,C.POINTER(C.c_ulong)];f.restype=C.c_long
size=1024*1024;ret=C.c_ulong()
for _ in range(8):
    buf=C.create_string_buffer(size);status=f(5,buf,size,C.byref(ret))
    if status!=-1073741820:break
    size=max(size*2,ret.value+65536)
rows=[]
if status>=0:
    base=C.addressof(buf);off=0
    while off<ret.value:
        nxt,threads=struct.unpack_from('<II',buf,off);nbytes=struct.unpack_from('<H',buf,off+56)[0];ptr=struct.unpack_from('<Q',buf,off+64)[0];pid,ppid=struct.unpack_from('<QQ',buf,off+80)
        if nbytes and not base<=ptr<=base+ret.value-nbytes:raise RuntimeError('invalid process string pointer')
        name=C.string_at(ptr,nbytes).decode('utf-16-le') if nbytes else ''
        rows.append({'pid':pid,'ppid':ppid,'name':name})
        if not nxt:break
        off+=nxt
paths=[Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock'),BASE/'rtx221-round1-20261112/resources/WINDOWS_RTX_EPOCH.lock',Path('D:/rtx192-review-v2/ledger.sqlite'),Path('D:/rtx211-q8-20261109/ledger.sqlite'),BASE/'q8rtx213-supplement-runtime-20261109/ledger.sqlite',BASE/'rtx221-round1-20261112/resources/ledger.sqlite',BASE/'rtx223-round1-resume-20261112-e02/continuation/safety/runtime/family-ledger.sqlite']
files=[{'path':str(p),'exists':p.exists(),'bytes':p.stat().st_size if p.exists() else None,'sha256':sha(p) if p.exists() else None} for p in paths]
family=paths[-1];dst=HERE/'private/e02-family.sqlite';shutil.copy2(family,dst)
db=sqlite3.connect('file:'+str(dst).replace('\\','/')+'?mode=ro',uri=True);tables=db.execute("select name from sqlite_master where type='table'").fetchall();state={}
for (t,) in tables:
    if t in ('attempts','family_window','family','windows','budgets','state'):
        state[t]={'rows':db.execute('select count(*) from "'+t+'"').fetchone()[0]}
db.close()
res={'observed_utc':now(),'nt_status':hex(status&0xffffffff),'process_count':len(rows),'relevant_processes':[x for x in rows if any(v in x['name'].lower() for v in ('worker','llama','python','nvcc','zig'))],'process_scope':'Restricted namespace, not verified host-wide','files':files,'canonical_family_table_counts':state,'new_model_requests':0,'new_GPU_launches':0,'nvidia_smi':[]}
for args in (['nvidia-smi','--id=GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd','--query-gpu=index,uuid,name,memory.total,memory.used,driver_version','--format=csv'],['nvidia-smi','--id=GPU-6dd57db3-9aac-ccc8-bd69-225a5ea2c4dd','--query-compute-apps=pid,process_name,used_memory','--format=csv']):
    r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);res['nvidia_smi'].append({'argv':args,'code':r.returncode,'output':r.stdout.decode('utf8',errors='replace')})
(HERE/'FRESH_PROCESS_LOCK_LEDGER.json').write_text(json.dumps(res,indent=2),encoding='utf8');print(json.dumps(res,indent=2))
