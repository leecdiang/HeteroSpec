"""Bounded native old-R/observer bridge; all starts share the global ledger."""
from pathlib import Path
import json,subprocess,time,shutil,os,ctypes
from runner import Ledger,kill_owned
from build_host import OLD,ROOT,sha,put
ADMIT=OLD.parent/'admission-Qwen-v4'
LIMITS=dict(requests=8192,token_rows=16000000,operators=8192)
class Memory(ctypes.Structure):
    _fields_=[('length',ctypes.c_ulong),('load',ctypes.c_ulong)]+[(n,ctypes.c_ulonglong) for n in ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]
def execute(label,exe):
    out=ROOT/label;out.mkdir();panel=json.loads((ADMIT/'PANEL.json').read_bytes());slot=json.loads((ADMIT/'SLOTS.json').read_bytes())[0]
    slots=[]
    for i in range(2):
        s=dict(slot);s['slot_id']=f'r{i}';slots.append(s)
    binding=json.loads((ADMIT/'BINDING.json').read_bytes());binding['status']='FROZEN_BEFORE_FIRST_NATIVE_REQUEST';binding['families']['Qwen']['executable_sha256']=sha(exe)
    for name,data in [('PANEL.json',panel),('SLOTS.json',slots),('BINDING.json',binding),('PLAN.json',json.loads((ADMIT/'PLAN.json').read_bytes()))]:put(out/name,data)
    ledger=Ledger(ROOT/'ledger.sqlite',LIMITS);ledger.reserve(label,dict(requests=2,token_rows=16000,operators=0));p=None;owned=False;start=time.monotonic();code=None;status='FAILED'
    lock=Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock');samples=[]
    try:
        with lock.open('x') as f:json.dump(dict(pid=os.getpid(),job=label),f)
        owned=True
        cmd=[str(exe),str(out/'native'),'D:/HeteroSpec-PC/models/gguf/Qwen3-8B-Q8_0.gguf','D:/HeteroSpec-PC/models/gguf/Qwen3-0.6B-Q8_0.gguf',str(out/'PANEL.json'),str(out/'SLOTS.json'),'Qwen',str(out/'BINDING.json'),str(out/'PLAN.json')]
        put(out/'launch.json',dict(argv=cmd,reservation=dict(requests=2,token_rows=16000,operators=0),wall_limit_s=600,disk_free_min=20*1024**3,ram_free_min=4*1024**3,exe_sha256=sha(exe)))
        with (out/'stdout.log').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
            env={k:v for k,v in os.environ.items() if not k.startswith(('HS_','GGML_','JSA_','HSC_'))}
            p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
            p.stdin.write(b'RUN\nCONTINUE\nCONTINUE\n');p.stdin.flush();p.stdin.close()
            while p.poll() is None:
                m=Memory();m.length=ctypes.sizeof(m);assert ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
                row=dict(seconds=time.monotonic()-start,disk_free=shutil.disk_usage(ROOT).free,ram_free=m.available);samples.append(row)
                if row['seconds']>600 or row['disk_free']<20*1024**3 or row['ram_free']<4*1024**3:raise RuntimeError('live resource limit reached')
                time.sleep(1)
            code=p.returncode
        if code:raise RuntimeError(f'native exit {code}')
        result=json.loads((out/'native/result.json').read_bytes());assert result['status']=='COMPLETE' and len(result['requests'])==2
        status='COMPLETE'
    except BaseException as e:put(out/'failure.json',dict(error=repr(e)));raise
    finally:
        if p is not None:kill_owned(p)
        if owned:lock.unlink()
        put(out/'resource-samples.json',samples);put(out/'exit.json',dict(status=status,code=code,seconds=time.monotonic()-start))
        ledger.finish(label,status,code);ledger.close()
if __name__=='__main__':
    execute('bridge-old-r-01',OLD/'bin/rtx-scope-transfer.exe')
    execute('bridge-observer-r-01',ROOT/'draft/reference-observer/bin/rtx-scope-transfer.exe')
