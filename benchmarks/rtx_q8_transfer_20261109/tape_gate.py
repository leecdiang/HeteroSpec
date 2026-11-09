"""Native owned-tape production, complete live ownership and replay/negative gates."""
from pathlib import Path
import copy,json,sys
from admission import ROOT,put,sha
from execute import WORK,execute
from lifecycle_gate import read,spec,candidate,canonical
from extra_gates import load_bank,check_one

MANIFEST='JOB_MANIFEST_TAPES.json'

def freeze():
    base=read(ROOT/'JOB_MANIFEST_LIFECYCLE.json');models={k:v for k,v in base['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    roots=read(ROOT/'QUALIFICATION_TASKS.json')['roots']+[read(ROOT/'EOG_FIXTURE_SOURCE_209.json')['input']]
    requests=[]
    for i,x in enumerate(roots):
        free=WORK/'runs'/(f'lifecycle-v2-R-free-r{i}' if i<4 else 'extra-v2-EOG-R')/'native/free/receipt.json';r=read(free)
        requests.append(dict(name='root-'+str(i),root=x['id'],prompt_ids=x['prompt_ids'],greedy_ids=r['ids'],autonomous_R_receipt_sha256=sha(free)))
    job=candidate('loop4','LOCAL',7,models,'producer');job['proposal_tape_requests']=requests
    jobs=[spec('tapes-v2-native-producer','loop4',job,len(requests),sum(len(x['prompt_ids'])+8*(len(x['greedy_ids'])-1) for x in requests))]
    put(ROOT/MANIFEST,dict(base,status='FROZEN_NATIVE_TAPE_PRODUCER_AND_REPLAY_DAG',jobs=jobs,roots=roots,
        producer_requests=len(requests),subsequent_fixed_requests=32+3,
        replay_origins=[dict(index=0,cap=16),dict(index=4,cap=128)],replay_arms='all8 cut/projection/k, heavy and clean;32 requests',
        native_negative_cases=['corrupted canonical hash','live request carrying a replay tape','rehash with wrong pending seed'],
        expansion='Bind full producer tape hashes before the exact32 replay and3 negative jobs are frozen; never performance data; all oracle work charged to original512 stage ceiling.'))
    print('Frozen native producer',len(requests),'requests; next32 replay plus3 negatives',flush=True)

def expand(meta):
    manifest=read(ROOT/MANIFEST);models={k:v for k,v in manifest['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))};roots=manifest['roots'];jobs=[];tapes={}
    native=WORK/'runs/tapes-v2-native-producer/native'
    assert len(meta['proposal_tapes'])==5
    for i,record in enumerate(meta['proposal_tapes']):
        p=native/record['path'];tape=read(p);assert canonical(tape)==record['canonical_tape_sha256']
        assert record['target_calls']==record['target_rows']==0 and record['draft_rows']==len(tape['prompt_ids'])+8*len(tape['rows'])
        assert record['draft_rows']==sum(int(k)*v for k,v in record['draft_physical_width_hist'].items())
        tapes[i]=dict(tape=tape,sha256=canonical(tape),file_sha256=sha(p),path=str(p),record=record)
    put(ROOT/'OWNED_TAPES.json',dict(tapes={str(k):v for k,v in tapes.items()},producer_result_sha256=sha(native/'result.json'),scope='Separate native draft-only producer; no target replay or live timing claim'))
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                entries=[]
                for index,cap in [(0,16),(4,128)]:
                    x=dict(roots[index],cap=cap,proposal_tape=tapes[index]['tape'],proposal_tape_sha256=tapes[index]['sha256'])
                    for mode in ('heavy','clean'):entries.append(dict(name=f'r{index}-{mode}',capture=mode=='heavy',input=x))
                payload=candidate(core,cut,k,models,'replay');payload['inputs']=entries
                rows=sum(len(e['input']['prompt_ids'])+(k+1)*(e['input']['cap']-1) for e in entries)
                jobs.append(spec(f'tapes-v2-replay-{core}-{cut}-k{k}',core,payload,len(entries),rows))
    x=dict(roots[0],cap=16,proposal_tape=tapes[0]['tape'],proposal_tape_sha256=tapes[0]['sha256'])
    bad=copy.deepcopy(x);bad['proposal_tape_sha256']='0'*64
    wrong=copy.deepcopy(x);wrong['proposal_tape']['rows'][0]['seed']=(wrong['proposal_tape']['rows'][0]['seed']+1)%151936;wrong['proposal_tape_sha256']=canonical(wrong['proposal_tape'])
    for name,input,mode,error in [('hash',bad,'replay','owned tape content SHA'),('live-permission',x,'live','live/replay tape permission'),('pending-seed',wrong,'replay','owned tape seed/base/width')]:
        payload=candidate('packed','LOCAL',7,models,mode);payload['inputs']=[dict(name='negative',capture=False,input=input)]
        j=spec('tapes-v2-negative-'+name,'packed',payload,1,2*len(x['prompt_ids'])+16*(x['cap']-1));j['expect_error']=error;jobs.append(j)
    filename='JOB_MANIFEST_TAPE_REPLAY_EXPANDED.json';put(ROOT/filename,dict(manifest,status='EXACT_PRODUCER_BOUND_REPLAY_AND_NEGATIVES_FROZEN',jobs=jobs,owned_tapes_sha256=sha(ROOT/'OWNED_TAPES.json')))
    return filename,jobs,tapes

def check_live(tapes):
    proofs=[]
    for core in ('loop4','packed'):
        for cut in ('SIMPLE','LOCAL'):
            for k in (3,7):
                for index in range(5):
                    native=WORK/'runs'/(f'lifecycle-v2-{core}-{cut}-k{k}' if index<4 else f'extra-v2-EOG-{core}-{cut}-k{k}')/'native'
                    name=f'r{index}-heavy' if index<4 else 'eog-heavy';r=read(native/name/'receipt.json');tape=tapes[index]['tape'];rows={x['base']:x for x in tape['rows']}
                    for cycle in r['cycles']:
                        actual=rows[cycle['base']];assert cycle['seed']==actual['seed'] and cycle['proposals']==actual['proposals'][:k],'Native live proposal ownership mismatch'
                        for j in range(k):
                            p=native/name/'draft'/f"proposal-{cycle['cycle']}-{j}.f32";assert sha(p)==actual['proposal_vector_sha256'][j],'Full native draft proposal vector hash mismatch'
                    proofs.append(dict(core=core,cut=cut,k=k,index=index,cycles=len(r['cycles']),all_proposal_vectors_match=True,receipt_sha256=sha(native/name/'receipt.json')))
    put(ROOT/'LIVE_TAPE_OWNERSHIP_CHECKED.json',dict(passed=True,proofs=proofs,all8_arms_and5_origins=True,finite_only=True))

def main():
    if sys.argv[1]=='freeze':freeze();return
    assert read(ROOT/'EXTRA_COMPLETE.json')['passed']
    manifest=read(ROOT/MANIFEST);native=execute(manifest['jobs'][0],MANIFEST);filename,jobs,tapes=expand(read(native/'result.json'));check_live(tapes)
    roots=manifest['roots'];banks={i:load_bank(i,roots[i],WORK/'runs'/(f'lifecycle-v2-R-free-r{i}' if i<4 else 'extra-v2-EOG-R')/'native/free') for i in (0,4)}
    for job in jobs:
        native=execute(job,filename)
        if 'negative' in job['id']:continue
        for index in (0,4):
            entry=next(e for e in job['job']['inputs'] if e['name']==f'r{index}-heavy');check_one(banks[index],native,entry['name'],entry['input'],'replay')
            heavy=read(native/f'r{index}-heavy/receipt.json');clean=read(native/f'r{index}-clean/receipt.json')
            assert heavy['endpoint']==clean['endpoint'] and all(v==0 for v in clean['observed_API_calls_within_service'].values())
            assert not clean['draft_physical_width_hist'] and clean['draft_calls']==0
        print('TAPE_REPLAY_PASS',job['id'],flush=True)
    put(ROOT/'TAPES_COMPLETE.json',dict(passed=True,producer_requests=5,replay_requests=32,native_negatives=3,full_live_draft_vector_ownership=True,full_replay_target_vectors_KV_pending=True))

if __name__=='__main__':main()
