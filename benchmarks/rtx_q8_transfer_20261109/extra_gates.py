"""Prerecorded termination, exhaustive controlled transactions and native negatives."""
from pathlib import Path
import collections,copy,hashlib,json,sys
from admission import HERE,ROOT,sha,put
from execute import BASE,WORK,execute
from lifecycle_gate import read,spec,candidate,canonical,Bank,MANIFEST as NATURAL
from normalize import trace_from_row
from active_kv import parse

MANIFEST='JOB_MANIFEST_EXTRA.json'

def freeze():
    base=read(ROOT/NATURAL);models={k:v for k,v in base['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots'];eog=read(ROOT/'EOG_FIXTURE_SOURCE_209.json')['input'];jobs=[]
    jobs.append(spec('extra-v2-EOG-R','R',dict(models,lowering='SIMPLE',inputs=[dict(name='free',capture=True,input=eog)]),1,len(eog['prompt_ids'])+eog['cap']-1))
    r0=read(WORK/'runs/lifecycle-v2-R-free-r0/native/free/receipt.json');greedy=r0['ids'];p=roots[0]['prompt_ids']
    assert len(greedy)>=20,'Fixed controlled fixture requires original independent greedy continuation'
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                payload=candidate(core,cut,k,models);payload['inputs']=[dict(name='eog-'+mode,capture=mode=='heavy',input=eog) for mode in ('heavy','clean')]
                jobs.append(spec(f'extra-v2-EOG-{core}-{cut}-k{k}',core,payload,2,2*(2*len(eog['prompt_ids'])+2*(k+1)*(eog['cap']-1))))
                cases=[('reject-'+str(j),j+2,j) for j in range(k)]+[('cap-'+str(cap),cap,None) for cap in range(2,k+2)]
                cases += [('bonus',k+2,None),('cap1',1,None),('bonus-resume',k+3,None),('correction-resume',k+3,0)]
                inputs=[]
                for name,cap,reject in cases:
                    rows=[]
                    for index in range(cap):
                        proposals=list(greedy[index+1:index+8]);assert len(proposals)==7
                        if index==0 and reject is not None:proposals[reject]=(proposals[reject]+1)%151936
                        rows.append(dict(base=len(p)+index,seed=greedy[index],proposals=proposals))
                    tape=dict(schema='heterospec.rtx211.R-derived-controlled-fixture.v1',root=roots[0]['id'],prompt_ids=p,rows=rows,max_k=7,
                        independent_R_receipt_sha256=sha(WORK/'runs/lifecycle-v2-R-free-r0/native/free/receipt.json'),fixture_only=True)
                    x=dict(roots[0],cap=cap,proposal_tape=tape,proposal_tape_sha256=canonical(tape))
                    inputs.append(dict(name=name,capture=True,input=x))
                payload=candidate(core,cut,k,models,'replay');payload['inputs']=inputs
                bound=sum(len(p)+(k+1)*(e['input']['cap']-1) for e in inputs)
                jobs.append(spec(f'extra-v2-controls-{core}-{cut}-k{k}',core,payload,len(inputs),bound))
    negatives=[('unsupported-k',dict(k=5),'M2 explicit k3/7 reserve8 D4 contract'),('insufficient-reserve',dict(target_output_reserve=4),'M2 explicit k3/7 reserve8 D4 contract'),
        ('unknown-option',dict(unregistered_rtx211=True),'Unknown M1 native job field'),('ignored-context',dict(n_ctx=2048),'Ignored context request'),
        ('transient-capacity',dict(inputs=[dict(name='bad',capture=False,input=dict(roots[0],prompt_ids=(p*12)[:893],cap=128))]),'transient position capacity')]
    for name,patch,error in negatives:
        payload=candidate('packed','LOCAL',7,models);payload['inputs']=[];payload.update(patch)
        job=spec('extra-v2-negative-'+name,'packed',payload,1,2*893+16*127);job['expect_error']=error;jobs.append(job)
    inputs=read(ROOT/'cohort/COHORT_ADMISSION.json')['selected']
    payload=dict(models,lowering='SIMPLE',inputs=[dict(name='formal-'+str(i),capture=False,input=x) for i,x in enumerate(inputs)])
    jobs.append(spec('extra-v2-formal-independent-R','R',payload,len(inputs),sum(len(x['prompt_ids'])+x['cap']-1 for x in inputs)))
    put(ROOT/MANIFEST,dict(base,jobs=jobs,status='FROZEN_EXTRA_SEMANTIC_GATES',fixed_requests=sum(j['requests'] for j in jobs),fixed_rows=sum(j['rows'] for j in jobs),
        source_fixture_sha256=sha(ROOT/'EOG_FIXTURE_SOURCE_209.json'),controlled_R_sha256=sha(WORK/'runs/lifecycle-v2-R-free-r0/native/free/receipt.json'),
        required_stop='Actual native EOG required; all controlled rejection ranks/bonus/resumption/caps must pass; unknown error never counts as a passing negative; no clean timing admitted'))
    print('Frozen extra gates',sum(j['requests'] for j in jobs),'requests',flush=True)

def load_bank(index,x,free):
    bank=Bank(index,x,free)
    for p in sorted((ROOT/'oracle-manifests').glob(f'lifecycle-v2-oracle-r{index}-*.json')):
        job=read(p)['jobs'][0];native=WORK/'runs'/job['id']/'native';assert (native.parent/'COMPLETE.json').exists(),'Retained incomplete oracle prevents reuse'
        bank.add(native,job['job']['cases']);bank.counter=max(bank.counter,int(job['id'].rsplit('-',1)[1]))
    return bank

def check_one(bank,native,name,x,mode,expected=None):
    heavy=native/name;r=read(heavy/'receipt.json');r['study_cap']=x['cap'];_,d=trace_from_row(r,x['prompt_ids'],bank.meta['vocab'],bank.meta['eog_ids'],'rtx')
    old=bank.endpoint;ids=old['ids'][:x['cap']];eog=old['eog'][:len(ids)]
    endpoint=dict(ids=ids,eog=eog,length=len(ids),terminal_id=ids[-1],stop_reason='EOG' if eog[-1] else 'CAP')
    assert r['endpoint']==endpoint,'Controlled/EOG independent endpoint mismatch'
    bank.fill(r,d);vectors=[];states=[]
    for use in d['vector_uses']:
        key=use['key'];label='initial' if key=='initial' else 'verify-'+key[4:].replace('/','-')
        actual=(heavy/'target'/(label+'.f32')).read_bytes();want=bank.vector(use['prefix'])
        vectors.append(dict(key=key,equal=actual==want,actual_sha256=hashlib.sha256(actual).hexdigest(),reference_sha256=hashlib.sha256(want).hexdigest()))
    for i,s in enumerate(d['states']):
        label='initial' if i==0 else 'commit-'+str(i-1);path=heavy/'target/state'/label;prefix=s['prefix']
        actual,_=parse((path/'sequence.bin').read_bytes(),list(range(len(prefix))),bank.profile)
        states.append(dict(key=label,active_KV_equal=actual==bank.state(prefix),frontier_equal=(path/'frontier.f32').read_bytes()==bank.vector(prefix),next_pending=s['next_pending'],unmaterialized=s['unmaterialized_suffix']))
        if i:
            c=r['cycles'][i-1];assert c['keep']==len(prefix) and c['target_after']==dict(min=0,max=len(prefix)-1)
            assert c['draft_after']==(dict(min=-1,max=-1) if mode=='replay' else c['target_after'])
    if mode=='replay':assert not r['draft_physical_width_hist'] and r['draft_calls']==0
    if name.startswith('reject-'):
        rank=int(name.split('-')[1]);assert len(r['cycles'])==1 and r['cycles'][0]['rejected'] and r['cycles'][0]['accepted']==rank
    if name=='bonus':assert len(r['cycles'])==1 and r['cycles'][0]['accepted']==r['k'] and r['cycles'][0]['commit_kind']=='bonus'
    if name.startswith('cap-'):assert r['length']==x['cap'] and r['cycles'][0]['commit_kind']=='accepted'
    if name=='cap1':assert not r['cycles']
    if name in ('bonus-resume','correction-resume'):
        assert len(r['cycles'])>=2
        assert r['cycles'][0]['commit_kind']==('bonus' if name=='bonus-resume' else 'correction')
        assert r['cycles'][1]['seed']==r['cycles'][0]['pending_after']
    proof=dict(passed=all(v['equal'] for v in vectors) and all(s['active_KV_equal'] and s['frontier_equal'] for s in states),
        endpoint_equal=True,all_vectors=vectors,all_states=states,receipt_sha256=sha(heavy/'receipt.json'),mode=mode,finite_only=True)
    put(ROOT/'extra_checks'/(native.parent.name+'-'+name+'.json'),proof);assert proof['passed'],'Required controlled state/vector gate failed'

def main():
    if sys.argv[1]=='freeze':freeze();return
    assert read(ROOT/'NATURAL_COMPLETE.json')['passed'],'Complete natural gates required first'
    exposure=read(ROOT/'cohort/EXPOSURE_COMPLETE.json');assert exposure['passed'] and exposure['pr62_files']>0
    base=read(ROOT/MANIFEST);roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots']
    bank=load_bank(0,roots[0],WORK/'runs/lifecycle-v2-R-free-r0/native/free');ebank=None
    for job in base['jobs']:
        native=execute(job,MANIFEST)
        if job['id']=='extra-v2-EOG-R':
            eog=read(ROOT/'EOG_FIXTURE_SOURCE_209.json')['input'];ep=read(native/'free/receipt.json');assert ep['stop_reason']=='EOG' and len(ep['ids'])>1,'Required genuine later-verification EOG did not occur'
            ebank=load_bank(4,eog,native/'free')
        elif job['id'].startswith('extra-v2-EOG-'):
            for item in job['job']['inputs']:
                if item['capture']:check_one(ebank,native,item['name'],item['input'],'live')
            assert read(native/'eog-heavy/receipt.json')['endpoint']==read(native/'eog-clean/receipt.json')['endpoint']
            assert all(x==0 for x in read(native/'eog-clean/receipt.json')['observed_API_calls_within_service'].values())
        elif job['id'].startswith('extra-v2-controls-'):
            for item in job['job']['inputs']:check_one(bank,native,item['name'],item['input'],'replay')
        elif 'negative-' in job['id']:assert (native.parent/'EXPECTED_REJECT.json').exists()
        else:assert job['id']=='extra-v2-formal-independent-R'
        print('EXTRA_PASS',job['id'],flush=True)
    put(ROOT/'EXTRA_COMPLETE.json',dict(passed=True,genuine_EOG=True,all_rejection_ranks=True,bonus_and_correction_resumption=True,caps=True,native_negative_cases=5,independent_new_formal_R=True,remaining_gates=['Owned tape producer/live/replay binding','V2 geometry counters','Four-origin equal-work bridge']))

if __name__=='__main__':main()
