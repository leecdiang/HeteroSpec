"""Private width-eight frontend; preserve released CUDA and all prior builds."""
import importlib.util,shutil,subprocess
from close_base import HERE,PHASE1,PHASE2,ASSET,read,save,sha,head,now

def main():
    source=head();src=HERE/'generated/c-source';build=HERE/'generated/c-build';driver=HERE/'generated/c-driver'
    assert not src.exists() and not build.exists()
    shutil.copytree(PHASE2/'generated/source',src)
    p=src/'src/llama-graph.cpp';s=p.read_text(encoding='utf-8')
    a='GGML_ASSERT(q->ne[1] <= 4 && q->ne[3] == 1 && k->ne[3] == 1);'
    assert s.count(a)==1;s=s.replace(a,a.replace('<= 4','<= 8'));p.write_text(s,encoding='utf-8',newline='\n')
    changed={};inventory={}
    for f in src.rglob('*'):
        if f.is_file():
            rel=f.relative_to(src).as_posix();inventory[rel]=sha(f)
            if sha(PHASE2/'generated/source'/rel)!=inventory[rel]:changed[rel]=inventory[rel]
    assert list(changed)==['src/llama-graph.cpp']
    save(HERE/'generated/C_PATCH_IDENTITY.json',{'source_commit':source,'utc':now(),'changed_from_phase2':changed,'source_inventory':inventory,
          'only_semantic_extension':'query-batch width assertion 4 to 8; legacy scalar guard unchanged','phase2_graph_sha256':sha(PHASE2/'generated/source/src/llama-graph.cpp')})
    (driver/'generated').mkdir(parents=True);shutil.copyfile(src/'common/live_capture.h',driver/'live_capture.h')
    spec=importlib.util.spec_from_file_location('prior_build',PHASE1/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.HERE=driver;m.SRC=src;m.BUILD=build;m.main()
    cmd=[str(ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'),'--build',str(build),'--target','llama-server','-j','4']
    with (driver/'generated/build-server.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(driver/'generated/SERVER_BUILD_ATTEMPT.json',{'command':cmd,'exit_code':r.returncode})
    assert r.returncode==0
    x=read(driver/'generated/BUILD_IDENTITY.json');x.update({'server_sha256':sha(build/'bin/llama-server.exe'),'patch_identity_sha256':sha(HERE/'generated/C_PATCH_IDENTITY.json'),'source_commit':source})
    assert x['original_cuda_equal'];save(HERE/'generated/C_BUILD_IDENTITY.json',x)
    print('C private CLI/server built; no inference in build.',flush=True)

if __name__=='__main__':main()
