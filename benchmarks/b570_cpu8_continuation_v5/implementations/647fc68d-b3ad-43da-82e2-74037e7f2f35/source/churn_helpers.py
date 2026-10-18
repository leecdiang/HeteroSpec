"""Bounded CPU-only real process churn; PID reuse is observed, never assumed."""
import argparse,json,os,subprocess,sys
p=argparse.ArgumentParser();p.add_argument('--children',type=int,default=200);a=p.parse_args()
if not 1<=a.children<=200:raise ValueError('children bound')
for index in range(a.children):
    result=subprocess.run([sys.executable,'-I','-B','-c','import os; print(os.getpid())'],capture_output=True,text=True,timeout=5,check=True,creationflags=getattr(subprocess,'DETACHED_PROCESS',0))
    print(json.dumps(dict(index=index,pid=int(result.stdout.strip()),parent_pid=os.getpid())),flush=True)
print(json.dumps(dict(status='CHURN_COMPLETE',children=a.children)),flush=True)
