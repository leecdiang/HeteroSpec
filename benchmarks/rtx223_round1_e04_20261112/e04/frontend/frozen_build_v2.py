"""Pre-scan, materialize and OS-freeze frontend code-generation/link inputs.

No DLL loading, backend/model call or GPU execution is performed.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shutil,subprocess,time
from input_freeze import ReadFreeze,FreezeRefusal,need,sha,snapshot,verify,verify_manifest_identity
import input_freeze as active_freeze_module
import dep_witness_v2 as active_dependency_module
from dep_witness_v2 import parse_dependency,resolved_cpu

ROOT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e04').resolve();HERE=ROOT/'e04/frontend'
PARENT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e03')
PARENT_SOURCE=PARENT/'e03/frontend/source-v4'
OLD=Path('D:/rtx211-q8-20261109')
ORIGINAL_TOOL=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx221-round1-20261112/request/compiler_copy')
EXTERNAL_ROOTS=[Path('D:/rtx192-review-v2'),Path('E:/rtx170/profiler/sdk')]

def put(path,value):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2)
def parse_dependencies(path,target,source):return parse_dependency(path,target,source)
def cpu_features(text):
    return resolved_cpu(text)
def replace_prefix(text,old,new):
    return text.replace(str(old),str(new)).replace(old.as_posix(),new.as_posix())
def options(tool):
    flags=['-target','x86_64-windows-gnu','-stdlib=libc++','-nostdinc','-nostdinc++','-march=native','-Werror=date-time','-resource-dir',str(tool/'lib')]
    for p in [tool/'lib/libcxx/include',tool/'lib/libcxxabi/include',tool/'lib/include',tool/'lib/libc/include/any-windows-any',tool/'lib/libunwind/include']:
        flags+=['-isystem',str(p)]
    defs=['NDEBUG','__MSVCRT_VERSION__=0xE00','_WIN32_WINNT=0x0a00','_LIBCPP_ABI_VERSION=1','_LIBCPP_ABI_NAMESPACE=__1','_LIBCPP_HAS_THREADS=1','_LIBCPP_HAS_MONOTONIC_CLOCK=1','_LIBCPP_HAS_TERMINAL=1','_LIBCPP_HAS_MUSL_LIBC=0','_LIBCXXABI_DISABLE_VISIBILITY_ANNOTATIONS','_LIBCPP_DISABLE_VISIBILITY_ANNOTATIONS','_LIBCPP_HAS_VENDOR_AVAILABILITY_ANNOTATIONS=0','_LIBCPP_HAS_FILESYSTEM=1','_LIBCPP_HAS_RANDOM_DEVICE=1','_LIBCPP_HAS_LOCALIZATION=1','_LIBCPP_HAS_UNICODE=1','_LIBCPP_HAS_WIDE_CHARACTERS=1','_LIBCPP_HAS_NO_STD_MODULES=1','_LIBCPP_PSTL_BACKEND_SERIAL','_LIBCPP_HARDENING_MODE=_LIBCPP_HARDENING_MODE_NONE']
    return flags+['-D'+d for d in defs]
def base_compile(core,source,tool):
    raw=json.loads((OLD/(core+'-v2')/'worker.json').read_bytes())['argv'][2:]
    result=[];i=0
    while i<len(raw):
        arg=raw[i]
        if arg in ('-MF','-o'):i+=2;continue
        if arg in ('-MD','-c'):i+=1;continue
        if arg.lower().endswith('entry.cpp'):i+=1;continue
        result.append(replace_prefix(arg,OLD/'frontend-v2',source));i+=1
    return [str(tool/'zig.exe'),'clang',*options(tool),*result]
def staged_path(path,workspace):
    p=Path(path).resolve()
    for n,base in enumerate(EXTERNAL_ROOTS):
        if p.is_relative_to(base):return workspace/'headers'/str(n)/p.relative_to(base)
    raise FreezeRefusal('unexpected external codegen dependency: '+str(p))
def stage_arg(arg,workspace):
    for n,base in enumerate(EXTERNAL_ROOTS):arg=replace_prefix(arg,base,workspace/'headers'/str(n))
    return arg
def run_record(label,args,cwd,env,out,input_data=None):
    begin=time.monotonic();p=subprocess.run(args,cwd=cwd,env=env,input=input_data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=300)
    (out/(label+'.stdout.log')).write_bytes(p.stdout);(out/(label+'.stderr.log')).write_bytes(p.stderr)
    record={'label':label,'argv':args,'cwd':str(cwd),'returncode':p.returncode,'wall_seconds':time.monotonic()-begin,'stdout_sha256':sha(out/(label+'.stdout.log')),'stderr_sha256':sha(out/(label+'.stderr.log'))}
    put(out/(label+'.json'),record);need(p.returncode==0,label+' failed; retained output logs');return record

def prepare(version='v2',reuse_toolchain=None):
    run=HERE/('run-'+version);run.mkdir(exist_ok=False)
    source=run/'source';shutil.copytree(PARENT_SOURCE,source)
    expected=json.loads((PARENT/'e03/frontend/SOURCE_v4.json').read_bytes())['files']
    need(all(sha(source/n)==h for n,h in expected.items()),'parent source changed before copying')
    binding=source/'e03_binding.hpp';text=binding.read_text(encoding='utf8');need(text.count('rtx223-round1-20261112-e03')==1,'epoch anchor changed');binding.write_text(text.replace('rtx223-round1-20261112-e03','rtx223-round1-20261112-e04'),encoding='utf8',newline='\n')
    if reuse_toolchain:
        tool=Path(reuse_toolchain).resolve();need(tool.is_relative_to(HERE),'reuse only own e04 staged toolchain')
        prior=tool.parent/'TOOLCHAIN_COPY_IDENTITY.json';old=json.loads(prior.read_bytes());tool_before=old['files']
        need(all(sha(tool/p)==h for p,h in tool_before.items()),'owned staged toolchain differs from its preparation identity')
        need({str(p.relative_to(tool)) for p in tool.rglob('*') if p.is_file()}==set(tool_before),'owned staged toolchain membership changed')
        put(run/'TOOLCHAIN_COPY_IDENTITY.json',{'origin':old['origin'],'copy':str(tool),'files':tool_before,'bytes':old['bytes'],'reused_preparation_identity':str(prior),'reused_preparation_sha256':sha(prior),'scope':'fresh v2 complete owned-copy hash/membership check; v1 provisional scans are not reused'})
    else:
        tool=run/'toolchain';tool.mkdir()
        origin_tool_inputs=[ORIGINAL_TOOL/'zig.exe',*[p for p in (ORIGINAL_TOOL/'lib').rglob('*') if p.is_file()]]
        tool_before={str(p.relative_to(ORIGINAL_TOOL)):sha(p) for p in origin_tool_inputs}
        shutil.copy2(ORIGINAL_TOOL/'zig.exe',tool/'zig.exe');shutil.copytree(ORIGINAL_TOOL/'lib',tool/'lib')
        need(all(sha(ORIGINAL_TOOL/p)==h and sha(tool/p)==h for p,h in tool_before.items()),'Zig/resource source or copy changed while staging')
        put(run/'TOOLCHAIN_COPY_IDENTITY.json',{'origin':str(ORIGINAL_TOOL),'copy':str(tool),'files':tool_before,'bytes':sum((tool/p).stat().st_size for p in tool_before),'scope':'source prehash matches source postcopy and isolated staged bytes; no old files locked or written'})
    deps=run/'deps';deps.mkdir();build=run/'build';build.mkdir()
    temp=run/'temp';temp.mkdir();env={k:os.environ[k] for k in ('SystemRoot','WINDIR','SystemDrive','ComSpec') if k in os.environ}
    env.update(PATH=str(tool)+os.pathsep+str(Path(os.environ['SystemRoot'])/'System32'),TEMP=str(temp),TMP=str(temp),ZIG_LIB_DIR=str(tool/'lib'),ZIG_GLOBAL_CACHE_DIR=str(run/'global-cache'),ZIG_LOCAL_CACHE_DIR=str(run/'local-cache'),INCLUDE='',LIB='',CL='')
    put(run/'ENVIRONMENT.json',env)
    parent_inputs=json.loads((PARENT/'e03/frontend/build-v4/BUILD.json').read_bytes())['linked_input_identities_before_and_after']
    materialized={};core_info={};archive_paths=[]
    for core in ('loop4','packed'):
        folder=build/core;folder.mkdir();(folder/'bin').mkdir()
        original=base_compile(core,source,tool)
        first=run/(core+'-initial.d');run_record(core+'-initial-scan',[*original,'-M','-MF',str(first),'-MT',str(folder/'worker.obj'),str(source/'entry.cpp')],run,env,run)
        for p in parse_dependencies(first,folder/'worker.obj',source/'entry.cpp'):
            path=Path(p)
            if path.is_relative_to(run):continue
            target=staged_path(path,deps);target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():shutil.copy2(path,target)
            need(sha(path)==sha(target),'dependency copy differs')
            materialized[str(path)]={'staged':str(target),'sha256':sha(target)}
        flags=[stage_arg(a,deps) for a in original]
        for n,base in enumerate(EXTERNAL_ROOTS):
            # All search roots are private copies; unused directories remain empty.
            for arg in flags:
                if arg.startswith('-I') and str(deps/'headers'/str(n)) in arg:Path(arg[2:]).mkdir(parents=True,exist_ok=True)
        final=run/(core+'-prescan.d');run_record(core+'-prescan',[*flags,'-M','-MF',str(final),'-MT',str(folder/'worker.obj'),str(source/'entry.cpp')],run,env,run)
        observed=parse_dependencies(final,folder/'worker.obj',source/'entry.cpp');need(all(Path(p).is_relative_to(HERE) for p in observed),'final scan escaped owned isolated frontend workspace')
        run_record(core+'-predefines',[*flags,'-dM','-E','-x','c++','-'],run,env,run,b'')
        run_record(core+'-effective',[*flags,'-###','-c',str(source/'entry.cpp'),'-o',str(folder/'worker.obj')],run,env,run)
        compile_args=[*flags,'-v','-MD','-MF',str(folder/'worker.d'),'-c',str(source/'entry.cpp'),'-o',str(folder/'worker.obj')]
        oldrun=OLD/(core+'-v2');line=(oldrun/'link.log').read_text(encoding='utf8').strip();need(line.startswith('lld-link ') and '\n' not in line,'linker trace must be exactly one command')
        link=[str(tool/'zig.exe'),'lld-link'];archives=[]
        for arg in line.split()[1:]:
            arg=replace_prefix(arg,oldrun,folder)
            p=Path(arg)
            if p.is_absolute() and p.is_file() and not p.is_relative_to(run):
                if str(p) in parent_inputs:need(sha(p)==parent_inputs[str(p)],'parent link input changed: '+str(p))
                unique=hashlib.sha256(str(p).casefold().encode()).hexdigest()[:16];target=deps/'link'/unique/p.name;target.parent.mkdir(parents=True,exist_ok=True)
                if not target.exists():shutil.copy2(p,target)
                need(sha(p)==sha(target),'link input copy differs')
                materialized[str(p)]={'staged':str(target),'sha256':sha(target)};arg=str(target)
                if p.suffix.lower() in ('.lib','.a'):archives.append(str(target));archive_paths.append(str(target))
            link.append(arg)
        link+=['/verbose','/map:'+str(folder/'worker.map')]
        core_info[core]={'compile':compile_args,'link':link,'prescan_dependencies':observed,'effective_CPU':cpu_features((run/(core+'-effective.stderr.log')).read_text(encoding='utf8')),'archives':archives,'object':str(folder/'worker.obj'),'exe':str(folder/'bin/worker.exe')}
    put(run/'MATERIALIZED_INPUTS.json',materialized)
    workflow_files=[Path(__file__),HERE/'input_freeze.py',HERE/'dep_witness_v2.py',HERE/'link_witness.py']
    need(all(p.is_file() for p in workflow_files),'link witness helper not frozen yet')
    workflow=run/'workflow';workflow.mkdir()
    for p in workflow_files:shutil.copy2(p,workflow/p.name)
    recipe={'schema':'heterospec.e04.frontend-frozen-recipe.v1','run':str(run),'source':str(source),'toolchain':str(tool),'dependencies':str(deps),'environment':env,'cores':core_info,'workflow_files':{str(p):sha(p) for p in workflow.iterdir()},'OS_runtime_scope':'Windows/system DLLs are not frozen; isolated compiler/resources/headers/archives are frozen','native_release':'BLOCKED','numeric_DLL_binding':'external post-build manifest; no compiled DLL hash literal'}
    put(run/'RECIPE.json',recipe)
    membership={str(p.resolve()):sha(p) for base in (tool,source,deps,workflow) for p in base.rglob('*') if p.is_file()}
    extra=[run/'RECIPE.json',run/'ENVIRONMENT.json',run/'MATERIALIZED_INPUTS.json',run/'TOOLCHAIN_COPY_IDENTITY.json',run/'loop4-prescan.d',run/'packed-prescan.d',run/'loop4-effective.stderr.log',run/'packed-effective.stderr.log',run/'loop4-predefines.stdout.log',run/'packed-predefines.stdout.log']
    prepared={'schema':'heterospec.e04.frontend-prepared-inputs.v2','entries':snapshot([*map(Path,membership),*extra]),'tree_membership':membership,'recipe_sha256':sha(run/'RECIPE.json'),'codegen_started':False}
    put(run/'PREPARED_INPUTS.json',prepared)
    print(json.dumps({'prepared':str(run),'headers_materialized':len(materialized),'prepared_sha256':sha(run/'PREPARED_INPUTS.json'),'next':'invoke workflow/frozen_build_v2.py build --prepared-sha <this independent digest>','no_GPU':True}));return run

def freeze_build(run,expected_prepared_sha):
    run=Path(run).resolve();need(run.is_relative_to(HERE),'wrong run directory')
    need(Path(__file__).resolve()==run/'workflow/frozen_build_v2.py','execute the staged, frozen workflow copy for codegen/link')
    recipe=json.loads((run/'RECIPE.json').read_bytes());tool=Path(recipe['toolchain']);source=Path(recipe['source']);deps=Path(recipe['dependencies']);env=recipe['environment'];build=run/'build'
    prepared=verify_manifest_identity(run/'PREPARED_INPUTS.json',expected_prepared_sha)
    need(prepared['recipe_sha256']==sha(run/'RECIPE.json'),'prepared compile/link recipe changed')
    workflow=run/'workflow';need(sha(workflow/'frozen_build_v2.py')==sha(__file__),'build generator changed since staging')
    need(Path(active_freeze_module.__file__).resolve()==workflow/'input_freeze.py','active OS-freeze module is not the frozen workflow copy')
    need(Path(active_dependency_module.__file__).resolve()==workflow/'dep_witness_v2.py','active dependency parser is not the frozen workflow copy')
    need(all(sha(p)==h for p,h in recipe['workflow_files'].items()),'staged workflow source changed before freeze')
    members={str(p.resolve()):sha(p) for root in (tool,source,deps,workflow) for p in root.rglob('*') if p.is_file()}
    need(members==prepared['tree_membership'],'prepared membership/source/tool/header/library identity changed')
    all_paths=list(map(Path,members))+[run/'RECIPE.json',run/'ENVIRONMENT.json',run/'MATERIALIZED_INPUTS.json',run/'TOOLCHAIN_COPY_IDENTITY.json',run/'loop4-prescan.d',run/'packed-prescan.d',run/'loop4-effective.stderr.log',run/'packed-effective.stderr.log',run/'loop4-predefines.stdout.log',run/'packed-predefines.stdout.log']
    all_paths.append(run/'PREPARED_INPUTS.json')
    entries=snapshot(all_paths);freeze={'schema':'heterospec.e04.frontend-input-freeze.v2','entries':entries,'tree_membership':members,'recipe_sha256':sha(run/'RECIPE.json'),'prepared_inputs_sha256':expected_prepared_sha,'freeze_mechanism':'Win32 GENERIC_READ+FILE_SHARE_READ on isolated copies; write/delete denied while handles held','pre_codegen':True,'codegen_witness':'final -M prescan then actual -MD exact-set equality; LLD /verbose and map selected archive members','old_inputs_locked':False,'OS_DLLs_attested':False}
    put(run/'FREEZE.json',freeze)
    final=[];generated=[]
    with ReadFreeze(entries+[{'path':str(run/'FREEZE.json'),'sha256':sha(run/'FREEZE.json')}]) as held:
        for core,info in recipe['cores'].items():
            record=run_record(core+'-compile',info['compile'],run,env,run);actual=parse_dependencies(build/core/'worker.d',info['object'],source/'entry.cpp')
            need(actual==info['prescan_dependencies'],'actual codegen headers differ from frozen prescan: '+core)
            actual_CPU=cpu_features((run/(core+'-compile.stderr.log')).read_text(encoding='utf8'))
            need(actual_CPU==info['effective_CPU'],'native CPU/feature resolution changed: '+core)
            obj={'path':info['object'],'bytes':Path(info['object']).stat().st_size,'sha256':sha(info['object'])};held.add(obj);generated.append(obj)
            run_record(core+'-link',info['link'],run,env,run)
            trace=(run/(core+'-link.stdout.log')).read_text(encoding='utf8')+(run/(core+'-link.stderr.log')).read_text(encoding='utf8')
            import importlib.util
            spec=importlib.util.spec_from_file_location('locked_link_witness',workflow/'link_witness.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            map_text=(build/core/'worker.map').read_text(encoding='utf8');witness=module.analyze_link_inputs(trace,info['archives'],map_text=map_text);put(run/(core+'-LINK_WITNESS.json'),witness)
            final.append({'core':core,'exe':info['exe'],'exe_sha256':sha(info['exe']),'object':obj,'actual_dependency_file':str(build/core/'worker.d'),'actual_dependencies':actual,'actual_dependency_file_sha256':sha(build/core/'worker.d'),'actual_CPU':actual_CPU,'link_witness':core+'-LINK_WITNESS.json','codegen_and_link_passed':True})
            verify(entries);verify(generated)
        after={str(p.resolve()):sha(p) for root in (tool,source,deps,workflow) for p in root.rglob('*') if p.is_file()}
        need(after==members,'frozen input membership/hash changed during build')
        put(run/'POSTFREEZE.json',{'same_membership_and_hashes':True,'files_checked':len(entries),'generated_inputs':generated,'locks_held_through_codegen_link_and_verification':True,'OS_DLLs_attested':False})
    result={'schema':'heterospec.e04.frontend-bound-build.v1','status':'PASS_FROZEN_BUILD_NOT_NATIVE_QUALIFIED','freeze_sha256':sha(run/'FREEZE.json'),'recipe_sha256':sha(run/'RECIPE.json'),'postfreeze_sha256':sha(run/'POSTFREEZE.json'),'outputs':final,'model_requests':0,'GPU_launches':0,'CUDA_DLL_loads':0,'native_gate':'BLOCKED','loaded_numeric_identity':'NOT_RUN; post-build external DLL binding only'}
    put(run/'BUILD.json',result);print(json.dumps({'status':result['status'],'cores':[{k:x[k] for k in ('core','exe_sha256')} for x in final],'frozen_inputs':len(entries)}));return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','build']);p.add_argument('--version',default='v2');p.add_argument('--run');p.add_argument('--reuse-toolchain');p.add_argument('--prepared-sha');a=p.parse_args()
    if a.action=='prepare':prepare(a.version,a.reuse_toolchain)
    else:freeze_build(a.run,a.prepared_sha)
