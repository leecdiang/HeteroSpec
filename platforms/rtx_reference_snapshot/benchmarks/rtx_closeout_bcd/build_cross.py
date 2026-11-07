"""Separate diagnostic-only build; one optional isolated state/path block."""
import importlib.util,shutil,subprocess
from close_base import HERE,PHASE1,ASSET,read,save,sha,head,now

def main():
    source=head();src=HERE/'generated/x-source';build=HERE/'generated/x-build';driver=HERE/'generated/x-driver'
    assert not src.exists() and not build.exists();shutil.copytree(HERE/'generated/c-source',src)
    p=src/'common/live_capture.h';s=p.read_text(encoding='utf-8');a='    if (std::getenv("HS_LIVE_FORK")) {';assert s.count(a)==1
    s=s.replace(a,(HERE/'cross_block.h.txt').read_text(encoding='utf-8')+a);s=s.replace('#include <filesystem>','#include <filesystem>\n#include <iterator>');p.write_text(s,encoding='utf-8',newline='\n')
    inventory={};changed={}
    for f in src.rglob('*'):
        if f.is_file():
            rel=f.relative_to(src).as_posix();inventory[rel]=sha(f)
            if inventory[rel]!=sha(HERE/'generated/c-source'/rel):changed[rel]=inventory[rel]
    assert list(changed)==['common/live_capture.h']
    save(HERE/'generated/CROSS_PATCH_IDENTITY.json',{'utc':now(),'source_commit':source,'changed_from_C':changed,'source_inventory':inventory,'block_sha256':sha(HERE/'cross_block.h.txt'),'purpose':'Paid isolated state x current-query-layout diagnostic only; no change to C or D executable.'})
    (driver/'generated').mkdir(parents=True);shutil.copyfile(p,driver/'live_capture.h')
    spec=importlib.util.spec_from_file_location('prior_build',PHASE1/'build.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m.HERE=driver;m.SRC=src;m.BUILD=build;m.main()
    cmd=[str(ASSET/'.venv-analysis/Lib/site-packages/cmake/data/bin/cmake.exe'),'--build',str(build),'--target','llama-server','-j','4']
    with (driver/'generated/build-server.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
    save(driver/'generated/SERVER_BUILD_ATTEMPT.json',{'command':cmd,'exit_code':r.returncode});assert r.returncode==0
    x=read(driver/'generated/BUILD_IDENTITY.json');assert x['original_cuda_equal'];x.update({'server_sha256':sha(build/'bin/llama-server.exe'),'source_commit':source,'patch_identity_sha256':sha(HERE/'generated/CROSS_PATCH_IDENTITY.json')})
    save(HERE/'generated/CROSS_BUILD_IDENTITY.json',x);print('Diagnostic-only crossing frontend built; no model inference.',flush=True)

if __name__=='__main__':main()
