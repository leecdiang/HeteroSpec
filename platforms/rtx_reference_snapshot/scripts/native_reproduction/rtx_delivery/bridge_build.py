"""Link bridge against a freshly rebuilt historical core; replace two selector users."""
import argparse,concurrent.futures,json,pathlib,shutil,subprocess,time
P=pathlib.Path
import sys
# Helpers are shipped alongside this portable adapter.
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from rtx_recover import sha,read,save
def main():
    ap=argparse.ArgumentParser();ap.add_argument('root',type=P);ap.add_argument('--name',default='bridge-build-v2');ap.add_argument('--zig',type=P,required=True);a=ap.parse_args();root=a.root.resolve();code=P(__file__).parent.resolve()
    source=root/'original/native/source';old=root/'clean-build';build=root/a.name;build.mkdir(exist_ok=False);(build/'source').mkdir();(build/'bin').mkdir()
    zig=a.zig.resolve()
    header=(source/'src/hs_scope.h').read_text();first=header.index('inline int layout95()');last=header.index('inline int mask()',first)
    header=header[:first]+'inline int requested_layout=0;\ninline int layout95(){return requested_layout;}\n'+header[last:]
    (build/'source/hs_scope.h').write_text(header,encoding='utf-8',newline='\n')
    for name in ('llama-graph.cpp','llama-context.cpp'):shutil.copyfile(source/'src'/name,build/'source'/name)
    includes=[build/'source',source/'src',old/'src',source/'include',source/'ggml/include',source/'common',source/'vendor']
    records=[]
    def execute(label,argv):
        start=time.perf_counter()
        with (build/(label+'.log')).open('wb') as f:p=subprocess.Popen(list(map(str,argv)),stdout=f,stderr=subprocess.STDOUT);rc=p.wait()
        rec=dict(label=label,argv=list(map(str,argv)),pid=p.pid,exit_code=rc,seconds=time.perf_counter()-start,log_sha256=sha(build/(label+'.log')))
        if rc:raise RuntimeError(str(rec))
        return rec
    for name in ('llama-graph.cpp','llama-context.cpp','worker.cpp'):
        src=code/name if name=='worker.cpp' else build/'source'/name
        records.append(execute(name,[zig,'c++','-std=c++17','-DGGML_BACKEND_DL','-D_CRT_SECURE_NO_WARNINGS','-O3','-DNDEBUG',*[f'-I{p}' for p in includes],'-c',src,'-o',build/(name+'.obj')]))
        save(build/'PROGRESS.json',records)
    shutil.copyfile(old/'src/libllama.a',build/'libllama.a')
    records.append(execute('archive',[zig,'ar','r',build/'libllama.a',build/'llama-graph.cpp.obj',build/'llama-context.cpp.obj']))
    records.append(execute('link',[zig,'c++','-O3',build/'worker.cpp.obj',build/'libllama.a',old/'ggml/src/ggml.a',old/'ggml/src/ggml-base.a',old/'vendor/hash/libvendor-hash.a','-lpsapi','-lws2_32','-o',build/'bin/rtx-bridge.exe']))
    for p in (root/'original/native/bin').glob('*.dll'):shutil.copyfile(p,build/'bin'/p.name)
    save(root/(a.name+'-BUILD.json'),dict(status='BUILT_NOT_QUALIFIED',records=records,files={str(p.relative_to(root)):sha(p) for p in list((build/'bin').glob('*'))+list((build/'source').glob('*'))},worker_sha256=sha(code/'worker.cpp'),compiler_sha256=sha(zig),core_origin='Fresh clean-build; no prior object archive used',change='dynamic selector; new common request driver with k1/k3 and resident/fresh; separate PQ/QB resident contexts avoid layout-blind graph cache reuse'))
    print('BRIDGE_BUILD_PASS',flush=True)
if __name__=='__main__':main()
