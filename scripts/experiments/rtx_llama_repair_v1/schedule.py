"""Natural Llama matrices and six-period Williams counterbalancing."""
from __future__ import annotations
import argparse, hashlib
from lr_common import *
ARMS={'R':('R',1,1,False,False,0),'M_PQ':('PQ',1,4,True,False,0),
      'M_QB':('QB',0,4,True,False,0),'C_PQ':('PQ',1,4,True,True,3),
      'C_QB':('QB',0,4,True,True,3)}
LABELS=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB')
WILLIAMS=(0,1,5,2,4,3)

def make(panel,i,arm,producer,observer,category,name,**extra):
    x=panel['inputs'][i];input_check(x);native='C_PQ' if arm in ('C_PQ_A','C_PQ_B') else arm
    scope,selector,ub,scoped,draft,k=ARMS[native]
    return dict(schema=1,study_id=STUDY,family='Llama',slot_id=name,source_index=i,
      input_id=x['id'],prompt_ids_sha256=x['prompt_ids_sha256'],arm=native,experiment_arm=arm,
      scope=scope,layout_selector=selector,target_ub=ub,target_outputs=ub,scoped_target=scoped,
      draft_enabled=draft,k=k,lifecycle='fresh',observer=observer,producer='NATIVE',category=category,
      repair={'prefill':producer,'trace':{'mode':'off'}},llama_diag={'mode':'off'},**extra)

def development(panel):
    need(len(panel['inputs'])==3,'failure plus both retained controls')
    recipes=(('R','native'),('R','reference'),('M_PQ','native'),('M_QB','native'),('C_PQ','native'),('C_QB','native'))
    return [make(panel,i,a,p,o,'development',f'dev/i{i:02d}/{a}/{p}/{o}')
      for i in range(3) for a,p in recipes for o in ('off','heavy')]

def qualification(panel,policy):
    need(policy.get('prefill') in ('native','reference'),'uniform prefill policy')
    return [make(panel,i,a,'native' if a=='R' else policy['prefill'],o,'qualification',f'held/i{i:02d}/{a}/{o}')
      for i in range(len(panel['inputs'])) for a in ARMS for o in ('off','heavy')]

def original_references(panel):
    out=[make(panel,i,'R','native',o,'qualification',f'oracle/i{i:02d}/R/{o}')
      for i in range(len(panel['inputs'])) for o in ('off','heavy')]
    # This is the old executable's real registered protocol, not a new oracle.
    for s in out:s['study_id']='rtx_scope_transfer_v1'
    return out

def timing(panel,policy,session,seed='llama-repair-williams-v1'):
    n=len(panel['inputs']);need(n>=12 and n%6==0,'panel count must be a positive multiple of six, >=12')
    need(type(session) is int and 0<=session<6,'six registered periods')
    labels=sorted(LABELS,key=lambda a:hashlib.sha256((seed+'|arm|'+a).encode()).digest())
    inputs=sorted(range(n),key=lambda i:hashlib.sha256(f'{seed}|input|{session}|{i}'.encode()).digest())
    out=[]
    for i in inputs:
        row=(session+i)%6;order=[labels[(x+row)%6] for x in WILLIAMS]
        for a in order:
            for category in ('warmup','measured'):
                out.append(make(panel,i,a,'native' if a=='R' else policy['prefill'],'off',category,
                  f'formal/s{session}/i{i:02d}/{a}/{category}',session=session))
    return out

def probe(panel,i,arm,cycle,mode='pair',trace=False,pair_order='scalar-first'):
    need(arm in ('C_PQ','C_QB') and type(cycle) is int and cycle>=0,'probe a real verification cycle')
    need(mode in ('checkpoint','pair'),'probe mode');need(pair_order in ('scalar-first','batch-first'),'pair order')
    s=make(panel,i,arm,'native','heavy','diagnostic',f'diag/i{i:02d}/{arm}/cycle{cycle}/{mode}/{pair_order}/trace{int(trace)}')
    s['llama_diag']={'mode':mode,'cycle':cycle,'pair_order':pair_order,'max_state_bytes':512*1024**2}
    if trace:s['repair']['trace']={'mode':'tensors','phases':['VERIFY'],
      'name_regex':r'^(l_out|result_norm|result_output)(-[0-9]+)?$','max_files':4096,'max_bytes':2*1024**3}
    return s

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['development','qualification','oracle','timing','probe'])
    p.add_argument('--panel',required=True);p.add_argument('--policy');p.add_argument('--session',type=int,default=0)
    p.add_argument('--input',type=int,default=0);p.add_argument('--arm',default='C_QB');p.add_argument('--cycle',type=int)
    p.add_argument('--trace',action='store_true');p.add_argument('--out',required=True)
    a=p.parse_args();pan=read(a.panel);pol=read(a.policy) if a.policy else {'prefill':'native'}
    if a.kind=='development':out=development(pan)
    elif a.kind=='qualification':out=qualification(pan,pol)
    elif a.kind=='oracle':out=original_references(pan)
    elif a.kind=='timing':out=timing(pan,pol,a.session)
    else:out=[probe(pan,a.input,a.arm,a.cycle,trace=a.trace)]
    save(a.out,out,exclusive=True);print('slots',len(out))
