"""Bypass diagnostic metadata work when capture is disabled; retain old binaries."""
import shutil
from run import HERE,save,sha

def apply():
    src=HERE/'generated/source/common/hs_observer.h'
    s=src.read_text(encoding='utf-8')
    marker='    if(!enabled())return llama_decode(c,b); // no observer metadata or forced sync\n'
    if marker in s:return
    names=['llama-cli.exe','llama-server.exe']
    identity={}
    for name in names:
        p=HERE/'generated/build/bin'/name
        dst=HERE/'generated'/('qualified-wide-'+name)
        assert not dst.exists()
        shutil.copyfile(p,dst);identity[name]=sha(dst)
    identity['build_identity']=__import__('json').loads((HERE/'generated/BUILD_IDENTITY.json').read_text())
    save(HERE/'generated/QUALIFIED_WIDE_BUILD.json',identity)
    anchor='inline int decode(llama_context*c,llama_batch b,const char*role){\n'
    assert s.count(anchor)==1
    src.write_text(s.replace(anchor,anchor+marker),encoding='utf-8',newline='\n')

if __name__=='__main__':apply()
