"""Reuse the established external-CUDA build workflow in an isolated directory."""
import importlib.util,subprocess
from base import HERE,PHASE1,ASSET,read,save,sha

def main():
    assert (HERE/'generated/source/src/hs_scope.h').exists()
    spec=importlib.util.spec_from_file_location('prior_build',PHASE1/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.HERE=HERE;m.SRC=HERE/'generated/source';m.BUILD=HERE/'generated/build';m.main()
    cmd=[str(ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'),'--build',str(m.BUILD),'--target','llama-server','-j','4']
    with (HERE/'generated/build-server.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    if r.returncode:raise RuntimeError('Server build failed; log retained')
    x=read(HERE/'generated/BUILD_IDENTITY.json');x['server_sha256']=sha(m.BUILD/'bin/llama-server.exe')
    x['phase2_patch_identity_sha256']=sha(HERE/'generated/PATCH_IDENTITY.json');save(HERE/'generated/BUILD_IDENTITY.json',x)
    print('Private CLI/server built; no model generation yet.',flush=True)
if __name__=='__main__':main()
