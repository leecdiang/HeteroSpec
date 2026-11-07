"""Isolated source/core build against the exact published numerical backend."""
import importlib.util,shutil,subprocess
from common import *
def main():
    cfg=read(LOCAL/'CONFIG.json');restored=Path(cfg['restored']);src=LOCAL/'native/source';build=LOCAL/'native/build';driver=LOCAL/'native/driver'
    assert not src.exists();src.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(restored/'phase2/experiment/generated/source',src)
    from llama_graph_patch import patch
    patch(src)
    old=restored/'phase2/experiment/generated/source';changes={p.relative_to(src).as_posix():sha(p) for p in src.rglob('*') if p.is_file() and (not (old/p.relative_to(src)).exists() or sha(p)!=sha(old/p.relative_to(src)))}
    save(PUB/'NATIVE_PATCH.json',{'upstream':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','source':'restored Phase2 private graph/core','changed_from_phase2':changes,'recipe':'separate Llama dense GQA query-axis view branch; historical Qwen path retained; no precision/kernel change; role/phase and reuse key retained'})
    (driver/'generated').mkdir(parents=True);shutil.copyfile(src/'common/live_capture.h',driver/'live_capture.h')
    spec=importlib.util.spec_from_file_location('prior_build',restored/'phase1/experiment/build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.HERE=driver;m.SRC=src;m.BUILD=build;m.main()
    cmake=Path(cfg['asset'])/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'
    cmd=[str(cmake),'--build',str(build),'--target','llama-server','-j','4']
    with (driver/'generated/build-server.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(driver/'generated/SERVER_BUILD_ATTEMPT.json',{'command':cmd,'exit_code':r.returncode});assert r.returncode==0
    meta=read(driver/'generated/BUILD_IDENTITY.json');meta['server_sha256']=sha(build/'bin/llama-server.exe');meta['source_commit']=head();meta['patch_sha256']=sha(PUB/'NATIVE_PATCH.json');save(PUB/'NATIVE_BUILD.json',meta)
    print('NATIVE BUILD COMPLETE',flush=True)
if __name__=='__main__':main()
