"""Use device-local Vulkan buffers; retain both model offloads, F16 KV and original kernels."""
from experiment import *
def probe():
    measures=[]
    for role,arm in [('reference-mem','S1'),('candidate-mem','QB')]:
        for C in (1024,4096):
            ub=1 if arm=='S1' else 32
            for dual in (True,False):
                name=f'localmem-{role}-{C}-dual{int(dual)}'
                adm=run(name,role,job('qwen',C,[dict(kind='admit',ub=ub,draft_context=dual)],capacity_trace=True,device_local=True),allow_failure=True)
                measures.append(dict(unit=name,status=adm['status'],min_free=adm.get('min_free_device')))
                if not dual and adm['status']=='COMPLETE':
                    base=256 if C==1024 else 1024;p=next(x for x in read(PLAN)[config('qwen',C)] if x['B']==base and x['q']==32 and len(x['groups'])==2)
                    s=slot('qwen',C,p,arm,True)
                    if arm=='S1':s['ub']=1
                    name=f'localmem-grid-{role}-{C}'
                    result=run(name,role,job('qwen',C,[s],capacity_trace=True,device_local=True),allow_failure=True)
                    measures.append(dict(unit=name,status=result['status'],min_free=result.get('min_free_device')))
    put_once(ROOT/'DEVICE_LOCAL_PROBE.json',measures)
if __name__=='__main__':probe()
