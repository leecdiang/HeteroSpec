"""Synthetic CPU review-helper tree, never a scientific workload."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',required=True);p.add_argument('--children',type=int,default=0)
    p.add_argument('--child',action='store_true');a=p.parse_args();folder=Path(a.folder)
    if a.child:
        (folder/(str(os.getpid())+'.ready')).write_text(str(os.getpid()))
        cutoff=time.monotonic()+15
        while not (folder/'STOP').exists() and time.monotonic()<cutoff:time.sleep(.02)
        return 0
    if not 1<=a.children<=32:raise ValueError('bounded child count')
    folder.mkdir(exist_ok=False)
    children=[]
    try:
        for i in range(a.children):
            children.append(subprocess.Popen([sys.executable,'-I','-B',str(Path(__file__).resolve()),'--folder',str(folder),'--child'],
                                            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
        cutoff=time.monotonic()+10
        while len(list(folder.glob('*.ready')))<a.children:
            if time.monotonic()>cutoff or any(c.poll() is not None for c in children):raise RuntimeError('helper readiness')
            time.sleep(.02)
        (folder/'ALL_READY.json').write_text(json.dumps(dict(children=a.children,pids=[c.pid for c in children])))
        time.sleep(3)
        (folder/'STOP').write_text('stop')
        for c in children:
            if c.wait(timeout=3)!=0:raise RuntimeError('helper nonzero')
        return 0
    finally:
        for c in children:
            if c.poll() is None:c.kill()
        for c in children:c.wait(timeout=3)
if __name__=='__main__':sys.exit(main())
