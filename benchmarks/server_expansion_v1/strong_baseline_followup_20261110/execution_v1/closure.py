"""CPU dependency closure: verify inherited proofs and every new -MD input."""
import argparse
from pathlib import Path
import shlex
import subprocess
from support import fresh,need,read,sha


def collect(root,work,out):
    files={};origins=[]
    for relative in ('run-01/build-R-01/DEPENDENCIES.json','run-01/build-loop4-01/DEPENDENCIES.json',
                     'q32-q4-full-build-04/loop4/DEPENDENCIES.json','q32-q4-full-build-10/loop4/DEPENDENCIES.json'):
        p=root/relative;need(p.is_file(),'Missing inherited compiled dependency receipt: '+relative)
        j=read(p);origins.append(dict(path=str(p),sha256=sha(p),translation_units=j.get('translation_units'),
                                     cuda_translation_units=j.get('cuda_translation_units')))
        for name,value in j['files'].items():
            digest=value if isinstance(value,str)else value['sha256']
            need(sha(name)==digest,'Inherited transitive byte mismatch: '+name)
            if name in files:need(files[name]==digest,'Conflicting dependency identities')
            files[name]=digest
    dependencies=list(work.rglob('*.d'));need(len(dependencies)>=7,'Missing new transitive dependency files')
    for p in dependencies:
        text=p.read_text().replace('\\\n',' ');target,separator,body=text.partition(':')
        need(separator and target,'Dependency format')
        for name in shlex.split(body):
            q=Path(name);need(q.is_absolute()and q.is_file(),'Unresolved compiler dependency: '+name)
            digest=sha(q)
            if name in files:need(files[name]==digest,'New/inherited dependency identity conflict')
            files[name]=digest
    binaries=[work/'backend/operand-worker',work/'gold/gold-worker',work/'model/model-worker',work/'parent-guard']
    module_promises={}
    for binary in binaries:
        need(binary.is_file(),'Missing executable')
        p=subprocess.run(['ldd',str(binary)],capture_output=True,text=True,timeout=30)
        need(p.returncode==0 and 'not found'not in p.stdout,'Unresolved ELF dependency')
        libraries=[]
        for line in p.stdout.splitlines():
            token=line.split('=>',1)[-1].strip().split()[0]
            if token.startswith('/'):
                q=Path(token).resolve();files[str(q)]=sha(q);libraries.append(str(q))
        module_promises[str(binary)]=dict(executable_sha256=sha(binary),ELF_needed_libraries=libraries,
             actual_after_GPU_initialization='MUST_BE_VERIFIED_BY_HOST_BEFORE_ACCEPTING_OUTPUT')
    for library in ('libcuda.so.1','libnvidia-ptxjitcompiler.so.1','libnvidia-fatbinaryloader.so.1'):
        p=Path('/usr/lib/x86_64-linux-gnu')/library
        if p.is_file():files[str(p.resolve())]=sha(p.resolve())
    crypto=Path('/usr/lib/x86_64-linux-gnu/libcrypto.so.3');need(crypto.is_file(),'Pinned runtime SHA library')
    files[str(crypto.resolve())]=sha(crypto.resolve())
    fresh(out,dict(schema='hs.strong.compiled-closure.v1',scope='CPU_BUILD_AND_PROMISED_RUNTIME_FILES_NOT_GPU_QUALIFICATION',
         inherited_receipts=origins,new_dependency_files=[dict(path=str(p),sha256=sha(p))for p in dependencies],
         files=dict(sorted(files.items())),module_promises=module_promises,
         new_translation_units=['mmvq.cu','ggml-cuda.cu','llama-graph.cpp','operand_worker.cpp','model_entry.cpp',
                                'work_counts.cpp','gold_worker.cpp','gold_quant.cu'],native_model_requests=0))


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--work',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();collect(a.root,a.work,a.out)


if __name__=='__main__':main()
