"""Post-run integrity, repetition and frozen-source audits; no inference."""
import json,subprocess
from pathlib import Path
from run import HERE,OLD,ORIGINAL,ASSET,read,save,sha

def main():
    count={};raw_hash_checks=0;source_commits={};binaries={};raw_repeat_checks=0
    for panel,n in [('engineering',12),('formal',24),('attention',8),('wide-qualification',8),('matched-qualification',8)]:
        files=sorted((HERE/'runs'/panel).glob('*/RESULT.json'));assert len(files)==n
        count[panel]=len(files)
        for p in files:
            r=read(p);assert r['valid']
            assert r.get('historical_equal',r.get('reference_equal',True))
            for name,h in r.get('files',{}).items():assert sha(p.parent/name)==h;raw_hash_checks+=1
            commit=r['source_commit'];subprocess.check_call(['git','cat-file','-e',commit+'^{commit}'],cwd=HERE)
            source_commits.setdefault(panel,set()).add(commit)
            binaries.setdefault(panel,set()).add(r['frontend_sha256'])
    for task in [15,25,18,31]:
        for condition in ['N0','N1']:
            copies=[]
            for rep in range(1,4):
                d=HERE/f'runs/formal/HumanEval-{task}-{condition}-capture-r{rep}'
                assert d.exists()
                copies.append({p.relative_to(d).as_posix():sha(p) for p in (d/'live').glob('*') if p.suffix in ['.state','.f32','.kv']})
            assert copies[0] and copies[0]==copies[1]==copies[2];raw_repeat_checks+=len(copies[0])*3
    kv=read(HERE/'generated/analysis/LOGICAL_KV_COMPARISONS.json');assert len(kv)==12
    assert all(x['prompt_kv_equal'] and x['different_tensor_count']==70 for x in kv)
    assert all(not s['different_positions'] for x in kv for s in x['tensors'] if s['layer']==0)
    counts={'measured':0,'warmup':0};panels={}
    for panel,n,w,ub in [('cost-v2',171,9,None),('cost-wide',304,16,None),('cost-matched',152,8,4)]:
        root=HERE/'runs'/panel;manifest=read(root/'MANIFEST.json');rr=read(root/'RECORDS.json')
        assert len(rr)==n and len(list(root.glob('*_WARMUP.json')))==w
        source_commits[panel]={manifest['source_commit']}
        runner='run_cost.py' if panel=='cost-v2' else ('run_wide.py' if panel=='cost-wide' else 'run_matched.py')
        blob=subprocess.check_output(['git','show',manifest['source_commit']+':'+runner],cwd=HERE)
        import hashlib
        assert hashlib.sha256(blob).hexdigest()==manifest['runner_sha256']
        for r in rr:
            p=root/f"r{r['repetition']}_{r['condition']}_{r['task'].replace('/','-')}.json"
            assert read(p)==r
            assert r['response']['timings']['cache_n']==0
        for p in root.glob('*_WARMUP.json'):
            r=read(p);assert r['timings']['cache_n']==0 and len(r['tokens'])==r['tokens_predicted'] and len(r['tokens'])<=32
        sessions=[]
        for p in sorted(root.glob('*_COMMAND.json')):
            c=read(p)['command'];label=p.stem.replace('_COMMAND','');log=(root/(label+'.log')).read_text(encoding='utf-8',errors='replace')
            import re
            layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',log)
            spec=('--model-draft' in c)
            if layers:assert layers==([('37','37'),('29','29')] if spec else [('37','37')])
            assert c[c.index('--n-gpu-layers')+1]=='all' and c[c.index('--device')+1]=='CUDA0' and c[c.index('--fit')+1]=='off'
            assert 'Device 0: NVIDIA GeForce RTX 5070 Ti Laptop GPU' in log
            actual_ub=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',log)))
            expected_ub=int(c[c.index('--ubatch-size')+1])
            if actual_ub:assert all(x==expected_ub for x in actual_ub)
            if ub:assert expected_ub==ub
            assert c[c.index('--flash-attn')+1]=='off' and c[c.index('--ctx-size')+1]=='4096'
            assert '--no-cache-prompt' in c and '--parallel' in c and c[c.index('--parallel')+1]=='1'
            sessions.append({'label':label,'requested_full_gpu_offload':True,'requested_ub_capacity':expected_ub,
                             'full_gpu_offload_from_log':layers,'actual_ubatches_from_log':actual_ub,
                             'observation_limit':'Default service verbosity suppresses detailed layer/context loader messages; requests/commands/source and CUDA enumeration are audited, CLI qualifiers separately parse full placement/UB logs.',
                             'log_sha256':sha(root/(label+'.log'))})
        panels[panel]={'requests':n,'warmups':w,'sessions':sessions,'manifest_sha256':sha(root/'MANIFEST.json')}
        counts['measured']+=n;counts['warmup']+=w
    b=read(HERE/'SOURCE_BINDINGS.json');assert sha(OLD/'native-build/bin/llama-cli.exe')==b['original_native_frontend_sha256']
    assert sha(ORIGINAL/'scripts/platform/rtx_trajectory_cost_v4/native.py')==b['native_parser_sha256']
    assert sha(OLD/'pinned-source/common/hs_observer.h')==b['old_observer_sha256']
    assert sha(OLD/'pinned-source/tools/server/server-context.cpp')==b['old_server_source_sha256']
    pre=read(HERE/'generated/ASSET_CHECK_PRE_WIDE.json');post={}
    for label,name in [('target','Qwen3-8B-Q8_0.gguf'),('draft','Qwen3-0.6B-Q8_0.gguf')]:
        p=ASSET/'models/gguf'/name;post[label]={'sha256':sha(p),'bytes':p.stat().st_size}
        assert post[label]==pre[label] and post[label]['sha256']==b['expected_model_sha256'][label]
    post['runtime_dlls']={p.name:sha(p) for p in sorted((ASSET/'tools/llama-b10839').glob('*.dll'))}
    assert post['runtime_dlls']==pre['runtime_dlls']
    post['private_cuda_sha256']=sha(HERE/'generated/build/bin/ggml-cuda.dll')
    assert post['private_cuda_sha256']==pre['runtime_dlls']['ggml-cuda.dll']
    post['gpu_post']=subprocess.check_output(['nvidia-smi','--query-gpu=name,driver_version,memory.used','--format=csv,noheader'],text=True).strip()
    save(HERE/'generated/ASSET_CHECK_POST.json',post)
    result={'status':'PASS','cli_complete_trajectories':count,'measured_requests':counts['measured'],
            'excluded_warmups':counts['warmup'],'all_complete_generation_requests':sum(count.values())+sum(counts.values()),
            'raw_result_hash_checks':raw_hash_checks,'formal_bitwise_repeat_raw_files':raw_repeat_checks,
            'source_commits':{k:sorted(v) for k,v in source_commits.items()},'frontend_hashes':{k:sorted(v) for k,v in binaries.items()},
            'panels':panels,'original_assets_unchanged':True,'runtime_dlls_checked':len(post['runtime_dlls']),
            'preparation_failure_before_any_model_execution':{'path':'runs/cost/PREPARATION_FAILURE.json','retained':True},
            'metadata_correction':{'path':'runs/cost-wide/*_COMMAND.json','field':'attention_constraint',
                'issue':'The legacy boolean is true for ordinary_k3, although its frozen runner explicitly sets neither attention flag. Actual environment is sanitized; condition and frozen runner determine mode. Original evidence files are preserved.'}}
    assert (HERE/'runs/cost/PREPARATION_FAILURE.json').exists()
    save(HERE/'generated/analysis/POST_AUDIT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['panels','source_commits','frontend_hashes','metadata_correction']}),flush=True)

if __name__=='__main__':main()
