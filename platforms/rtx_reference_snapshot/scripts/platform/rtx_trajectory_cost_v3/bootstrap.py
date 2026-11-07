"""Pinned source extraction and complete published scientific branch inventory.

Preparation only. No model context, sampler or decode is constructed.
"""
import json,subprocess,tarfile
from pathlib import Path
from prepare import ROOT,STUDY,sha,save,now

TAR_SHA256='5892a57221b9e7b6451ff368c085f95bd61697f879792b2da63d0f835b0eef31'

def prepare_dependencies(source_tar):
    source=ROOT/'work/pinned-source';source.mkdir(parents=True,exist_ok=True)
    if not (source/'include/llama.h').is_file():
        if source_tar is None:raise RuntimeError('--source-tar is required for pinned headers and timer build')
        source_tar=Path(source_tar).resolve()
        if sha(source_tar)!=TAR_SHA256:raise RuntimeError('PINNED_SOURCE_ARCHIVE_CHANGED')
        with tarfile.open(source_tar) as tar:tar.extractall(source,filter='data')
        if not (source/'include/llama.h').exists():raise RuntimeError('pinned source archive layout differs')
    rows=[]
    output=subprocess.check_output(['git','ls-remote','--heads','origin'],cwd=ROOT,text=True)
    baseline='abff99356815371648dc38f1466e66701e96840e'
    for line in output.splitlines():
        h,name=line.split()
        if name.endswith('experiment/rtx-trajectory-and-matched-cost-v3'):continue
        if not any(x in name.lower() for x in ['358h','b570','m4','rtx','latency','heterospec','main']):continue
        exists=subprocess.run(['git','cat-file','-e',h+'^{commit}'],cwd=ROOT,capture_output=True).returncode==0
        if not exists:subprocess.run(['git','fetch','--no-tags','--filter=blob:none','origin',h],cwd=ROOT,check=True)
        ancestor=subprocess.run(['git','merge-base','--is-ancestor',h,baseline],cwd=ROOT).returncode==0
        rows.append({'name':name,'sha':h,'local_object':True,'ancestor_of_main':ancestor})
    save(ROOT/'work/BRANCH_SCOPE.json',rows)
    out=ROOT/'work/h2-bin';out.mkdir(exist_ok=True);q=out/'Q.exe';worker=Path(__file__).with_name('query_defaults.cpp')
    zig='D:/HeteroSpec-PC/.venv-analysis/Lib/site-packages/ziglang/zig.exe'
    cmd=[zig,'c++','-std=c++17','-O2','-target','x86_64-windows-gnu','-I'+str(source/'include'),'-I'+str(source/'ggml/include'),'-I'+str(source/'vendor/nlohmann'),str(worker),'-o',str(q)]
    if not q.exists():
        with (ROOT/'work/QUERY_BUILD.log').open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
        if r.returncode:raise RuntimeError('scalar API query build failed')
    query=[str(q),'D:/HeteroSpec-PC/tools/llama-b10839'];r=subprocess.run(query,capture_output=True,check=True)
    (ROOT/'work/RUNTIME_DEFAULTS.stdout.log').write_bytes(r.stdout);(ROOT/'work/RUNTIME_DEFAULTS.stderr.log').write_bytes(r.stderr)
    defaults=json.loads(r.stdout);save(ROOT/'work/RUNTIME_DEFAULTS.json',defaults)
    save(STUDY/'DEPENDENCY_PREPARATION.json',{'utc':now(),'source_tar_sha256':TAR_SHA256,'query_command':query,'query_build_command':cmd,'query_source_sha256':sha(worker),'query_exe_sha256':sha(q),'context_creations':0,'model_forward_calls':0,'scope':'API scalar defaults only; no weights/context/decode'})
