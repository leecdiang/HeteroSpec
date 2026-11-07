"""Read-only request, frozen-implementation and asset integrity audit."""
import hashlib,math,subprocess
from close_base import HERE,PHASE1,PHASE2,ASSET,OLDROOT,EOG,read,save,sha

def main():
    bindings=read(HERE/'SOURCE_BINDINGS.json');pre=bindings['assets_pre'];post={}
    for label,name in [('target','Qwen3-8B-Q8_0.gguf'),('draft','Qwen3-0.6B-Q8_0.gguf')]:
        p=ASSET/'models/gguf'/name;post[label]={'sha256':sha(p),'bytes':p.stat().st_size};assert post[label]==pre[label]
    post['runtime_dlls']={p.name:sha(p) for p in sorted((ASSET/'tools/llama-b10839').glob('*.dll'))};assert post['runtime_dlls']==pre['runtime_dlls']
    save(HERE/'generated/ASSET_CHECK_POST.json',post)
    patch=read(PHASE2/'generated/PATCH_IDENTITY.json');expected={**patch['phase1_source_files_sha256'],**patch['changed_from_phase1']}
    for name,h in patch['phase1_source_files_sha256'].items():assert sha(PHASE1/'generated/source'/name)==h
    for name,h in expected.items():assert sha(PHASE2/'generated/source'/name)==h
    old_bindings=read(PHASE2/'SOURCE_BINDINGS.json')
    for name,key in [('llama-cli.exe','phase1_cli_sha256'),('llama-server.exe','phase1_server_sha256')]:assert sha(PHASE1/'generated/build/bin'/name)==old_bindings[key]
    p1bind=read(PHASE1/'SOURCE_BINDINGS.json');old=OLDROOT/'work/rtx-target-v1'
    for path,key in [(old/'native-build/bin/llama-cli.exe','original_native_frontend_sha256'),(OLDROOT/'scripts/platform/rtx_trajectory_cost_v4/native.py','native_parser_sha256'),(old/'pinned-source/common/hs_observer.h','old_observer_sha256'),(old/'pinned-source/tools/server/server-context.cpp','old_server_source_sha256')]:assert sha(path)==p1bind[key]
    for name,key in [('llama-cli.exe','frontend_sha256'),('llama-server.exe','server_sha256')]:assert sha(PHASE2/'generated/build/bin'/name)==bindings['phase2_build'][key]
    cp=read(HERE/'generated/C_PATCH_IDENTITY.json');cb=read(HERE/'generated/C_BUILD_IDENTITY.json')
    for name,h in cp['source_inventory'].items():assert sha(HERE/'generated/c-source'/name)==h
    assert len(cp['changed_from_phase2'])==1 and cb['patch_identity_sha256']==sha(HERE/'generated/C_PATCH_IDENTITY.json')
    for name,key in [('llama-cli.exe','frontend_sha256'),('llama-server.exe','server_sha256'),('ggml-cuda.dll','retained_cuda_sha256')]:assert sha(HERE/'generated/c-build/bin'/name)==cb[key]
    tasks={t['id']:t for t in read(HERE/'B_INPUTS.json')+read(PHASE2/'INPUTS.json')};panels={};total=0;warmups=0
    expected_counts={'bridge_b':(16,4),'b':(384,16),'c_bridge':(48,2),'c_topology':(16,8),'c':(792,24),'d_reset':(96,4),'d':(96,4)}
    c2=read(HERE/'generated/C2_SELECTION.json')
    if c2['status']=='RUN':expected_counts['c2']=(448,16)
    else:assert c2['status']=='SKIPPED' and not (HERE/'runs/c2').exists()
    c3=read(HERE/'generated/C3_SELECTION.json')
    if c3['status']=='RUN':expected_counts.update({'c3':(448,16),'c3_long':(132,6),'c3_scopes':(16,8)})
    else:assert c3['status']=='SKIPPED' and not (HERE/'runs/c3').exists()
    c4=read(HERE/'generated/C4_SELECTION.json')
    expected_counts['c4_pilot']=(168,6)
    if c4['status']=='RUN':expected_counts.update({'c4':(448,16),'c4_long':(132,6)})
    else:assert c4['status']=='SKIPPED' and not (HERE/'runs/c4').exists() and not (HERE/'runs/c4_long').exists()
    diagnostics=read(HERE/'generated/C_BOUNDARY_DIAGNOSTICS.json')
    if (HERE/'runs/c_boundary_trace').exists():
        for stage in ['c_boundary_trace','c_boundary_state','c_boundary_cross']:
            if (HERE/'runs'/stage/'RECORDS.json').exists():
                n=len(read(HERE/'runs'/stage/'RECORDS.json'));expected_counts[stage]=(n,n)
    if (HERE/'generated/CROSS_BUILD_IDENTITY.json').exists():
        xp=read(HERE/'generated/CROSS_PATCH_IDENTITY.json');xb=read(HERE/'generated/CROSS_BUILD_IDENTITY.json')
        for name,h in xp['source_inventory'].items():assert sha(HERE/'generated/x-source'/name)==h
        assert xb['patch_identity_sha256']==sha(HERE/'generated/CROSS_PATCH_IDENTITY.json') and len(xp['changed_from_C'])==1
        for name,key in [('llama-cli.exe','frontend_sha256'),('llama-server.exe','server_sha256'),('ggml-cuda.dll','retained_cuda_sha256')]:assert sha(HERE/'generated/x-build/bin'/name)==xb[key]
    for stage,(count,nwarm) in expected_counts.items():
        root=HERE/'runs'/stage;manifest=read(root/'MANIFEST.json');rows=read(root/'RECORDS.json');assert len(rows)==count
        keys=[(r['task'],r['condition'],r['repetition'],r['requested_cap'],r.get('width_k')) for r in rows];assert len(set(keys))==len(keys)
        frozen={}
        runner='c2.py' if stage in ['c2','c3','c4'] else ('c4.py' if stage.startswith('c4_') else ('c3.py' if stage.startswith('c3_') else ('diagnostics.py' if stage in ['c_boundary_trace','c_boundary_state'] else ('cross.py' if stage=='c_boundary_cross' else f'run_{"b" if stage in ["b","bridge_b"] else ("d" if stage in ["d","d_reset"] else "c")}.py'))))
        source_files=['close_base.py','close_server.py','PROTOCOL.md',runner]+(['c4.py','c2.py'] if stage.startswith('c4') else [])
        for name in set(source_files):
            data=subprocess.check_output(['git','show',manifest['source_commit']+':'+name],cwd=HERE);frozen[name]=hashlib.sha256(data).hexdigest()
        # Runner identity must remain equal to the implementation used online.
        for name in set(source_files)-{'PROTOCOL.md'}:assert frozen[name]==sha(HERE/name)
        for r in rows:
            assert read(HERE/r['record_relative_path'])==r and r['source_commit']==manifest['source_commit']
            response=r['response'];ids=response['tokens'];t=tasks[r['task']]
            assert response['prompt']==t['formatted_prompt'] and r['formatted_prompt_sha256']==hashlib.sha256(t['formatted_prompt'].encode()).hexdigest()
            assert ids and len(ids)==response['tokens_predicted'] and len(ids)<=r['requested_cap'] and response['timings']['cache_n']==0 and not response['truncated']
            assert r['endpoint']==('EOS' if response['stop_type']=='eos' else 'limit') and (len(ids)==r['requested_cap'] or r['endpoint']=='EOS')
            assert ((ids[-1] in EOG)==(r['endpoint']=='EOS')) and not any(x in EOG for x in ids[:-1])
            assert all(math.isfinite(x) and x>0 for x in [r['wall_ms'],response['timings']['predicted_ms']])
            command=read((HERE/r['record_relative_path']).parent/'COMMAND.json');args=command['command']
            assert command['mask']==r['mask'] and command['spec']==r['spec'] and command['server_sha256']==r['server_sha256']
            assert args[args.index('--ubatch-size')+1]==str(r['ub']) and command['capture']==(stage in ['c_topology','d_reset','c_boundary_trace','c_boundary_state','c_boundary_cross','c3_scopes','c4_pilot'])
            for flag,value in [('--device','CUDA0'),('--n-gpu-layers','all'),('--ctx-size','4096'),('--flash-attn','off'),('--parallel','1'),('--threads','24'),('--threads-batch','24')]:assert args[args.index(flag)+1]==value
            if r['spec']:assert args[args.index('--spec-draft-n-max')+1]==str(r['k'])
            assert '--no-cache-prompt' in args and '--cache-ram' in args
        warms=list(root.glob('*/WARMUP.json'));assert len(warms)==nwarm
        for p in warms:
            r=read(p);assert r['timings']['cache_n']==0 and len(r['tokens'])==r['tokens_predicted'] and len(r['tokens'])<=32
        panels[stage]={'requests':count,'warmups':nwarm,'source_commit':manifest['source_commit'],'frozen_files_sha256':frozen,'records_sha256':sha(root/'RECORDS.json')}
        total+=count;warmups+=nwarm
    hashes={p.relative_to(HERE).as_posix():sha(p) for p in (HERE/'runs').rglob('*') if p.is_file()};save(HERE/'generated/RAW_FILE_HASHES.json',hashes)
    fixed_ub_count=sum(n+w for key,(n,w) in expected_counts.items() if key.startswith('c4'))
    out={'status':'PASS','panel_requests':total,'excluded_warmups':warmups,'all_complete_generation_requests':total+warmups,'complete_generations_before_boundary_diagnostics':total+warmups-diagnostics.get('paid_requests',0)-diagnostics.get('warmups',0)-fixed_ub_count,'fixed_ub_complete_generations':fixed_ub_count,'panels':panels,
         'boundary_paid_requests':diagnostics.get('paid_requests',0),'boundary_warmups':diagnostics.get('warmups',0),'paid_auxiliary_target_decode_calls':diagnostics.get('auxiliary_target_decode_calls',0),
         'raw_file_hashes':len(hashes),'phase1_source_checked':len(patch['phase1_source_files_sha256']),'phase2_source_checked':len(expected),'C_source_checked':len(cp['source_inventory']),
         'models_runtime_unchanged':True,'published_Dlls_checked':len(post['runtime_dlls']),'prior_archives':'separate immutable dependencies, verified when archived'}
    save(HERE/'generated/POST_AUDIT.json',out);print({k:v for k,v in out.items() if k!='panels'},flush=True)

if __name__=='__main__':main()
