"""Deterministic planned cells and starts. Does not execute native programs."""
from dataclasses import asdict
import argparse
from core import *

SENTINELS=('GSM8K/test/1248','GSM8K/test/831','GSM8K/test/1011','GSM8K/test/1249')
ARMS=('R','M_R','M_B','C_R_PQ','C_B_PQ','C_R_QH','C_B_QH')
GPU_MODES=('MQ','PQ','QH_C','QH_D','REPEAT4')
LIMITS={
 'cpu':dict(model_requests=0,operator_hosts=0,graph_computes=2592,owned_seconds=14400,output_bytes=2*1024**3),
 'operator':dict(model_requests=0,operator_hosts=161,graph_computes=160,owned_seconds=3600,output_bytes=2*1024**3),
 'pilot':dict(model_requests=64,model_processes=64,warmups=0,owned_seconds=7200,output_bytes=4*1024**3),
 'confirm':dict(model_requests=1008,model_processes=504,warmups=504,owned_seconds=21600,output_bytes=6*1024**3)}


def cpu_cells():
    cells=[]
    for q in (1,2,3,4):
        for n in (63,128,257):
            for h,hk in ((4,4),(8,1),(16,4)):
                for storage in ('compact','permuted'):
                    g=Geometry(128,128,q,n,h,hk,storage)
                    for mask in ('causal','single','holes'):
                        for pattern in ('dyadic','structured'):
                            x=dict(geometry=g.dict(),mask=mask,pattern=pattern,
                                   group='development' if q<=2 else 'held_after_code_lock')
                            x['id']=sha(x); cells.append(x)
    return cells


def operator_cells():
    # All GPU fixtures use model-style permuted Q; the CPU matrix also tests compact Q.
    return [dict(geometry=Geometry(128,128,q,n,8,hk,'permuted').dict(),
                 mask='causal',pattern='dyadic')
            for q in (1,2,3,4) for n in (63,257) for hk in (8,2)]


def make_plan(phase, panel=None):
    need(phase in LIMITS,'unknown phase')
    slots=[]
    def add(**kw):
        x=dict(study=STUDY,phase=phase,**kw); x['id']=sha(x); slots.append(x)
    if phase=='cpu':
        for c in cpu_cells():
            for mode in MODES: add(cell=c,mode=mode)
    elif phase=='operator':
        add(kind='capability_only',graph_compute=False,process=0)
        for repeat in range(2):
            for i,c in enumerate(operator_cells()):
                order=list(GPU_MODES); shift=(i+repeat)%5; order=order[shift:]+order[:shift]
                if repeat:order.reverse()
                for mode in order:add(kind='graph',cell=c,mode=mode,repeat=repeat,process=len(slots))
    elif phase=='pilot':
        for rep in range(2):
            for t in SENTINELS:add(stage='original_control',task=t,arm='R',repeat=rep,channel='counts',warmup=False)
        for ch in ('counts','diagnostic'):
            for t in SENTINELS:add(stage='shadow_control',task=t,arm='R_SHADOW',repeat=0,channel=ch,warmup=False)
        for ch in ('counts','diagnostic'):
            for t in SENTINELS:
                for arm in ARMS[1:]:add(stage='candidates',task=t,arm=arm,repeat=0,channel=ch,warmup=False)
        for x in slots:x['process_group']=x['id']
    else:
        need(type(panel) is list and len(panel)==24,'24 reviewed unseen inputs required')
        need(len({c['id'] for c in panel})==24,'duplicate task')
        need(all(set(c)=={'id','domain','bin','prompt_sha256'} and c['domain'] in ('code','math') and
                 type(c['bin']) is int and c['bin'] in (0,1,2) and hash_ok(c['prompt_sha256']) for c in panel),'panel fields')
        need(len({c['prompt_sha256'] for c in panel})==24,'duplicate prompt')
        need(all(sum(c['domain']==d and c['bin']==b for c in panel)==4 for d in ('code','math') for b in range(3)),'six balanced strata')
        for session in range(3):
            for i,c in enumerate(sorted(panel,key=lambda x:sha(x))):
                order=list(ARMS); shift=(i+session)%7; order=order[shift:]+order[:shift]
                if session%2:order.reverse()
                for arm in order:
                    group=sha(dict(task=c['id'],arm=arm,session=session))
                    for warm in (True,False):
                        add(task=c['id'],domain=c['domain'],length_bin=c['bin'],prompt_sha256=c['prompt_sha256'],
                            arm=arm,session=session,channel='counts',warmup=warm,process_group=group)
    return dict(study=STUDY,phase=phase,slots=slots,limits=LIMITS[phase],
        candidate_rule='prefer QH_C if full device support census passes; else QH_D; otherwise STOP',
        native_executable_bound=False,execution_F0=None,
        authority='CPU preparation now; exact runtime/input F0 and author approval before device/model stages',
        inherits_old_remaining_slots=False)


def select_panel(inventory, exposure):
    need(exposure.get('review_complete') is True and hash_ok(exposure.get('scope_sha256')),'reviewed history required')
    need(type(exposure.get('ids')) is list and type(exposure.get('prompt_sha256')) is list,'history arrays')
    out=[]; ids=set(); prompts=set(); buckets={(d,b):[] for d in ('code','math') for b in range(3)}
    allowed={'id','domain','prompt_ids','source_sha256','tokenizer_sha256','template_sha256'}
    for x in sorted(inventory,key=lambda v:v.get('id','')):
        need(type(x) is dict and set(x)==allowed,'outcome-free source schema required')
        need(type(x['id']) is str and x['id'] and x['id'] not in ids,'duplicate/invalid source ID'); ids.add(x['id'])
        n=len(x['prompt_ids']);need(x['domain'] in ('code','math') and 64<=n<=512,'domain/length')
        need(all(type(v) is int and 0<=v<128256 for v in x['prompt_ids']),'direct IDs')
        need(all(hash_ok(x[k]) for k in ('source_sha256','tokenizer_sha256','template_sha256')),'missing input pins')
        h=sha(x['prompt_ids'])
        if x['id'] in exposure['ids'] or h in exposure['prompt_sha256'] or h in prompts:continue
        prompts.add(h); b=0 if n<128 else 1 if n<256 else 2
        key=sha(dict(study=STUDY,seed='holdout-v1',id=x['id'],prompt=h))
        buckets[x['domain'],b].append((key,dict(id=x['id'],domain=x['domain'],bin=b,prompt_sha256=h),x))
    chosen=[]
    for key,items in buckets.items():
        need(len(items)>=4,'unfilled stratum '+str(key))
        for _,row,source in sorted(items,key=lambda z:z[0])[:4]:out.append(row);chosen.append(source)
    need(len({x['tokenizer_sha256'] for x in chosen})==1,'mixed tokenizer')
    return dict(panel=out,source_inputs=chosen,exposure=exposure,selection_reads_outcomes=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('phase',choices=LIMITS)
    p.add_argument('--panel');p.add_argument('--out',required=True)
    a=p.parse_args();write_new(a.out,make_plan(a.phase,read(a.panel) if a.panel else None))


def validate_plan(p):
    need(p.get('study')==STUDY and p.get('phase') in LIMITS,'unknown plan')
    panel=None
    if p['phase']=='confirm':
        rows={}
        for s in p['slots']:
            row=dict(id=s['task'],domain=s['domain'],bin=s['length_bin'],prompt_sha256=s['prompt_sha256'])
            if row['id'] in rows:need(rows[row['id']]==row,'inconsistent panel identity')
            rows[row['id']]=row
        panel=list(rows.values())
    need(p==make_plan(p['phase'],panel),'plan differs from deterministic protocol; amend prospectively, not by mutation')
