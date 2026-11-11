"""Integrity audit of retained Phase 2 evidence; never runs a model."""
import hashlib,json,re,subprocess
from base import HERE,PHASE1,ASSET,OLD,ORIGINAL,read,save,sha
from engineering import inspect_trace

def main():
    bindings=read(HERE/'SOURCE_BINDINGS.json');build=read(HERE/'generated/BUILD_IDENTITY.json')
    patch=read(HERE/'generated/PATCH_IDENTITY.json');inputs=read(HERE/'INPUTS.json');tasks={t['id']:t for t in inputs}
    assert sha(PHASE1/'COST_INPUTS.json')==bindings['phase1_inputs_sha256']
    assert read(PHASE1/'COST_INPUTS.json')==inputs
    for name,key in [('llama-cli.exe','phase1_cli_sha256'),('llama-server.exe','phase1_server_sha256')]:
        assert sha(PHASE1/'generated/build/bin'/name)==bindings[key]
    for name,h in patch['phase1_source_files_sha256'].items():assert sha(PHASE1/'generated/source'/name)==h
    expected_source={**patch['phase1_source_files_sha256'],**patch['changed_from_phase1']}
    assert {p.relative_to(HERE/'generated/source').as_posix() for p in (HERE/'generated/source').rglob('*') if p.is_file()}==set(expected_source)
    for name,h in expected_source.items():assert sha(HERE/'generated/source'/name)==h
    assert sha(HERE/'generated/PATCH_IDENTITY.json')==build['phase2_patch_identity_sha256']
    for name,h in patch['changed_from_phase1'].items():assert sha(HERE/'generated/source'/name)==h
    for name,h in build['changed_source_files'].items():assert sha(HERE/'generated/source'/name)==h
    for name,key in [('llama-cli.exe','frontend_sha256'),('llama-server.exe','server_sha256'),('ggml-cuda.dll','retained_cuda_sha256')]:
        assert sha(HERE/'generated/build/bin'/name)==build[key]
    original_bindings=read(PHASE1/'SOURCE_BINDINGS.json')
    for path,key in [(OLD/'native-build/bin/llama-cli.exe','original_native_frontend_sha256'),
                     (ORIGINAL/'scripts/platform/rtx_trajectory_cost_v4/native.py','native_parser_sha256'),
                     (OLD/'pinned-source/common/hs_observer.h','old_observer_sha256'),
                     (OLD/'pinned-source/tools/server/server-context.cpp','old_server_source_sha256')]:
        assert sha(path)==original_bindings[key]
    pre=bindings['model_runtime_pre'];post={}
    for label,name in [('target','Qwen3-8B-Q8_0.gguf'),('draft','Qwen3-0.6B-Q8_0.gguf')]:
        p=ASSET/'models/gguf'/name;post[label]={'sha256':sha(p),'bytes':p.stat().st_size};assert post[label]==pre[label]
    post['runtime_dlls']={p.name:sha(p) for p in sorted((ASSET/'tools/llama-b10839').glob('*.dll'))}
    assert post['runtime_dlls']==pre['runtime_dlls'];save(HERE/'generated/ASSET_CHECK_POST.json',post)
    engineering=read(HERE/'generated/ENGINEERING_QUALIFICATION.json');assert engineering['status']=='PASS'
    raw_checks=0
    for r in engineering['records']:
        assert r['valid'] and r['original_reference_equal'];assert r['ids']==tasks[f'HumanEval/{r["task"]}']['original_reference_ids']
        d=HERE/'runs/engineering'/f'HumanEval-{r["task"]}-{r["kind"]}'
        assert read(d/'RESULT.json')==r
        for name,h in r['files'].items():assert sha(d/name)==h;raw_checks+=1
    for m in [3,12,5,10]:
        d=HERE/'runs/engineering'/f'scope-{m}';proof=inspect_trace(d/'trace.jsonl',m,3)
        expected=next(x for x in engineering['selective_scope_checks'] if x['mask']==m);assert proof==expected['proof']
        rr=[read(d/f'REQUEST-{n}.json') for n in [1,2]]
        assert rr[0]['response']['tokens']==rr[1]['response']['tokens'] and rr[0]['endpoint']==rr[1]['endpoint']
    panels={};total=0;warmups=4;qualified=0;nonreference=0
    for stage in ['a1','a2','a3']:
        root=HERE/'runs'/stage;manifest=read(root/'MANIFEST.json');rr=read(root/'RECORDS.json')
        assert len(rr)==manifest['request_cap'] and manifest['inputs_sha256']==sha(HERE/'INPUTS.json')
        assert manifest['protocol_sha256']==sha(HERE/'MASTER_PROTOCOL.md') and manifest['build_identity']==build
        assert {(r['task'],r['condition'],r['repetition']) for r in rr}=={
            (t,c['name'],n) for t in manifest['tasks'] for c in manifest['conditions'] for n in range(1,manifest['repetitions']+1)}
        assert len(rr)==len({(r['task'],r['condition'],r['repetition']) for r in rr})
        frozen={}
        for name in ['MASTER_PROTOCOL.md','run_panel.py','server.py','base.py','CONFIG.json','INPUTS.json']:
            b=subprocess.check_output(['git','show',manifest['source_commit']+':'+name],cwd=HERE)
            frozen[name]=hashlib.sha256(b).hexdigest()
        for r in rr:
            assert r['source_commit']==manifest['source_commit'];t=tasks[r['task']];response=r['response']
            assert response['prompt']==t['formatted_prompt'] and response['timings']['cache_n']==0
            assert r['formatted_prompt_sha256']==hashlib.sha256(t['formatted_prompt'].encode()).hexdigest()
            assert (response['tokens']==t['original_reference_ids'] and r['endpoint']==t['original_endpoint'])==r['original_reference_equal']
            p=root/f'r{r["repetition"]}-{r["condition"]}'/(r['task'].replace('/','-')+'.json');assert read(p)==r
            assert response['tokens_predicted']==len(response['tokens']) and len(response['tokens'])<=t['cap']
            if stage!='a1' and r['condition'] in ['target3','mask15']:assert r['original_reference_equal']
        sessions=[]
        for rep in range(1,manifest['repetitions']+1):
            for c in manifest['conditions']:
                d=root/f'r{rep}-{c["name"]}';command=read(d/'COMMAND.json');args=command['command']
                assert command['server_sha256']==build['server_sha256'] and not command['capture']
                assert command['mask']==c['mask'] and command['spec']==c['spec']
                for flag,value in [('--device','CUDA0'),('--n-gpu-layers','all'),('--fit','off'),('--ubatch-size','4'),
                                   ('--ctx-size','4096'),('--flash-attn','off'),('--parallel','1'),('--threads','24'),('--threads-batch','24')]:
                    assert args[args.index(flag)+1]==value
                assert ('--model-draft' in args)==c['spec'] and '--no-cache-prompt' in args
                if c['spec']:assert args[args.index('--spec-draft-n-max')+1]=='3'
                warm=read(d/'WARMUP.json');assert warm['timings']['cache_n']==0 and len(warm['tokens'])==warm['tokens_predicted'] and len(warm['tokens'])<=32
                log=(d/'server.log').read_text(encoding='utf-8',errors='replace')
                assert 'Device 0: NVIDIA GeForce RTX 5070 Ti Laptop GPU' in log
                layers=re.findall(r'load_tensors: offloaded (\d+)/(\d+) layers to GPU',log)
                if layers:assert layers==([('37','37'),('29','29')] if c['spec'] else [('37','37')])
                actual_ub=list(map(int,re.findall(r'llama_context: n_ubatch\s*=\s*(\d+)',log)))
                if actual_ub:assert all(x==4 for x in actual_ub)
                if stage=='a3':
                    for name in ['GPU_PRE.json','GPU_POST.json']:
                        assert read(d/name)['outside_request_timer']
                sessions.append({'name':d.name,'log_sha256':sha(d/'server.log'),'detailed_layer_messages':layers,'detailed_ub_messages':actual_ub})
        matches=sum(r['original_reference_equal'] for r in rr);qualified+=matches;nonreference+=len(rr)-matches
        count_warm=len(list(root.glob('*/WARMUP.json')));assert count_warm==manifest['warmups']
        panels[stage]={'requests':len(rr),'reference_matches':matches,'warmups':count_warm,'source_commit':manifest['source_commit'],
                       'frozen_files_sha256':frozen,'sessions':sessions,'manifest_sha256':sha(root/'MANIFEST.json')}
        total+=len(rr);warmups+=count_warm
    raw_files={p.relative_to(HERE).as_posix():sha(p) for p in (HERE/'runs').rglob('*') if p.is_file()}
    save(HERE/'generated/analysis/RAW_FILE_HASHES.json',raw_files)
    failures=list((HERE/'generated').glob('BUILD_PREPARATION_FAILURE_*.json'));assert len(failures)==1
    assert read(failures[0])['model_executions']==0
    result={'status':'PASS','cli_complete_trajectories':8,'resident_qualification_requests':8,'panel_measured_requests':total,
            'excluded_warmups':warmups,'all_complete_generation_requests':8+8+total+warmups,
            'panel_reference_matches':qualified,'panel_nonreference_requests':nonreference,'panels':panels,
            'old_cli_result_hash_checks':raw_checks,'raw_files_sha256_bound':len(raw_files),'original_assets_unchanged':True,
            'phase1_source_files_checked':len(patch['phase1_source_files_sha256']),'runtime_dlls_checked':len(post['runtime_dlls']),
            'phase2_source_files_checked':len(expected_source),
            'preparation_failure':{'path':failures[0].relative_to(HERE).as_posix(),'model_executions':0,'retained':True},
            'placement_observation_limit':'Normal server verbosity suppresses detailed offload/UB lines; commanded values and CUDA enumeration are audited, and CLI qualifiers separately parse placement/UB.'}
    save(HERE/'generated/analysis/POST_AUDIT.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['panels']}),flush=True)

if __name__=='__main__':main()
