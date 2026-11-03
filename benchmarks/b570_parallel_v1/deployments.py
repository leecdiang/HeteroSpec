"""Re-admit with a saturating free-memory guard and keep deployment strata separate."""
from experiment import *
def gates():
    table=[]
    for fam,C in [('qwen',1024),('qwen',4096),('qwen',2048),('smol',4096),('qwen_target',4096)]:
        for role in ('reference-D','candidate-D'):
            ub=1 if role.startswith('reference') else 32
            for dual in ((False,) if fam=='qwen_target' else (True,False)):
                name=f'gate-D-{fam}-{C}-{role}-dual{int(dual)}'
                n=run(name,role,job(fam,C,[dict(kind='admit',ub=ub,draft_context=dual)],capacity_trace=True),allow_failure=True)
                table.append(dict(family=fam,C=C,role=role,dual=dual,status=n['status'],error=n.get('error'),unit=name))
    put_once(ROOT/'DEPLOYMENTS-D.json',table)
def admitted(f,C,dual=False):
    rr=[r for r in read(ROOT/'DEPLOYMENTS-D.json') if r['family']==f and r['C']==C and r['dual']==dual]
    return len(rr)==2 and all(r['status']=='COMPLETE' for r in rr)
def configs():
    out=[('qwen',1024)] if admitted('qwen',1024) else []
    full=next((c for c in (4096,2048) if admitted('qwen',c,True)),None)
    if full:out.append(('qwen',full))
    if (not full or full!=4096) and admitted('qwen_target',4096):out.append(('qwen_target',4096))
    if admitted('smol',4096):out.append(('smol',4096))
    return out
if __name__=='__main__':gates();print(configs())
