"""Build reference, loop4 or packed INCLUDING numerical modules on Linux.

CPU-only is a build diagnostic, never the GPU oracle. No model execution.
"""
from __future__ import annotations
import argparse, json, os, re, shutil, subprocess
from pathlib import Path
from common import need, read, save, sha, inventory, verify_tree, command
HERE=Path(__file__).resolve().parent

def compile_inputs(build):
    units=read(build/'compile_commands.json'); names=set(); unresolved=[]; header_count=0
    for u in units:
        p=Path(u['file']);p=p if p.is_absolute() else Path(u['directory'])/p;names.add(p.resolve())
    # Ninja's compiler-generated dep database includes transitive system/generated headers.
    raw=subprocess.check_output(['ninja','-C',str(build),'-t','deps'],text=True)
    (build/'NINJA_DEPS.txt').write_text(raw)
    for line in raw.splitlines():
        if line.startswith('    '):
            p=Path(line.strip());p=p if p.is_absolute() else build/p
            if p.is_file():names.add(p.resolve());header_count+=1
            else:unresolved.append(str(p))
    need(header_count>0, 'Missing compiler-produced transitive dependency closure')
    linkmap=build/'transfer-worker.map';need(linkmap.is_file(),'Missing actual link map')
    for line in linkmap.read_text(errors='replace').splitlines():
        if line.startswith('LOAD '):
            p=Path(line[5:].strip());p=p if p.is_absolute() else build/p
            if p.is_file():names.add(p.resolve())
    commands=subprocess.check_output(['ninja','-C',str(build),'-t','commands','transfer-worker'],text=True)
    (build/'ACTUAL_COMMANDS.txt').write_text(commands)
    names.add(linkmap.resolve());names.add((build/'ACTUAL_COMMANDS.txt').resolve())
    for p in build.rglob('*'):
        if p.is_file() and (p.suffix in ('.rsp','.cmake','.json','.ninja','.h','.hpp','.cuh','.o','.a') or p.name=='CMakeCache.txt'):
            names.add(p.resolve())
    return {'translation_units':len(units),'cuda_translation_units':sum(str(u['file']).endswith('.cu') for u in units),'files':{str(p):sha(p) for p in sorted(names)},
            'unresolved_compiler_dependencies':sorted(set(unresolved)),
            'dependency_report_sha256':sha(build/'NINJA_DEPS.txt')}

def build(staged,out,role,arch,cpu=False,jobs=2):
    need(os.name=='posix','Linux host required');need(1<=jobs<=4,'Use at most four build jobs on shared host')
    staged=Path(staged).resolve();out=Path(out).resolve();lock=read(staged/'SOURCE_LOCK.json')
    need(lock['status']=='SOURCE_PORTED_NOT_BUILT','Resolve platform port in a new version first')
    verify_tree(staged/'sources'/role,lock['sources'][role]);verify_tree(staged/'frontend',lock['frontend'])
    need(not out.exists() and not out.is_relative_to(staged),'Independent fresh build directory required')
    need(cpu or re.fullmatch(r'[0-9]+',str(arch)), 'Explicit observed CUDA architecture required')
    need(shutil.which('cmake') and shutil.which('ninja'),'cmake and ninja required; use approved user-space tools')
    need(cpu or shutil.which('nvcc'),'nvcc toolkit absent; nvidia-smi driver version is not a compiler')
    out.mkdir(parents=True);need(shutil.disk_usage(out).free>=20*1024**3,'Keep at least20GiB free for build')
    env=dict(os.environ)
    for k in list(env):
        if k.startswith(('GGML_','HS_','HSC_','JSA_')) or k in ('LD_PRELOAD',):env.pop(k)
    options=['cmake','-S',str(HERE),'-B',str(out/'native'),'-G','Ninja',
             '-DCMAKE_BUILD_TYPE=Release','-DROLE='+role,'-DLLAMA_SRC='+str(staged/'sources'/role),
             '-DFRONTEND_SRC='+str(staged/'frontend'),'-DTRANSFER_CUDA='+('OFF' if cpu else 'ON')]
    if not cpu:options+=['-DCMAKE_CUDA_ARCHITECTURES='+str(arch),'-DCMAKE_CUDA_COMPILER='+shutil.which('nvcc')]
    command(options,out/'configure',env=env)
    command(['cmake','--build',out/'native','--target','transfer-worker','-j',str(jobs),'--','-d','keeprsp','-d','keepdepfile','-v'],out/'compile',env=env,timeout=7200)
    exe=out/'native/bin/transfer-worker';need(exe.read_bytes()[:4]==b'\x7fELF','Not a native ELF binary')
    closure=compile_inputs(out/'native');need(cpu or closure['cuda_translation_units']>0,'No actual CUDA translation units were compiled');save(out/'DEPENDENCIES.json',closure)
    tools={}
    for name in ('cmake','ninja','c++','cc','nvcc'):
        p=shutil.which(name)
        if p:tools[name]={'path':str(Path(p).resolve()),'sha256':sha(p),'version':subprocess.check_output([p,'--version'],text=True,stderr=subprocess.STDOUT).splitlines()[:5]}
    save(out/'BUILD.json',{'role':role,'source_lock_sha256':sha(staged/'SOURCE_LOCK.json'),
        'reference_source_is_pristine':role=='reference','cuda':not cpu,'architecture':arch if not cpu else None,
        'executable':str(exe),'executable_sha256':sha(exe),'all_numerical_modules_built_from_source':True,
        'tools':tools,'build_environment':{k:os.environ.get(k) for k in ('CC','CXX','CUDAHOSTCXX','CUDA_HOME','PATH','LD_LIBRARY_PATH','CXXFLAGS','CFLAGS','LDFLAGS')},'wrapper_sources':{k:v for k,v in inventory(HERE).items() if '__pycache__' not in k and not k.endswith('.pyc')},'dependency_closure_sha256':sha(out/'DEPENDENCIES.json'),
        'dependency_closure_complete':not closure['unresolved_compiler_dependencies'],
        'status':'BUILT_NOT_QUALIFIED','actual_loaded_modules':'NOT_OBSERVED_UNTIL_NATIVE_RUN',
        'GPU_qualification':'NOT_RUN','cpu_build_is_not_GPU_reference':cpu})
    print(exe)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--staged',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--role',choices=['reference','loop4','packed'],required=True);p.add_argument('--arch');p.add_argument('--cpu-only',action='store_true');p.add_argument('--jobs',type=int,default=2)
    a=p.parse_args();build(a.staged,a.out,a.role,a.arch,a.cpu_only,a.jobs)
