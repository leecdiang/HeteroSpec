"""Capture on/off and repeated request/reset bridge on four exposed probes."""
from common import *
def main():
    tasks=read(PUB/'BRIDGE_INPUTS.json');conditions=read(REPO/'docs/experiments/jsa_rtx_validation_20261010/DESIGN.json')['S']['conditions']
    root=LOCAL/'runs/S_bridge';root.mkdir(parents=True,exist_ok=False)
    save(root/'START.json',{'utc':now(),'source_commit':head(),'formal':False,'planned_requests':32,'warmups':8})
    for capture in [False,True]:
        for c in conditions:
            d=root/('capture-'+str(int(capture))+'-'+c['name']);print('START',d.name,flush=True)
            with Server(d,c,capture) as s:
                for t in tasks:
                    slot=d.name+'|'+t['id'];r=measure(s,t,slot);save(d/(t['id'].replace('/','-')+'.json'),r);print('DONE',slot,flush=True)
    save(root/'COMPLETE.json',{'utc':now(),'requests':32,'warmups':8})
if __name__=='__main__':main()
