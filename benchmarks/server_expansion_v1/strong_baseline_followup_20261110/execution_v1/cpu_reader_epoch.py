"""CPU-only source epoch for a reader correction; exact native ELFs retained."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from host import verify_files
from support import fresh,need,read,sha,write


def main(root,work,previous_configuration):
    need(not work.exists(),'Fresh CPU reader epoch');work.mkdir();start=time.monotonic();steps=[]
    c=read(previous_configuration);old_cpu=Path(c['compiled_closure']).parent;here=Path(__file__).parent
    need(read(old_cpu/'STATE.json')['status']=='CPU_IMPLEMENTATIONS_BUILT_F0_S1_NOT_ADMITTED','Prior native CPU build was not complete')
    old_source=Path(next(p for p in c['source_files']if p.endswith('/build_model.py'))).parent
    native_sources=[p for p in old_source.rglob('*')if p.is_file()and
                    (p.suffix in ('.cpp','.hpp','.h','.cu','.c')or p.name in ('build_model.py','build_backend.py','build_gold.py','objects.py'))]
    identities=[]
    for p in native_sources:
        relative=p.relative_to(old_source);need(sha(p)==sha(here/relative),'Reader epoch cannot change native source/build inputs')
        identities.append(dict(path=str(relative),sha256=sha(p)))
    need(sha(c['compiled_closure'])==c['compiled_closure_sha256'],'Original compiled closure changed')
    verify_files(read(c['compiled_closure'])['files'])
    for role,value in c['executables'].items():need(sha(value['path'])==value['sha256'],'Original executable changed')
    for folder in ('backend','gold','model'):
        shutil.copytree(old_cpu/folder,work/folder,copy_function=os.link)
    for name in ('parent-guard','PARENT_GUARD_ZERO_GPU_PROOF.json','CPU_ECHO.json','HISTORICAL_READER_FIXTURE.json',
                 'COMPILED_CLOSURE.private.json'):
        os.link(old_cpu/name,work/name)
    fresh(work/'COMPILED_ARTIFACT_REUSE.private.json',dict(status='EXACT_NATIVE_BYTES_REUSED',
         previous_configuration=str(previous_configuration),previous_configuration_sha256=sha(previous_configuration),
         executables=c['executables'],unchanged_native_source_inputs=identities,
         scope='Pure Python reader/accounting/archive epoch; no recompile or numerical/ABI/clock change'))
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='');env.pop('HS_STRONG_GPU_ADMISSION_FILE',None)
    def step(label,args,cwd=None):
        t=time.monotonic()
        with (work/(label+'.stdout.log')).open('xb')as so,(work/(label+'.stderr.log')).open('xb')as se:
            result=subprocess.run(args,stdout=so,stderr=se,env=env,cwd=cwd,timeout=1800)
        steps.append(dict(step=label,returncode=result.returncode,caller_s=time.monotonic()-t,
                          stdout_sha256=sha(work/(label+'.stdout.log')),stderr_sha256=sha(work/(label+'.stderr.log'))))
        need(result.returncode==0,'CPU reader-epoch step failed: '+label)
    status='CPU_PIPELINE_FAILED'
    try:
        step('python-syntax',[sys.executable,'-B','-c','import ast,pathlib;[(ast.parse(p.read_text(),filename=str(p)))for p in pathlib.Path('+repr(str(here.parent))+').rglob("*.py")]'])
        step('prospective-manifest',[sys.executable,'-B',str(here/'prepare.py'),'--root',str(root),'--out',str(work/'prospective'),
             '--resume-configuration',str(previous_configuration)])
        for label,flags in [('normal',[]),('optimized',['-O'])]:
            step('design-'+label,[sys.executable,*flags,'-B','-m','unittest','-v','test_design_checks.py'],here.parent)
            step('execution-'+label,[sys.executable,*flags,'-B',str(here/'test_execution.py')])
        # Source-level distinction, tied to the exact compiled dependency bytes.
        entry=(old_cpu/'model/frontend/entry.cpp').read_text()
        common=(old_cpu/'backend/source/ggml/src/ggml-cuda/common.cuh').read_text()
        context=(old_cpu/'model/source/src/llama-context.cpp').read_text()
        need(entry.index('setenv("GGML_CUDA_DISABLE_GRAPHS","1",1)')<entry.index('llama_backend_init()'),
             'Actual CUDA graph switch must precede backend/model/context initialization')
        need('disable_cuda_graphs_due_to_env = (getenv("GGML_CUDA_DISABLE_GRAPHS") != nullptr)'in common and
             'return !(disable_due_to_gpu_arch || disable_cuda_graphs_due_to_env);'in common,'Compiled CUDA graph disable mechanism')
        need('hsc::reused(this);'in context and 'n_reused++;'in context,'hsc host graph reuse provenance')
        fresh(work/'GRAPH_POLICY_READER_CORRECTION.json',dict(status='SOURCE_MECHANISM_VERIFIED_SAME_NATIVE_BYTES',
             host_graph_counter='hsc::reused in llama-context is host graph cache reuse, not cudaGraphLaunch',
             cuda_policy='GGML_CUDA_DISABLE_GRAPHS=1 set before backend init; compiled common.cuh is_enabled returns false',
             source_files={str(p):sha(p)for p in [old_cpu/'model/frontend/entry.cpp',old_cpu/'backend/source/ggml/src/ggml-cuda/common.cuh',old_cpu/'model/source/src/llama-context.cpp']},
             original_native_ELFs_unchanged=True))
        # Fresh no-GPU configuration echoes from the actual retained binaries.
        echoes=[]
        for role,folder in [('operand','backend'),('model','model')]:
            for arm in 'GBC':
                job=old_cpu/(folder+'-'+arm+'.json');p=c['executables'][role]['path']
                result=subprocess.run([p,'--echo',str(job)],capture_output=True,text=True,env=env,timeout=30)
                need(result.returncode==0,'Actual reused native CPU echo');echoes.append(dict(role=role,arm=arm,stdout=result.stdout,stderr=result.stderr))
        fresh(work/'FRESH_REUSED_NATIVE_ECHO.json',dict(records=echoes,native_model_requests=0))
        status='CPU_IMPLEMENTATIONS_BUILT_F0_S1_NOT_ADMITTED'
    finally:
        write(work/'STATE.json',dict(status=status,steps=steps,caller_s=time.monotonic()-start,
              native_model_requests=0,GPU_admitted=False,auto_GPU_transition=False,
              exact_native_artifact_reuse=True,post_hoc_reader_correction=True))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('root','work','previous-configuration'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();main(a.root,a.work,a.previous_configuration)
