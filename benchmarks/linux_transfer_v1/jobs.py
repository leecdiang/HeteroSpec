"""Outcome-free independent-deployment panel, using fixed prior transfer inputs.

These are exposed transfer roots, NOT new unseen inputs. No speed-based arm pruning.
Plans/jobs are written once before their Linux confirmation outputs exist.
"""
from __future__ import annotations
import argparse, hashlib, random
from pathlib import Path
from common import need, read, save, sha
ARMS={
 'W_L4_M':('loop4','SIMPLE',False,'target_only'),
 'W_P_M':('packed','SIMPLE',False,'target_only'),
 'L_L4_M':('loop4','LOCAL',False,'target_only'),
 'L_P_M':('packed','LOCAL',False,'target_only'),
 'W_L4_D4':('loop4','SIMPLE',True,'matched'),
 'L_P_D4':('packed','LOCAL',True,'matched')}

def panel(inputs,primers,models,out):
    source=read(inputs);roots=source['inputs'];pre=read(primers)['inputs'];models=read(models)
    need(len(roots)==16 and len({x['id'] for x in roots})==16,'Use all16 frozen transfer roots')
    need(len(pre)==2 and len({x['id'] for x in pre})==2,'Two distinct exposed primers required')
    need(not {x['id'] for x in roots}&{x['id'] for x in pre},'Primer/test overlap')
    need(all(x.get('family')=='Qwen' and len(x['prompt_ids'])+132<=1024 and x['cap']==128 for x in roots+pre),'Preserve source contract and capacity')
    need(sha(models['target_model'])==models['target_sha256'] and sha(models['draft_model'])==models['draft_sha256'],'Pinned local models')
    out=Path(out);need(not out.exists(),'Fresh plan directory');out.mkdir(parents=True)
    arms=list(ARMS);workers=[]
    for session in range(4):
        order=arms[session:]+arms[:session];rs=list(roots);random.Random(19620261107+session).shuffle(rs)
        for arm in order:
            core,cut,draft,residency=ARMS[arm];name=f's{session}-{arm}'
            job=dict(models,family='Qwen',n_ctx=1024,threads=models.get('threads',8),lowering=cut,draft=draft,draft_width=4 if draft else 1,residency=residency,profile=False,
                inputs=[{'name':f'request-{i}','input':r,'capture':False} for i,r in enumerate(pre+rs)])
            if residency=='target_only':job.pop('draft_model');job.pop('draft_sha256')
            save(out/(name+'.json'),job)
            workers.append({'id':name,'session':session,'arm':arm,'core':core,'job':name+'.json','job_sha256':sha(out/(name+'.json')),
                            'roots':[r['id'] for r in rs],'primers':[r['id'] for r in pre]})
    save(out/'PLAN.json',{'schema':'linux-transfer.panel.v1','input_sha256':sha(inputs),'primer_sha256':sha(primers),'workers':workers,
      'arms':arms,'roots':sorted(r['id'] for r in roots),'sessions':4,'formal_requests':384,'primers':48,
      'order_design':'Four predeclared cyclic rows, not a full six-arm Williams design',
      'sample_status':'Previously exposed Windows roots; independent Linux deployment transfer, not unseen-input confirmation',
      'primary':[('L_P_D4',a) for a in arms[:4]]+[('L_P_D4','W_L4_D4')],
      'bootstrap_seed':19620261107,'bootstrap_draws':10000,'family_size':5,'linux_results_seen_at_plan_creation':'MUST_BE_ZERO_HOST_ATTESTATION'})

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('inputs','primers','models','out'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();panel(a.inputs,a.primers,a.models,a.out)
