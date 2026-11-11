"""Copy both historical runtimes and add heavy-mode read-only evidence hooks."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time

HERE=Path(__file__).resolve().parent
WORK=HERE.parents[3]
ROOT=WORK/'amended-native'
ASSET=Path('D:/HeteroSpec-PC')

def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def replace(text,old,new):
    if text.count(old)!=1:raise ValueError('observer source anchor differs: '+old[:80])
    return text.replace(old,new)

def main():
    ROOT.mkdir(parents=True,exist_ok=False)
    manifests=[]
    for variant,parent in [('original',Path('D:/hsc95/native/source')),('metadata4',Path('D:/hsc95/native-repair/source'))]:
        root=ROOT/variant;source=root/'source';root.mkdir()
        shutil.copytree(parent,source)
        before={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
        save(root/'PARENT_SOURCE_HASHES.json',before)
        path=source/'common/hs_observer.h';text=path.read_text(encoding='utf-8')
        text=replace(text,'#include "capture95.h"','#include "capture95.h"\n#include "jsa_observer.h"')
        text=replace(text,'    if(q95capture::callback(t,ask))return true;', '    if(jsa_observer::geometry(t,ask))return true;\n    if(q95capture::callback(t,ask))return true;')
        text=replace(text,'    auto before=position(c);int rc=llama_decode(c,b);hsc::decode_end();llama_synchronize(c);',
            '    auto before=position(c);jsa_observer::begin(c);int rc=llama_decode(c,b);hsc::decode_end();llama_synchronize(c);\n    if(rc==0)jsa_observer::logits(c,b,role);')
        text=replace(text,'    if(!enabled())return;const float*l=llama_get_logits_ith(c,idx);',
            '    if(!enabled())return;jsa_observer::sample(c,idx,id);const float*l=llama_get_logits_ith(c,idx);')
        path.write_bytes(text.encode())
        shutil.copyfile(HERE/'jsa_observer.h',source/'common/jsa_observer.h')
        path=source/'src/llama-graph.cpp';text=path.read_text(encoding='utf-8')
        text=replace(text,'        ggml_flash_attn_ext_set_prec (cur, GGML_PREC_F32);',
            '        ggml_flash_attn_ext_set_prec (cur, GGML_PREC_F32);\n        if(hsc::is_heavy())cb(cur,"hs_jsa_flash",il);')
        path.write_bytes(text.encode())
        path=source/'tools/server/server-context.cpp';text=path.read_text(encoding='utf-8')
        text=replace(text,'            hsc::commit();',
            '            hsc::commit();\n            if(hs::enabled())hs::emit({{"event","committed_token"},{"id",result.tok},{"origin",int(hsc::w.current)},{"output_index",slot.generated_tokens.size()-1},{"pending_id",slot.sampled},{"target_positions",hs::position(slot.ctx_tgt)}});')
        anchor='            if (hs::enabled()) hs::emit({{"event","verify_rollback"}'
        if text.count(anchor)!=1:raise ValueError('rollback source anchor differs')
        text=text.replace(anchor,'            if(hs::enabled() && slot.ctx_dft)hs::emit({{"event","draft_reconciled"},{"positions",hs::position(slot.ctx_dft)},{"pending_id",slot.sampled},{"next_target_position",slot.prompt.tokens.pos_next()}});\n'+anchor)
        path.write_bytes(text.encode())
        after={p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}
        changed=[name for name in after if after[name]!=before.get(name)]
        if set(changed)!={'common/hs_observer.h','common/jsa_observer.h','src/llama-graph.cpp','tools/server/server-context.cpp'}:
            raise ValueError('unexpected source change')
        save(root/'SOURCE_HASHES.json',after)
        cmake=ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe';zig=ASSET/'.venv-analysis/Lib/site-packages/ziglang/zig.exe'
        inherited=json.loads(Path('D:/hs-qb-confirmation-v02/NATIVE_BUILD.json').read_bytes())
        if sha(cmake)!=inherited['cmake_sha256'] or sha(zig)!=inherited['compiler_sha256']:raise ValueError('compiler drift')
        build=root/'build'
        configure=[str(cmake),'-S',str(source),'-B',str(build),'-G','Ninja',
          '-DCMAKE_MAKE_PROGRAM='+str(ASSET/'.venv-analysis/Scripts/ninja.exe'),
          '-DCMAKE_C_COMPILER='+str(zig),'-DCMAKE_C_COMPILER_ARG1=cc','-DCMAKE_CXX_COMPILER='+str(zig),'-DCMAKE_CXX_COMPILER_ARG1=c++',
          '-DCMAKE_AR='+str(ASSET/'scripts/debug/cuda_divergence/zig-ar.cmd'),'-DCMAKE_RANLIB='+str(ASSET/'scripts/debug/cuda_divergence/zig-ranlib.cmd'),
          '-DCMAKE_BUILD_TYPE=Release','-DBUILD_SHARED_LIBS=OFF','-DGGML_BACKEND_DL=ON','-DGGML_CPU=OFF','-DGGML_CUDA=OFF',
          '-DLLAMA_SUBPROCESS=OFF','-DLLAMA_BUILD_APP=OFF','-DLLAMA_BUILD_TESTS=OFF','-DLLAMA_BUILD_EXAMPLES=OFF','-DLLAMA_BUILD_MTMD=OFF',
          '-DLLAMA_OPENSSL=OFF','-DLLAMA_BUILD_UI=OFF','-DLLAMA_USE_PREBUILT_UI=OFF','-DLLAMA_BUILD_NUMBER=10839','-DLLAMA_BUILD_COMMIT=0cae43063',
          '-DCMAKE_EXE_LINKER_FLAGS=-lpsapi','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
        attempts=[]
        for label,command in [('configure',configure),('build',[str(cmake),'--build',str(build),'--target','llama-server','-j','4'])]:
            tick=time.perf_counter()
            with (root/(label+'.log')).open('xb') as log:
                process=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=900)
            receipt={'label':label,'exit_code':process.returncode,'seconds':time.perf_counter()-tick,'command':command,'log_sha256':sha(root/(label+'.log'))}
            save(root/(label+'-ATTEMPT.json'),receipt);attempts.append(receipt)
            if process.returncode:raise ValueError(variant+' '+label+' failed; preserve log')
        for name,want in inherited['numerical_DLL_sha256'].items():
            path=Path('D:/hs-qb-confirmation-v02/native/build/bin')/name
            if sha(path)!=want:raise ValueError('numerical library drift')
            shutil.copyfile(path,build/'bin'/name)
        manifest={'variant':variant,'status':'BUILT_NOT_MODEL_QUALIFIED','source_parent':str(parent),
                  'source_inventory_sha256':sha(root/'SOURCE_HASHES.json'),'changed_source_paths':changed,
                  'server':str(build/'bin/llama-server.exe'),'server_sha256':sha(build/'bin/llama-server.exe'),
                  'numerical_DLL_sha256':inherited['numerical_DLL_sha256'],'attempts':attempts,
                  'compiler_sha256':sha(zig),'cmake_sha256':sha(cmake),'new_model_requests':0}
        save(root/'NATIVE_BUILD.json',manifest);manifests.append(manifest)
        print(variant,'observer build complete',flush=True)
    save(ROOT/'BUILDS.json',manifests)

if __name__=='__main__':main()
