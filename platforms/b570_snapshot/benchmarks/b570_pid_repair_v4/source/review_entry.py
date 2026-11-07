"""An explicit review-only observer command; no default actor resource profile."""
import argparse,json,sys
from pathlib import Path
import subprocess
sys.path.insert(0,str(Path(__file__).resolve().parent))
from observer_policy import profile

def command(root,run_id,seconds,argv,python):
    profile('review',seconds)
    if not argv:raise ValueError('missing reviewer command')
    return [str(python),'-I','-B',str(root/'source/observe.py'),'--root',str(root),
            '--id',run_id,'--seconds',str(seconds),'--kind','review','--',*argv]

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--id',required=True)
    p.add_argument('--seconds',type=float,default=900);p.add_argument('argv',nargs=argparse.REMAINDER);a=p.parse_args()
    root=Path(a.root).resolve()
    if root!=Path(__file__).resolve().parents[1]:raise ValueError('review entry root')
    argv=a.argv[1:] if a.argv[:1]==['--'] else a.argv
    cmd=command(root,a.id,a.seconds,argv,Path(sys.executable).resolve())
    # The OS observer owns the deadline and descendant cleanup; tool wait time is not a deadline.
    result=subprocess.run(cmd,cwd=root)
    return result.returncode
if __name__=='__main__':sys.exit(main())
