"""Mutation, rejection and pure cache-state controls. No model/binder backend."""
import copy, itertools, json
from common import ROOT, save, modules
from conditions import evaluate, example
from symbolic import verify

def main():
    before=modules()
    rows=[json.loads(s) for s in (ROOT/'DEV_RAW.jsonl').read_text().splitlines()]
    base=next(x for x in rows if x.get('event')=='FIXTURE' and x['geometry']==dict(q=2,k=128,h=32,hk=8,storage=1,mask=1,pattern=0))
    positives=[verify(base,i) for i in range(3)]
    assert all(x.get('status')=='EXACT_ADDRESS_MATCH' for x in positives)
    mutants=[]
    for fault in ['query_offset','GQA_modulo','mask_reuse','output_recombine']:
        x=copy.deepcopy(base);g=x['layouts'][2]['graph']
        if fault=='query_offset':next(t for t in g if t['op']=='VIEW' and t['ne'][3]==2 and t['ne'][2]==32)['nb'][3]=0
        if fault=='GQA_modulo':x['mutant_gqa_rule']='modulo'
        if fault=='mask_reuse':next(t for t in g if t['op']=='VIEW' and t['ne'][3]==2 and t['ne'][2]==1)['nb'][3]=0
        if fault=='output_recombine':next(t for t in g if t['op']=='PERMUTE')['nb'][1]=128*32*4
        witness=verify(x,2);assert witness.get('status')!='EXACT_ADDRESS_MATCH'
        mutants.append(dict(fault=fault,detected=True,witness=witness))
    rejects=[]
    for fault in ['nondivisible_GQA','out_of_bounds','mask_stride','q3']:
        x=example()
        if fault=='nondivisible_GQA':x['hk']=7
        if fault=='out_of_bounds':x['q_offset']+=4
        if fault=='mask_stride':x['mask_nb'][1]+=4
        if fault=='q3':x['q']=3
        r=evaluate(x);assert r['errors'];rejects.append(dict(fault=fault,errors=r['errors']))
    assert evaluate(example())['representations']['QB']['vulkan_mul_mat_support'] is False
    assert evaluate(example(1))['representations']['QB']['vulkan_mul_mat_support'] is True
    # Source key includes role,phase,layout,ub,capacity; shape reuse belongs to upstream reuse checks.
    transitions=[];previous=None;epoch=0
    seq=[('target','PREFILL','MQ',128,4,1),('target','VERIFY','QB',4,4,2),
         ('draft','CONTINUE','MQ',1,1,1),('target','VERIFY','QB',4,4,1),
         ('target','VERIFY','QB',4,4,2),('target','RECONCILE','PQ',4,4,1),
         ('target','VERIFY','PQ',4,4,2)]
    topologies={};shape_rejections=0
    for role,phase,layout,ub,cap,q in seq:
        key=(role,phase,layout,ub,cap);invalidated=key!=previous
        if invalidated:epoch+=1;topologies.clear()
        topology=('MQ' if q==1 else layout,q)
        if key in topologies and topologies[key]!=topology:shape_rejections+=1
        # Pure guard model explicitly refuses reuse across query width, including q1 original path.
        reused=topologies.get(key)==topology
        topologies[key]=topology;previous=key
        transitions.append(dict(role=role,phase=phase,layout=layout,q=q,epoch=epoch,key_invalidated=invalidated,shape_match_reused=reused,topology=list(topology)))
    assert shape_rejections==1
    save(ROOT/'CONTRACT_TESTS.json',dict(symbolic_positive=positives,mutations=mutants,
         rejection_only=rejects,state_transitions=transitions,shape_reuse_rejected=shape_rejections,
         lifecycle_scope='Pure abstract guard model, not native binder or GPU cache validation; upstream actual shape checks separately source-bound.',
         modules_before=before,modules_after=modules(),gpu_starts=0))
    print(dict(symbolic_positive=3,mutants_detected=len(mutants),rejections=len(rejects),state_transitions=len(seq)))

if __name__=='__main__':main()
