"""Independent, read-only CPU audit. Does not import or execute archived code."""
import argparse
import collections
import hashlib
import io
import itertools
import json
import math
import os
from pathlib import Path
import statistics
import urllib.request
import zipfile

HEAD = '810407c9423cac925d38a976403e23c81bb1704b'
REPO = 'leecdiang/HeteroSpec'
ROOT = 'repository/benchmarks/rtx_evidence_closeout_v1/'
DESIGN = 'repository/docs/experiments/rtx_evidence_closeout_20261011/DESIGN.json'
CAS_SHA = '6cef4902fb2983024b4eb0c4b9a8a6c97ffed770d18495141f94144e11bc7232'
PARTS = [
    ('352e5a9633074d595d6ffb111f989a8bbb576591', 67108864,
     '719c037b10d8af0a95b6fa785e4217ca2f02db7116baa93f63395f48653ba384'),
    ('55ee171a85a2052e208c27a5951a592b491674b1', 47342360,
     '07db1ef18469b27eded817967d184cec06031796f4ef5a0ae13c1366c975ac2d')]
ARMS = ['R', 'M0', 'M3', 'R_prod', 'C3']
FAMILIES = ['Qwen', 'SmolLM2', 'Llama']

def sha(b): return hashlib.sha256(b).hexdigest()
def gitsha(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def objsha(o): return sha(json.dumps(o, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())
def js(b): return json.loads(b.decode('utf-8-sig'))
def gm(v): return math.exp(statistics.mean(math.log(x) for x in v))

def get(path, raw=False):
    request = urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,
        headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                 'Accept':'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
                 'User-Agent':'HeteroSpec-independent-CPU-audit'})
    with urllib.request.urlopen(request, timeout=120) as r: return r.read()

def signature(r, eog):
    o=r['output'];ids=o['ids'];flags=o['eog_flags']
    assert isinstance(ids,list) and 0<len(ids)<=128
    assert all(type(x) is int and x>=0 for x in ids)
    assert all(type(x) is bool for x in flags)
    assert flags==[x in eog for x in ids] and not any(flags[:-1])
    assert o['length']==len(ids) and o['terminal_id']==ids[-1]
    assert o['stop_reason']==('EOG' if flags[-1] else 'CAP')
    assert flags[-1] or len(ids)==128
    assert o['cached_tokens']==0 and o['truncated'] is False
    return (tuple(ids),tuple(flags),len(ids),ids[-1],o['stop_reason'])

def count_check(r):
    w=r['workload'];L=r['output']['length']
    assert not r.get('workload_error') and w['unsupported_replay'] is False
    assert w['output_ids_count']==L and w['prompt_ids_count']>0
    destinations=['accepted_committed','first_mismatch_rejected','unexamined_after_mismatch',
                  'terminal_discarded','unverified_before_verify']
    assert w['proposal_generated']==sum(w[k] for k in destinations)
    assert 0<=w['accepted_committed']<=w['proposal_verified']<=w['proposal_generated']
    assert w['unverified_before_verify']==w['proposal_generated']-w['proposal_verified']
    assert L==sum(w[k] for k in ['initial_target_committed','accepted_committed','bonus_committed',
                               'correction_committed','fallback_committed'])
    for name in ['accepted_prefix_hist','cycle_progress_hist','verification_caller_width_hist']:
        assert sum(w[name].values())==w['verify_cycles']
    weighted=lambda h:sum(int(k)*v for k,v in h.items())
    assert weighted(w['accepted_prefix_hist'])==w['accepted_committed']
    assert weighted(w['cycle_progress_hist'])==w['accepted_committed']+w['bonus_committed']+w['correction_committed']
    assert weighted(w['verification_caller_width_hist'])==w['proposal_verified']+w['verification_seed_rows']
    assert w['draft_continuation_rows']==w['draft_continuation_calls']
    assert w['draft_continuation_rows']==w['draft_proposal_rows']+w['draft_catchup_rows']
    assert weighted(w['target_caller_width_hist'])==w['target_continuation_rows']
    assert sum(w['target_caller_width_hist'].values())==w['target_continuation_calls']
    histograms=[w['target_physical_width_hist'],w['draft_physical_width_hist']]
    assert sum(sum(h.values()) for h in histograms)==w['physical_micrograph_calls']
    assert sum(weighted(h) for h in histograms)==w['physical_micrograph_rows']
    assert sum(w['target_continuation_physical_width_hist'].values())+w['target_prefill_physical_calls']==sum(w['target_physical_width_hist'].values())

def paired_analysis(records, eogs):
    assert len(records)==3600
    table={};sigs={}
    for r in records:
        key=(r['family'],r['task'],r['session'],r['round'],r['condition'])
        assert key not in table, 'duplicate coordinate'
        assert r['phase']=='formal' and r['status']=='COMPLETED' and r['warmup'] is False
        assert r['measurement_mode']=='counts'
        assert r['observation']==dict(phase_timers=False,heavy_capture=False,etw=False,added_sync=False)
        assert math.isfinite(r['wall_ms']) and r['wall_ms']>0
        table[key]=r;sigs[key]=signature(r,set(eogs[r['family']]))
    tasks=sorted({r['task'] for r in records})
    assert len(tasks)==24 and collections.Counter(t.split('/')[0] for t in tasks)=={'MBPP':12,'GSM8K':12}
    assert set(table)==set(itertools.product(FAMILIES,tasks,range(2),range(5),ARMS)), 'missing coordinate'
    result={}
    for f in FAMILIES:
        stable={a:all(len({sigs[f,t,s,j,a] for s in range(2) for j in range(5)})==1 for t in tasks) for a in ARMS}
        pairs=[]
        for a,b in itertools.combinations(ARMS,2):
            mismatch=[];task_effects=[];matched=0
            for t in tasks:
                differences=[]
                for s,j in itertools.product(range(2),range(5)):
                    ka,kb=(f,t,s,j,a),(f,t,s,j,b)
                    assert table[ka]['input_sha256']==table[kb]['input_sha256']
                    if sigs[ka]==sigs[kb]: matched+=1
                    else:
                        first=next((dict(index=i,left=x,right=y) for i,(x,y) in enumerate(itertools.zip_longest(sigs[ka][0],sigs[kb][0])) if x!=y),None)
                        differences.append(dict(session=s,round=j,first_difference=first))
                if differences:mismatch.append(dict(task=t,differences=differences))
                sr=[statistics.median(table[f,t,s,j,a]['wall_ms'] for j in range(5))/statistics.median(table[f,t,s,j,b]['wall_ms'] for j in range(5)) for s in range(2)]
                task_effects.append(dict(task=t,ratio=gm(sr),session_ratios=sr))
            pairs.append(dict(pair=a+'/'+b,matched_requests=matched,matched_tasks=24-len(mismatch),
                complete_pairwise_equal=matched==240 and stable[a] and stable[b],
                cost_ratio=gm([x['ratio'] for x in task_effects]),
                domains={d:gm([x['ratio'] for x in task_effects if x['task'].startswith(d+'/')]) for d in ['MBPP','GSM8K']},
                session_ratios=[gm([x['session_ratios'][s] for x in task_effects]) for s in range(2)],
                regressions=[x['task'] for x in task_effects if x['ratio']<1],mismatches=mismatch,task_effects=task_effects))
        result[f]=dict(stable_by_arm=stable,pairs=pairs)
    return result

def work_summary(records):
    output=[]
    keys=['output_ids_count','proposal_generated','proposal_verified','accepted_committed','draft_prefill_ids',
          'draft_continuation_rows','draft_proposal_rows','draft_catchup_rows','target_prefill_ids',
          'target_prefill_physical_calls','target_continuation_rows','target_continuation_calls','verify_cycles']
    for f,d,a in itertools.product(FAMILIES,['MBPP','GSM8K'],ARMS):
        rr=[r for r in records if r['family']==f and r['condition']==a and r['task'].startswith(d+'/')]
        totals={k:sum(r['workload'][k] for r in rr) for k in keys}
        totals['target_continuation_micrographs']=sum(sum(r['workload']['target_continuation_physical_width_hist'].values()) for r in rr)
        totals['target_total_micrographs']=sum(sum(r['workload']['target_physical_width_hist'].values()) for r in rr)
        totals['target_verification_rows']=sum(r['workload']['proposal_verified']+r['workload']['verification_seed_rows'] for r in rr)
        ratios={k:totals[k]/totals['output_ids_count'] for k in totals if k!='output_ids_count'}
        output.append(dict(family=f,domain=d,arm=a,requests=len(rr),totals=totals,per_output=ratios,
            acceptance_per_verified=totals['accepted_committed']/totals['proposal_verified'] if totals['proposal_verified'] else None,
            median_output_length=statistics.median(r['output']['length'] for r in rr),
            median_prompt_length=statistics.median(r['workload']['prompt_ids_count'] for r in rr),
            cap_requests=sum(r['output']['stop_reason']=='CAP' for r in rr),
            continuation_physical_widths=sorted({int(w) for r in rr for w in r['workload']['target_continuation_physical_width_hist']})))
    return output

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',default='audit-output');args=p.parse_args()
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    tree=js(get('git/trees/'+HEAD+'?recursive=1'));assert not tree['truncated']
    gitfiles={e['path']:e for e in tree['tree'] if e['type']=='blob'}
    pieces=[]
    for h,size,digest in PARTS:
        b=get('git/blobs/'+h,True);assert len(b)==size and sha(b)==digest and gitsha(b)==h;pieces.append(b)
    cas=b''.join(pieces);assert len(cas)==114451224 and sha(cas)==CAS_SHA
    z=zipfile.ZipFile(io.BytesIO(cas));assert len(z.namelist())==len(set(z.namelist()))
    index=js(z.read('INDEX.json'))['files'];assert len(index)==21794
    for n,entry in index.items():
        b=z.read(n);assert len(b)==entry['bytes'] and sha(b)==entry['sha256']
    def read(n):return js(z.read(n))
    def public(n):return read(ROOT+n)
    bound=['FORMAL_RECORDS.json','WORKLOAD_RECORDS.json','FORMAL_PLAN.json','CONFIRMATION_INPUTS.json',
           'RAW_RECORD_INDEX.json','PAID_LEDGER.json','BREAK_EVEN_MODEL.json','MODEL_CALIBRATION.json','SOURCE_RUNTIME.zip']
    for n in bound:assert gitsha(z.read(ROOT+n))==gitfiles[ROOT[len('repository/'):]+n]['sha'],n
    native=zipfile.ZipFile(io.BytesIO(z.read(ROOT+'SOURCE_RUNTIME.zip')))
    ni=js(native.read('INDEX.json'))['files'];assert len(ni)==6890
    for n,entry in ni.items():
        b=native.read(n);assert len(b)==entry['bytes'] and sha(b)==entry['sha256']
    records=public('FORMAL_RECORDS.json');plan=public('FORMAL_PLAN.json');inputs=public('CONFIRMATION_INPUTS.json')
    design=read(DESIGN);freeze=read('closeout/F0B_REMOTE_RECEIPT.json');model=public('BREAK_EVEN_MODEL.json')
    assert freeze['commit']=='8e771e5371179af504443bdfc65e4d6e0990ec35'
    assert objsha(plan)==freeze['plan_sha256'] and objsha(inputs)==freeze['input_sha256']
    assert objsha(model)==freeze['model_sha256'] and model['status']=='MODEL_TIMING_UNAVAILABLE'
    assert plan['design_sha256']==objsha(design)
    expected={s['slot']:(b,s) for b in plan['blocks'] for s in b['slots']}
    assert len(expected)==3600 and len(plan['blocks'])==150
    rawindex={r['slot']:r for r in public('RAW_RECORD_INDEX.json')};assert set(rawindex)==set(expected)
    byinput={(f,t['id']):t for f,tt in inputs['families'].items() for t in tt}
    print('SCHEMA '+json.dumps(records[0])[:16000])
    paths=set()
    for r in records:
        b,s=expected[r['slot']];entry=rawindex[r['slot']];path='closeout/'+entry['path']
        assert path not in paths;paths.add(path)
        rawbytes=z.read(path);assert sha(rawbytes)==entry['sha256']
        raw=js(rawbytes);assert r=={k:v for k,v in raw.items() if k not in ['response','trace_range']}
        folder=path.rsplit('/',1)[0]+'/'
        started=read(folder+'REQUEST_STARTED.json');done=read(folder+'COMPLETED.json')
        assert done['record_sha256']==sha(rawbytes) and started['slot']==r['slot']
        assert r['freeze_commit']==started['freeze_commit']==freeze['commit']
        assert r['actual_condition']==b['condition'] and r['contract_valid'] is True
        task=byinput[r['family'],r['task']]
        assert r['input_sha256']==s['input_sha256']==objsha(task)==started['input_sha256']
        assert started['body']['prompt']==task['prompt_ids'] and started['body']['n_predict']==128
        assert started['body']['temperature']==0 and started['body']['seed']==123
        response=raw['response'];obs=response['hs_closeout']
        assert r['output']['ids']==response['tokens'] and r['output']['length']==response['tokens_predicted']
        assert r['output']['stop_reason']=={'eos':'EOG','limit':'CAP'}[response['stop_type']]
        assert response['timings']['prompt_n']==len(task['prompt_ids'])
        assert response['timings']['cache_n']==0 and response['truncated'] is False
        assert r['workload']==obs['workload'] and r['feature_units']==obs['feature_units']
        assert obs['mode']=='counts' and all(obs[k] is False for k in r['observation'])
        assert obs['scope_mask']==b['condition']['mask'] and obs['target_ub']==b['condition']['prefill_ub']
        assert r['request_end_ns']>r['request_start_ns']
        assert math.isclose(r['wall_ms'],(r['request_end_ns']-r['request_start_ns'])/1e6,rel_tol=0,abs_tol=1e-9)
        count_check(r)
    families=paired_analysis(records,{f:design['assets'][f]['eog'] for f in FAMILIES})
    expected_result=public('RESULTS.json');recomputed=0
    for f,value in expected_result['families'].items():
        pairs={r['pair']:r for r in families[f]['pairs']}
        for arm,qual in value['qualification'].items():
            equal=families[f]['stable_by_arm'][arm] if arm=='R' else pairs['R/'+arm]['complete_pairwise_equal']
            assert qual['request_cost_qualified']==equal
            assert len(qual['mismatches'])==(0 if arm=='R' else 240-pairs['R/'+arm]['matched_requests'])
        for c in value['comparisons']:
            left,right=c['comparison'].split('/');reverse=left+'/'+right not in pairs
            actual=pairs[right+'/'+left] if reverse else pairs[left+'/'+right]
            ratio=1/actual['cost_ratio'] if reverse else actual['cost_ratio']
            assert math.isclose(ratio,c['diagnostic_complete_cost_ratio'],rel_tol=1e-12)
            assert c['request_qualified_ratio'] is None or math.isclose(ratio,c['request_qualified_ratio'],rel_tol=1e-12)
            for j,v in enumerate(actual['session_ratios']):
                assert math.isclose(1/v if reverse else v,c['session_ratios'][j],rel_tol=1e-12)
            negative=[r['task'] for r in actual['task_effects'] if (r['ratio']>1 if reverse else r['ratio']<1)]
            assert sorted(negative)==sorted(c['regressions']);recomputed+=1
    ledger=public('PAID_LEDGER.json');events=ledger['events']
    formal=[e for e in events if e['phase']=='formal' and e['kind']=='request']
    assert len(formal)==len({e['slot'] for e in formal})==3600 and {e['slot'] for e in formal}==set(expected)
    assert sum(e['phase']=='formal' and e['kind']=='warmup' for e in events)==150
    assert freeze['utc']<min(e['utc'] for e in events if e['phase']=='formal')
    assert math.isclose(sum(x['seconds'] for x in ledger['lifetimes']),ledger['owned_lifetime_seconds'],abs_tol=1e-6)
    result=dict(status='PASS',source_head=HEAD,archive_sha256=CAS_SHA,archive_files_verified=len(index),
        source_runtime_files_verified=len(ni),formal_records=len(records),native_result_crosschecks=len(paths),
        native_full_output_and_counter_crosscheck=True,request_endpoint_timer_crosscheck=True,
        proposal_and_output_conservation=True,physical_work_conservation=True,recomputed_comparisons=recomputed,
        owned_lifetime_seconds=ledger['owned_lifetime_seconds'],paid_units=sum(e['paid_units'] for e in events),
        model_status=model['status'],new_model_forwards=0,archived_code_executed=False,
        external_model_and_DLL_bytes_rehashed=False,families=families,work=work_summary(records))
    (out/'RTX_CROSSAUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    compact={k:v for k,v in result.items() if k!='families'}
    compact['families']={f:dict(stable_by_arm=v['stable_by_arm'],pairs=[{**{k:x for k,x in p.items() if k not in ['mismatches','task_effects']},'mismatch_tasks':[x['task'] for x in p['mismatches']]} for p in v['pairs']]) for f,v in families.items()}
    print('AUDIT_RESULT '+json.dumps(compact,ensure_ascii=False))

if __name__=='__main__':main()
