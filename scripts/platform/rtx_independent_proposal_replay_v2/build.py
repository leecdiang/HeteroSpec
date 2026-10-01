"""Compile small separated frontends; link no replacement llama or CUDA code."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from prepare import ROOT,STUDY,save
def main():
    src=ROOT/'work/pinned-source';out=ROOT/'work/h2-bin';out.mkdir(exist_ok=True)
    zig=Path('D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe')
    source=Path(__file__).with_name('worker.cpp');attempt=[]
    for role,define in [('P',['-DPROPOSER_ONLY']),('R',[])]:
        cmd=[str(zig),'c++','-std=c++17','-O2','-target','x86_64-windows-gnu','-I'+str(src/'include'),'-I'+str(src/'ggml/include'),'-I'+str(src/'vendor/nlohmann'),str(source),*define,'-lpsapi','-o',str(out/(role+'.exe'))]
        with (ROOT/'work'/('build-'+role+'.log')).open('wb') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
        attempt.append({'role':role,'command':cmd,'exit_code':p.returncode});save(STUDY/'BUILD_ATTEMPTS.json',attempt)
        if p.returncode:raise RuntimeError('build failed '+role)
    save(STUDY/'BUILD_IDENTITY.json',{'upstream_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','compiler_sha256':hashlib.file_digest(zig.open('rb'),'sha256').hexdigest(),'compiler_version':subprocess.check_output([str(zig),'version'],text=True).strip(),'frontends':{role:hashlib.file_digest((out/(role+'.exe')).open('rb'),'sha256').hexdigest() for role in ['P','R']},'worker_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'commands':attempt,'runtime_dlls':'original released b10839 distribution, loaded by exact external path; no core/backend rebuild','patch':'new additive frontends only','eligibility':'NOT_YET_QUALIFIED'})
    print('Built separated P/R frontends')
if __name__=='__main__':main()
