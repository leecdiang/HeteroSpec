"""One bounded real user-systemd resource check; standard-library CPU only.

Creates only uniquely named transient units beneath the existing user manager.
Never loads a model/backend, opens a GPU device or invokes a native worker.
"""
import argparse
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import time


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, sort_keys=True, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())


def worker(out, mode):
    root = Path(out)
    cg = next(x[3:] for x in Path('/proc/self/cgroup').read_text().splitlines() if x.startswith('0::'))
    base = Path('/sys/fs/cgroup') / cg.lstrip('/')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or (base/'memory.max').read_text().strip() != '67108864' or (base/'pids.max').read_text().strip() != '8':
        raise RuntimeError('actual resource domain or empty CPU visibility differs')
    if mode == 'normal':
        child = os.fork()
        if child == 0:
            while True: time.sleep(1)
        write(root/'normal-ready.json', dict(pid=os.getpid(),child=child,cgroup=cg,
              memory_max=(base/'memory.max').read_text(),pids_max=(base/'pids.max').read_text(),
              child_cgroup=Path('/proc',str(child),'cgroup').read_text(),native_calls=0))
        while True: time.sleep(1)
    write(root/'oom-ready.json',dict(pid=os.getpid(),cgroup=cg,native_calls=0))
    # Confined64MiB domain; force a real kernel allocation failure in this CPU unit.
    value=bytearray(128*1024*1024)
    for i in range(0,len(value),4096): value[i]=1
    raise RuntimeError('allocation unexpectedly survived the kernel limit')


def main(out):
    root=Path(out)
    if not root.is_absolute() or root.exists(): raise RuntimeError('fresh output required')
    root.mkdir(mode=0o700)
    own_units=[]; receipts=[]
    def run(args):
        r=subprocess.run(args,capture_output=True,text=True,timeout=8)
        return dict(argv=args,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
    try:
        for mode in ('normal','oom'):
            unit='hs-p4-cpu-'+str(time.time_ns())+'-'+mode+'.service'
            own_units.append(unit)
            cmd=['systemd-run','--user','--unit='+unit,'--property=MemoryMax=67108864',
                '--property=MemorySwapMax=0','--property=TasksMax=8','--property=RuntimeMaxSec=15',
                '--property=KillMode=control-group','--property=TimeoutStopSec=2','--property=OOMPolicy=stop',
                '--setenv=CUDA_VISIBLE_DEVICES=','/usr/bin/python3','-I',str(Path(__file__).resolve()),
                '--worker',mode,'--out',str(root)]
            launch=run(cmd)
            if launch['returncode']: raise RuntimeError('existing user manager cannot start bounded unit: '+str(launch))
            end=time.monotonic()+6
            ready=root/(mode+'-ready.json')
            while not ready.exists() and time.monotonic()<end: time.sleep(.02)
            if not ready.exists(): raise RuntimeError('CPU unit did not report readiness')
            identity=json.loads(ready.read_text()); base=Path('/sys/fs/cgroup')/identity['cgroup'].lstrip('/')
            fds=[]
            for pid in [identity['pid']]+([identity['child']] if mode=='normal' else []):
                try: fds.append(os.pidfd_open(pid,0))
                except ProcessLookupError:
                    if mode=='normal': raise
            entry=dict(mode=mode,unit=unit,launch=launch,identity=identity,
                kernel_limits={},events_seen=[],native_calls=0)
            for name in ('memory.max','memory.swap.max','pids.max','memory.current','pids.current','cgroup.procs'):
                try: entry['kernel_limits'][name]=(base/name).read_text()
                except FileNotFoundError: entry['kernel_limits'][name]='REMOVED_AFTER_EXIT'
            if mode=='normal':
                if set(map(int,entry['kernel_limits']['cgroup.procs'].split())) != {identity['pid'],identity['child']}:
                    raise RuntimeError('unknown member in new owned CPU domain')
                entry['stop']=run(['systemctl','--user','stop',unit])
                if entry['stop']['returncode']: raise RuntimeError('owned unit stop failed')
            end=time.monotonic()+6
            while time.monotonic()<end:
                try: entry['events_seen'].append((base/'memory.events').read_text())
                except FileNotFoundError: pass
                state=run(['systemctl','--user','show',unit,'--property=ActiveState','--property=Result','--property=ExecMainCode','--property=ExecMainStatus','--property=ControlGroup'])
                inactive = any(x in state['stdout'].splitlines() for x in ('ActiveState=inactive','ActiveState=failed'))
                empty = not (base/'cgroup.procs').exists() or not (base/'cgroup.procs').read_text().strip()
                exited = all(bool(select.select([f],[],[],0)[0]) for f in fds)
                if inactive and empty and exited: break
                time.sleep(.02)
            entry['final_unit']=state
            entry['all_held_pidfds_exited']=all(bool(select.select([f],[],[],0)[0]) for f in fds)
            entry['domain_empty_or_removed']=not (base/'cgroup.procs').exists() or not (base/'cgroup.procs').read_text().strip()
            for f in fds: os.close(f)
            write(root/(mode+'-observed.json'),entry)
            if not entry['all_held_pidfds_exited'] or not entry['domain_empty_or_removed']:
                raise RuntimeError('owned CPU domain exit/release not confirmed')
            if mode=='oom' and 'Result=oom-kill' not in state['stdout']:
                raise RuntimeError('no actual kernel OOM evidence')
            receipts.append(entry)
            write(root/(mode+'-receipt.json'),entry)
        write(root/'RESULT.json',dict(status='PASS_REAL_KERNEL_CPU_ISOLATION_AND_OWNED_CLEANUP',
              checks=receipts,GPU_contexts=0,models=0,placements=0,forwards=0,
              limitation='systemd pre-exec domain placement observed; no native launcher integration or GPU isolation proof'))
    except BaseException as e:
        write(root/'STOP.json',dict(status='BLOCKED_REAL_CPU_CHECK',reason=str(e),completed=receipts,native_calls=0))
        raise
    finally:
        # Only units newly created by this invocation; no old/unknown unit touched.
        for unit in own_units:
            run(['systemctl','--user','stop',unit])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--worker',choices=('normal','oom'))
    a=p.parse_args()
    if a.worker: worker(a.out,a.worker)
    else: main(a.out)
