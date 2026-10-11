"""Before any forward: capture-only actual query/head shapes for both model roles."""
from common import *
import shutil
def main():
    src=LOCAL/'native/source';build=LOCAL/'native/build';prior=LOCAL/'native/version01';prior.mkdir(exist_ok=False)
    for name in ['src/llama-graph.cpp','common/hs_observer.h']:
        p=src/name;out=prior/name;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out)
    for name in ['llama-server.exe','llama-cli.exe']:shutil.copyfile(build/'bin'/name,prior/name)
    p=src/'src/llama-graph.cpp';s=p.read_text(encoding='utf-8');before='    if (hs_query_batch && q->ne[1] > 1 && arch == LLM_ARCH_LLAMA) {'
    assert s.count(before)==1
    after='    if (std::getenv("HS_NATIVE_CAPTURE")) cb(q, "hs_attention_q", il); // capture-only actual target/draft head/query shape\n'+before
    p.write_text(s.replace(before,after),encoding='utf-8',newline='\n')
    p=src/'common/hs_observer.h';s=p.read_text(encoding='utf-8');before2='std::strcmp(t->name,"result_output")==0';after2='std::strcmp(t->name,"hs_attention_q-0")==0||'+before2;assert s.count(before2)==1;p.write_text(s.replace(before2,after2),encoding='utf-8',newline='\n')
    cmake='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe';cmd=[cmake,'--build',str(build),'--target','llama-server','llama-cli','-j','4']
    with (LOCAL/'native/capture-shape-build.log').open('xb') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(LOCAL/'native/CAPTURE_SHAPE_PATCH.json',{'scope':'capture-only query tensor naming and observation; no tensor op/arithmetic/algorithm/DLL change','changes':[{'file':'src/llama-graph.cpp','before':before,'after':after},{'file':'common/hs_observer.h','before':before2,'after':after2}],'old_binary_sha256':sha(prior/'llama-server.exe'),'command':cmd,'exit_code':p.returncode,'forwards':0,'utc':now()});assert p.returncode==0
    old=read(PUB/'NATIVE_BUILD.json');dll={n:sha(build/'bin'/n) for n in old['runtime_dlls']};assert dll==old['runtime_dlls']
    shutil.move(PUB/'NATIVE_BUILD.json',PUB/'NATIVE_BUILD_01.json')
    inventory={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file()};save(LOCAL/'native/SOURCE_HASHES_FINAL.json',inventory)
    save(PUB/'NATIVE_BUILD.json',{**old,'binary_sha256':sha(build/'bin/llama-server.exe'),'cli_sha256':sha(build/'bin/llama-cli.exe'),'source_inventory_sha256':sha(LOCAL/'native/SOURCE_HASHES_FINAL.json'),'capture_shape_patch':read(LOCAL/'native/CAPTURE_SHAPE_PATCH.json'),'prior_build_manifest_sha256':sha(PUB/'NATIVE_BUILD_01.json'),'model_forwards':0})
    print('CAPTURE SHAPE BUILD PASS',sha(build/'bin/llama-server.exe'),flush=True)
if __name__=='__main__':main()
