"""Registered development, untouched confirmation and matched timing plans."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from common import *

CANDIDATES=('M_PQ','M_QB','C_PQ','C_QB')
TIMING=('R','M_PQ','M_QB','C_PQ_A','C_PQ_B','C_QB')
ROW_GROUPS={'qkv','attn_out','ffn','lm_head'}
BUDGET={'development':272,'confirmation':288,'regression':64,'timing':576,'total':1200}

def policy(rows):
    need(isinstance(rows,str),'policy must be text')
    if rows=='off':return rows
    parts=rows.split(',');need(len(parts)==len(set(parts)) and set(parts)<=ROW_GROUPS and parts,'invalid row families')
    return ','.join(sorted(parts))

def input_check(x):
    ids=x.get('prompt_ids');need(isinstance(ids,list) and 0<len(ids)<=892,'prompt length')
    need(all(type(v) is int and 0<=v<151936 for v in ids),'prompt tokens')
    need(x.get('cap')==128 and x.get('prompt_ids_sha256')==hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),'prompt hash/cap')
    need(isinstance(x.get('id'),str) and x['id'],'input id')
    for k in ('text_sha256','source_revision','tokenization_receipt_sha256'):
        need(isinstance(x.get(k),str) and x[k],'missing '+k)
    if 'teacher_ids' in x:
        need(isinstance(x['teacher_ids'],list) and 0<len(x['teacher_ids'])<=128,'teacher trace must be a complete historical endpoint, at most128 IDs')
        need(all(type(v) is int and 0<=v<151936 for v in x['teacher_ids']),'teacher IDs')
    return x

def panel_check(panel,kind):
    need(kind in ('development','confirmation','regression'),'panel kind')
    xs=panel['inputs'];need(len(xs)==(4 if kind=='development' else 12) if kind!='regression' else bool(xs),'panel size')
    for x in xs:input_check(x)
    for k in ('id','text_sha256','prompt_ids_sha256'):need(len({x[k] for x in xs})==len(xs),'duplicate '+k)
    if kind!='development':need(not any('teacher_ids' in x for x in xs),'teacher forcing cannot be confirmation')
    if kind=='confirmation':
        need(panel.get('natural_inputs_only') is True,'natural inputs required')
        for domain in ('code','math'):
            for stratum,lo,hi in [('short',128,384),('long',512,768)]:
                group=[x for x in xs if (x.get('domain'),x.get('stratum'))==(domain,stratum)]
                need(len(group)==3 and all(lo<=len(x['prompt_ids'])<=hi for x in group),'unbalanced natural input strata')
    return panel

def spec(label):
    a='C_PQ' if label in ('C_PQ_A','C_PQ_B') else 'R' if label=='R_NEW' else label
    need(a in ('R',*CANDIDATES),'unknown arm')
    scope='R' if a=='R' else a.split('_')[1]
    return dict(arm=a,experiment_arm=label,scope=scope,layout_selector=0 if scope=='QB' else 1,
                scoped_target=a!='R',target_ub=1 if a=='R' else 4,target_outputs=1 if a=='R' else 4,
                draft_enabled=a.startswith('C_'),k=3 if a.startswith('C_') else 0)

def make_slot(x,i,label,kind,unit,producer='NATIVE',rows='off',session=0,cohort=None,trace=None):
    z=spec(label);cohort=cohort or ('reference' if label=='R' else 'repair')
    need(cohort in ('reference','repair'),'cohort')
    need(producer in ('NATIVE','P1','RSEED','BSEED','SELF'),'producer')
    need(not(cohort=='reference' and (label!='R' or producer!='NATIVE')),'historical executable only supplies native R')
    need(producer!='BSEED' or label=='R_NEW','BSEED is reference-consumer diagnosis only')
    if z['arm']=='R' and producer=='RSEED':raise ValueError('R cannot import itself as a different context')
    sid=f'{unit}/i{i:02d}/{label}/{kind}'
    return dict(schema=1,study_id=STUDY,family='Qwen',slot_id=sid,source_index=i,input_id=x['id'],
        prompt_ids_sha256=x['prompt_ids_sha256'],lifecycle='resident',observer='heavy' if kind=='heavy' else 'off',
        producer=producer if z['arm']!='R' or producer in ('SELF','BSEED') else 'NATIVE',category=kind,session=session,
        cohort=cohort,rows=policy(rows) if cohort=='repair' else 'off',trace=trace or {'mode':'metadata'},**z)

def development(panel,kind,attempt='v00',rows='off',trace=None,producer=None):
    panel_check(panel,'development');need(kind in ('baseline','p1','rseed','sham','cross','candidate','trace'),'development kind')
    arms=('R_NEW',*CANDIDATES) if kind=='baseline' else ('R_NEW',) if kind in ('sham','cross') else CANDIDATES
    prod={'baseline':'NATIVE','p1':'P1','rseed':'RSEED','sham':'SELF','cross':'BSEED','candidate':'RSEED','trace':'RSEED'}[kind]
    if kind in ('trace','candidate') and producer is not None:
        need(producer in ('NATIVE','P1','RSEED'),'diagnostic/candidate producer');prod=producer
    if kind=='trace':arms=('R_NEW','M_QB')
    out=[]
    for i,x in enumerate(panel['inputs']):
        for a in arms:
            for k in ('heavy','off'):
                out.append(make_slot(x,i,a,k,f'development/{attempt}/{kind}','NATIVE' if a=='R_NEW' and kind not in ('sham','cross') else prod,rows,cohort='repair',trace=trace))
    return out

def confirmation(panel,producer,rows,attempt='h0',regression=False):
    panel_check(panel,'regression' if regression else 'confirmation')
    need(producer in ('NATIVE','P1','RSEED'),'final producer')
    return [make_slot(x,i,a,k,('regression' if regression else 'confirmation')+'/'+attempt,
            'NATIVE' if a in ('R','R_NEW') else producer,rows) for i,x in enumerate(panel['inputs']) for a in ('R','R_NEW',*CANDIDATES) for k in ('heavy','off')]

def timing(panel,producer,rows,session):
    panel_check(panel,'confirmation');integer(session,0,3,'session')
    result=[]
    for j in range(12):
        i=(j+session)%12;x=panel['inputs'][i];rot=(i+session)%6
        for a in TIMING[rot:]+TIMING[:rot]:
            for k in ('warmup','measured'):result.append(make_slot(x,i,a,k,f'timing/s{session}','NATIVE' if a=='R' else producer,rows,session))
    return result

def native_slot(s,compatibility_study='rtx_dense14b_transfer_v1'):
    # The historical executable needs its old input schema; OUT/ledger/UUID are new.
    out={k:v for k,v in s.items() if k not in ('cohort','rows')}
    out['study_id']=compatibility_study if s['cohort']=='reference' else STUDY
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=('baseline','p1','rseed','sham','cross','candidate','trace','confirmation','timing'))
    p.add_argument('--panel',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--producer',default='RSEED');p.add_argument('--rows',default='off');p.add_argument('--session',type=int,default=0);p.add_argument('--attempt',default='v00')
    a=p.parse_args();panel=read(a.panel)
    z=confirmation(panel,a.producer,a.rows,a.attempt) if a.phase=='confirmation' else timing(panel,a.producer,a.rows,a.session) if a.phase=='timing' else development(panel,a.phase,a.attempt,a.rows,producer=a.producer)
    save(a.out,{'study_id':STUDY,'phase':a.phase,'panel_sha256':sha(a.panel),'rows':z,'model_requests':len(z),'executed':False},True)
