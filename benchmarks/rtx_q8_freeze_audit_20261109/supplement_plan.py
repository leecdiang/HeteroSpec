"""OFFLINE ONLY: quantify a concrete optional state-coverage supplement; no runner."""
from pathlib import Path
import collections,json
from core import WORK,RECORDS,OUT,read,put,digest,ledger,stamp

def crossings(job,item):
    r=read(WORK/'runs'/job['id']/'native'/item['name']/'receipt.json');v=iter(e for e in r['executions'] if e['phase']=='VERIFY');found=[]
    for c in r['cycles']:
        n=0;groups=[]
        while n<r['k']+1:
            e=next(v);n+=e['width'];groups+=e['expected_extents']
        if len(set(groups))>1:found.append(dict(base=c['base'],accepted=c['accepted'],rejected=c['rejected'],kind=c['commit_kind'],extents=groups))
    return r,found

def main():
    entries=ledger();natural=[];formal=[];rawstates_missing=[]
    for a in entries:
        if a['status']!='COMPLETE':continue
        j=read(WORK/'runs'/a['id']/'JOB.json')
        if j['exe_sha256']=='73113940c38b24093a73d5bfefb46852af66b703c4923379fdd972cba603e249':continue
        for item in j['job'].get('inputs',[]):
            r,cross=crossings(j,item)
            if item['capture']:natural.extend(dict(job=j['id'],name=item['name'],root=item['input']['id'],**c) for c in cross)
            if a['stage']=='live' and item['name'].startswith('test-'):
                formal.extend(dict(job=j['id'],name=item['name'],root=item['input']['id'],**c) for c in cross)
                for c in cross:
                    p=WORK/'runs'/j['id']/'native'/item['name']/'target/state'/('commit-'+str(next(cy['cycle'] for cy in r['cycles'] if cy['base']==c['base'])))
                    assert not (p/'sequence.bin').exists();rawstates_missing.append(str(p/'sequence.bin'))
    assert not natural and formal
    manifest=read(RECORDS/'JOB_MANIFEST_LIVE.json');jobs=manifest['jobs'][:8];roots=read(RECORDS/'cohort/COHORT_FREEZE.json')['inputs']
    chosen=None
    for x in roots:
        qualifying=set()
        for j in jobs:
            item=next(v for v in j['job']['inputs'] if v['input']['id']==x['id']);_,cs=crossings(j,item)
            if any(c['rejected'] for c in cs):qualifying.add(j['job']['k'])
        if qualifying=={3,7}:chosen=x;break
    assert chosen['id']=='APPS/train/603';fulls=set();needed=set();needed_states=set();candidate=[];bindings=[];captures_bytes=0
    state_size=lambda n:888+147468*n
    for j in jobs:
        item=next(v for v in j['job']['inputs'] if v['input']['id']==chosen['id']);r,_=crossings(j,item);prefix=chosen['prompt_ids'].copy();needed.add(tuple(prefix));needed_states.add(tuple(prefix));state_lengths=[len(prefix)]
        for c in r['cycles']:
            complete=prefix+[c['seed']]+c['proposals'];fulls.add(tuple(complete))
            for i in range(1,r['k']+2):needed.add(tuple(complete[:len(prefix)+i]))
            prefix=complete[:c['keep']];needed_states.add(tuple(prefix));state_lengths.append(len(prefix))
        state_lengths.append(len(prefix))
        predicted=sum(state_size(n) for n in state_lengths)+607744*(3+(2*r['k']+2)*len(r['cycles']));captures_bytes+=predicted
        candidate.append(dict(id='SUPPLEMENT-NOT-RUN-'+j['arm_label'],exe=j['exe'],exe_sha256=j['exe_sha256'],requests=1,
            conservative_rows=2*len(chosen['prompt_ids'])+2*(r['k']+1)*(chosen['cap']-1),
            job=dict(j['job'],inputs=[dict(name='boundary-natural-heavy',input=chosen,capture=True)]),
            predicted_capture_bytes=predicted,qualification_only=True))
        bindings.append(dict(original_worker=j['id'],item=item['name'],clean_receipt_sha256=digest((WORK/'runs'/j['id']/'native'/item['name']/'receipt.json').read_bytes())))
    leaves=sorted(p for p in fulls if not any(len(q)>len(p) and q[:len(p)]==p for q in fulls));covered=set();cases=[];reference_bytes=0
    for i,path in enumerate(leaves):
        use=sorted(p for p in needed|needed_states if len(p)<=len(path) and path[:len(p)]==p and p not in covered)
        assert use
        positions=sorted(len(p) for p in use);states=sorted(len(p) for p in use if p in needed_states)
        cases.append(dict(name=f'prebound-path-{i:02d}',forced=[dict(ids=chosen['prompt_ids'],phase='PREFILL',all=False),dict(ids=list(path[len(chosen['prompt_ids']):]),phase='FORCED',all=False)],observe_positions=positions,state_positions=states))
        reference_bytes+=len(positions)*607744+sum(state_size(n) for n in states);covered.update(use)
    assert covered==needed|needed_states
    refs=[];base=read(WORK/'runs/same-work-v2-R-0/JOB.json')
    for start in range(0,len(cases),4):
        cc=cases[start:start+4];refs.append(dict(id=f'SUPPLEMENT-NOT-RUN-independent-R-{start//4}',exe=base['exe'],exe_sha256=base['exe_sha256'],requests=len(cc),
            conservative_rows=sum(sum(len(v['ids']) for v in c['forced']) for c in cc),job=dict({k:v for k,v in base['job'].items() if k!='cases'},cases=cc)))
    request=sum(j['requests'] for j in refs+candidate);rows=sum(j['conservative_rows'] for j in refs+candidate)
    assert request==37 and rows==18543 and 463+request<=512
    put('BOUNDARY_COVERAGE_GAP.json',dict(heavy_transactions_with_extent_crossing=natural,formal_crossing_cycles=formal,formal_crossing_cycles_count=len(formal),
        formal_crossing_and_rejection_count=sum(c['rejected'] for c in formal),formal_crossing_roots=sorted({c['root'] for c in formal}),
        missing_clean_state_payloads=rawstates_missing,
        interpretation='A verified finite joint-coverage gap, not a detected numeric mismatch. Forced within/cross geometry and equal-work raw states passed independently. Old clean state payloads cannot be retroactively recovered offline.'))
    put('OPTIONAL_SUPPLEMENT_DRAFT.json',dict(status='OFFLINE_DRAFT_ONLY_NOT_AUTHORIZED_TO_RUN',new_GPU_requests_executed=0,
        purpose='Only if stronger natural cross-extent rejection/rollback active-KV assurance is required. No repetition of formal timing, no speed estimand.',
        selection='First original frozen input order with observed cross-extent rejection in both k3/k7; coverage/branch only, never service time. Explicitly post-hoc targeted follow-up, not blind input confirmation.',
        selected_root=chosen,original_clean_bindings=bindings,reference_jobs=refs,candidate_jobs=candidate,
        budget=dict(new_logical_requests=request,independent_R_cases=len(cases),heavy_candidates=8,native_workers=len(refs)+len(candidate),new_conservative_rows=rows,
            projected_qualification_requests=463+request,qualification_limit=512,remaining_qualification_after_success=512-463-request,
            projected_cumulative_requests=2679+request,cumulative_request_limit=3072,projected_cumulative_rows=2854298+rows,cumulative_row_limit=4000000,
            new_tranche_after_success=1775+request,new_tranche_limit=2048,no_stage_transfer=True,no_refunds=True),
        projected_raw_payload_bytes=captures_bytes+reference_bytes,storage='Use a fresh C: directory with >=10GiB floor plus estimated payload and margin; do not spend D:20GiB reserve or move/delete existing evidence.',
        reference_vectors=len(needed),reference_state_prefixes=len(needed_states),new_primers=0,new_profiling=0,
        gates=['Explicit user decision before any model execution; recheck newest RTX ledger/resources/cooperative mutex.',
        'Freeze every exact source/model/job/reference token path and observation position before any new output; bind all8 V2 executables/configurations.',
        'Original R UB1 independently computes all pre-bound full vectors/active states; no expected float from candidates.',
        'Compare every new heavy requested vector and committed active KV/frontier, full endpoint/trace/masks against pre-bound R; require equality to original clean token/branch traces.',
        'If a trace differs or a state/vector/guard fails, retain it and stop; do not expand references, weaken tolerance, replace root, or rerun formal1024.',
        'All new capture costs excluded from old performance statistics. Passing improves finite bridge evidence, cannot recover old uncaptured KV or undo historical freeze deviation.']))
    print(json.dumps(dict(joint_gap_cycles=len(formal),crossing_rejections=sum(c['rejected'] for c in formal),supplement_requests=request,rows=rows,predicted_raw_GiB=(captures_bytes+reference_bytes)/1024**3,executed=0)),flush=True)

if __name__=='__main__':main()
