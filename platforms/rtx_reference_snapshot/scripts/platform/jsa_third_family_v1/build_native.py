"""Restore PR80 private core, bind draft UB1 and capture-only mechanism records."""
from common import *
import shutil,importlib.util
def main():
    src=LOCAL/'native/source';driver=LOCAL/'native/driver';build=LOCAL/'native/build'
    restored=read(OLD/'benchmarks/jsa_rtx_validation_v1/RESTORE_CHECK.json')
    assert sha(restored['private_archive']['path'])==restored['private_archive']['sha256']
    original=Path(restored['restored_root'])/'jsa/native/source'
    contract=read(OLD/'benchmarks/jsa_rtx_validation_v1/SOURCE_RUNTIME_CONTRACT.json')
    for name,h in contract['files_sha256'].items():assert sha(original/name)==h
    assert not src.exists();shutil.copytree(original,src)
    p=src/'tools/server/server-context.cpp';s=p.read_text(encoding='utf-8');changes=[]
    def replace(a,b):
        nonlocal s
        assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b);changes.append({'before':a,'after':b})
    # The CLI has no draft-UB option. This binds the setting already required by PR83.
    replace('common_params params_dft = common_base_params_to_speculative(params_base);',
            'common_params params_dft = common_base_params_to_speculative(params_base);\n                params_dft.n_ubatch = 1; // PR83 fixed draft physical batch; no algorithm change')
    replace('            slot.stats.n_draft_tokens += draft.size();',
            '            slot.stats.n_draft_tokens += draft.size();\n            if (hs::enabled()) hs::emit({{"event","draft_proposal"},{"slot",slot.id},{"ids",draft},{"pending",slot.sampled},{"n_past",slot.prompt.n_tokens()}});')
    replace('                slot.spec_i_batch.clear();',
            '                if (hs::enabled()) hs::emit({{"event","verify_result"},{"slot",slot.id},{"proposed_ids",slot.spec_draft},{"accepted_plus_last",accepted},{"query_indices",slot.spec_i_batch},{"replay",slot.spec_is_replay},{"rollback_count",slot.spec_draft.size()+1-accepted.size()}});\n                slot.spec_i_batch.clear();')
    replace('            slot.mem.seq_rm(slot.id, slot.prompt.tokens.pos_next(), -1);\n\n            for (size_t i = 0; i < ids.size(); ++i)',
            '            slot.mem.seq_rm(slot.id, slot.prompt.tokens.pos_next(), -1);\n            if (hs::enabled()) hs::emit({{"event","verify_rollback"},{"slot",slot.id},{"kept_position_next",slot.prompt.tokens.pos_next()},{"actual_positions",hs::position(slot.ctx_tgt)},{"accepted_ids",ids}});\n\n            for (size_t i = 0; i < ids.size(); ++i)')
    p.write_text(s,encoding='utf-8',newline='\n')
    save(LOCAL/'native/PATCH.json',{'upstream':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','restored_archive_sha256':restored['private_archive']['sha256'],'old_source_contract':contract,'original_server_context_sha256':sha(original/'tools/server/server-context.cpp'),'patched_server_context_sha256':sha(p),'changes':changes,'scope':'Required draft UB1 parameter binding and capture-only integer/token/state-position records; original dense Llama/Qwen graphs, arithmetic, sampling and CUDA DLLs unchanged','model_forwards':0})
    (driver/'generated').mkdir(parents=True);shutil.copyfile(src/'common/live_capture.h',driver/'live_capture.h')
    spec=importlib.util.spec_from_file_location('prior_build',REPO.parent/'recovered/phase1/experiment/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=driver;m.SRC=src;m.BUILD=build;m.main()
    cmake=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe')
    cmd=[str(cmake),'--build',str(build),'--target','llama-server','-j','4']
    with (LOCAL/'native/build-server.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(LOCAL/'native/SERVER_BUILD.json',{'command':cmd,'exit_code':r.returncode,'utc':now()});assert r.returncode==0
    old_build=read(OLD/'benchmarks/jsa_rtx_validation_v1/NATIVE_BUILD.json')
    actual={}
    for name,h in old_build['all_runtime_dlls'].items():
        actual[name]=sha(build/'bin'/name);assert actual[name]==h
    source={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()}
    save(LOCAL/'native/SOURCE_HASHES.json',source)
    save(PUB/'NATIVE_BUILD.json',{'status':'BUILT_NOT_ENGINEERING_QUALIFIED','binary_sha256':sha(build/'bin/llama-server.exe'),'compiler_sha256':m.sha(Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')),'runtime_dlls':actual,'published_numerical_stack_unchanged':True,'source_inventory_sha256':sha(LOCAL/'native/SOURCE_HASHES.json'),'source_files':len(source),'patch':read(LOCAL/'native/PATCH.json'),'model_forwards':0})
    print('NATIVE BUILD COMPLETE; published numerical DLL hashes all match',flush=True)
if __name__=='__main__':main()
