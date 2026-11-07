"""Local launch-return persistence witness; no model calls."""
import time
from prepare import *
from execution import identity

if __name__=='__main__':
    d=OUT/'detached-fixture';d.mkdir(parents=True,exist_ok=True)
    save(d/'START.json',{'pid':os.getpid(),'creation_identity':identity(os.getpid()),'utc':utc()})
    for i in range(3):
        time.sleep(10);save(d/'PROGRESS.json',{'step':i,'pid':os.getpid(),'utc':utc()})
    save(d/'COMPLETE.json',{'complete':True,'pid':os.getpid(),'creation_identity':identity(os.getpid()),'utc':utc()})
