"""Synthetic CPU actors; their records are inputs, never self-attested PASS."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--case',choices=['C1','C2','C3'],required=True);p.add_argument('--role',default='root',choices=['root','child','grandchild']);p.add_argument('--nonce',required=True);a=p.parse_args();root=Path(a.root)
def write(name,**kw):
    with (root/name).open('x',encoding='utf-8') as f:json.dump(dict(pid=os.getpid(),parent_pid=os.getppid(),nonce=a.nonce,**kw),f);f.write('\n');f.flush();os.fsync(f.fileno())
def child(role):
    return subprocess.Popen([sys.executable,'-B',str(Path(__file__).resolve()),'--root',str(root),'--case',a.case,'--role',role,'--nonce',a.nonce],stdin=subprocess.DEVNULL,creationflags=0x8)
if a.case=='C3' and a.role!='grandchild':child('child' if a.role=='root' else 'grandchild')
write(a.role+'.ready.json',event='READY');print('READY',a.role,a.nonce,flush=True)
if a.case=='C1':time.sleep(1);write('COMPLETE.json',event='COMPLETE');print('COMPLETE',a.nonce,flush=True)
elif a.case=='C2':time.sleep(30);write('LATE_WORK.json',event='UNEXPECTED_LATE_WORK')
elif a.role=='root':
    deadline=time.perf_counter()+60
    while time.perf_counter()<deadline:
        control=root/'CRASH_GO.json'
        if control.exists():
            data=json.loads(control.read_text());assert data['nonce']==a.nonce;os._exit(7)
        time.sleep(.01)
    os._exit(70)
else:time.sleep(60)
