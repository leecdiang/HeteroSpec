"""Observe a change in ordered prefix identity and subsequent native reuse."""
from experiment import *
def check():
    fam='smol';C=4096;h=252;width=8
    p=dict(B=256,head=h,q=width);records={}
    for role,a in [('reference-reuse','S1'),('candidate-reuse','QB'),('candidate-reuse','WB')]:
        s=slot(fam,C,p,a,True,True);s.update(ids=sequences(fam)[h:h+32],step=width,ub=1 if a=='S1' else width)
        name=f'reuse-{role}-{a}'
        n=run(name,role,job(fam,C,[s],dispatch=a!='S1'),allow_failure=True)
        if n.get('records'):
            r=n['records'][0];records[a]=dict(calls=r['trace_calls'],vectors=r['vectors'])
    for a in ('QB','WB'):
        if a in records:records[a]['equal']=records[a]['vectors']==records['S1']['vectors']
    put_once(ROOT/'REUSE.json',records)
if __name__=='__main__':check()

