"""Recompute #84 exported native counters/lengths. Does not restore raw archives or run GPU."""
import argparse, collections, hashlib, json, math, statistics
from pathlib import Path

def prior(results, inputs):
    rows=results['native_case_diagnostics']; output={}
    for family in ('Qwen','SmolLM2','Llama'):
        panel={}
        for domain in ('ALL','MBPP','GSM8K'):
            rr=[r for r in rows if r['family']==family and r['condition']=='C3_K3' and
                (domain=='ALL' or r['task'].startswith(domain+'/'))]
            expected=192 if domain=='ALL' else 96
            assert len(rr)==expected and len({r['slot'] for r in rr})==expected
            assert all(r['contract_valid'] and r['native_counts']['tokens_predicted']==r['length'] for r in rr)
            for r in rr:
                n=r['native_counts'];assert 0<=n['draft_n_accepted']<=n['draft_n']
            proposed=sum(r['native_counts']['draft_n'] for r in rr)
            accepted=sum(r['native_counts']['draft_n_accepted'] for r in rr)
            lengths=[r['length'] for r in rr];tids=sorted({r['task'] for r in rr})
            prompts=[len(t['prompt_ids']) for t in inputs['families'][family] if t['id'] in tids]
            assert len(prompts)==len(tids)
            ratios={}
            for a,b in (('R','M3'),('M3','C3_K3'),('R','C3_K3')):
                logs=[]
                for session in range(2):
                    per=[]
                    for tid in tids:
                        tt=[]
                        for arm in (a,b):
                            prices=[r['wall_ms'] for r in rows if r['family']==family and r['condition']==arm
                                    and r['session']==session and r['task']==tid]
                            assert len(prices)==4 and all(math.isfinite(z) and z>0 for z in prices)
                            tt.append(statistics.median(prices))
                        per.append(math.log(tt[0]/tt[1]))
                    logs.append(statistics.mean(per))
                ratios[a+'/'+b]=math.exp(statistics.mean(logs))
            panel[domain]={'requests':expected,'unique_tasks':len(tids),'draft_n':proposed,
                'draft_n_accepted':accepted,'pooled_native_accepted_over_drafted':accepted/proposed,
                'mean_request_native_fraction':statistics.mean(r['native_counts']['draft_n_accepted']/r['native_counts']['draft_n'] for r in rr),
                'drafted_per_output_id':proposed/sum(lengths),'output_ids_median':statistics.median(lengths),
                'prompt_ids_median_unique_tasks':statistics.median(prompts),'cap_stop_requests':sum(r['stop_type']=='limit' for r in rr),
                'cap_stop_fraction':sum(r['stop_type']=='limit' for r in rr)/expected,
                'output_length_bins':dict(collections.Counter('1-32' if n<=32 else '33-64' if n<=64 else '65-127' if n<128 else '128' for n in lengths)),
                'request_ratios':ratios}
        output[family]=panel
    return {'status':'EXPORTED_NATIVE_COUNTER_REANALYSIS_ONLY','source_PR':84,
        'source_head':'59b0f87a7011dad15f5e1146591ae83d9556d0e7','formal_C3_K3_requests':576,
        'families':output,'counter_definition':'unchanged published draft_n_accepted/draft_n; token-weighted ratio, not iid acceptance or per-cycle progress',
        'unavailable':['formal verification/catch-up/rollback row counts','complete phase wall or GPU cost partition','prospective coefficient calibration'],
        'scientific_limit':'published diagnostics recomputed; raw native arrays/scientific CAS not independently restored here',
        'historical_Qwen':'approximately1.035 and new1.106 are different frozen designs; no optimization A/B or difference attribution'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();root=Path(a.root);base=root/'benchmarks/jsa_third_family_v1'
    files=('RESULTS.json','CONFIRMATION_INPUTS.json')
    # Input SHA is checked against SOURCE_BINDINGS, avoiding reliance on a copied literal.
    bindings=json.loads((root/'docs/experiments/rtx_evidence_closeout_20261011/SOURCE_BINDINGS.json').read_text())
    pinned={Path(b['path']).name:b['sha'] for b in bindings['files']}
    bound={};data={}
    for name in files:
        raw=(base/name).read_bytes();git=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        assert git==pinned[name], 'source Git blob differs'
        bound[name]={'git_blob_sha':git,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
        data[name]=json.loads(raw)
    result=prior(data['RESULTS.json'],data['CONFIRMATION_INPUTS.json']);result['source_bindings']=bound
    Path(a.out).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'output':a.out,'C3_requests':576}))

if __name__=='__main__':main()
