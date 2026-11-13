"""Bind actual new frontend compiler/link dependencies plus immutable parent closure."""
from pathlib import Path
import ctypes,json,re,os
from admission import HERE,ROOT,REPO,put,sha
from execute import WORK,BASE

def argv(text):
    n=ctypes.c_int();f=ctypes.windll.shell32.CommandLineToArgvW;f.argtypes=[ctypes.c_wchar_p,ctypes.POINTER(ctypes.c_int)];f.restype=ctypes.POINTER(ctypes.c_wchar_p)
    p=f(text,ctypes.byref(n));assert p
    try:return [p[i] for i in range(n.value)]
    finally:ctypes.windll.kernel32.LocalFree(p)

def main():
    files={};builds={}
    def bind(p,role):
        p=Path(p).resolve();assert p.is_file() and p.suffix.lower() not in ('.key','.pem','.gguf')
        key=str(p);files[key]=dict(role=role,sha256=sha(p),bytes=p.stat().st_size);return key
    for core in ('loop4','packed'):
        run=WORK/(core+'-v2');raw=(run/'worker.d').read_text().replace('\\\n',' ');body=re.split(r':\s+',raw,maxsplit=1)[1]
        deps=[Path(x.replace('\\ ',' ').replace('\\#','#')).resolve() for x in re.findall(r'(?:\\[ \t#]|[^\s])+',body)]
        assert (WORK/'frontend-v2/entry.cpp').resolve() in deps
        for p in deps:bind(p,'actual_frontend_dependency')
        for p in (run/'worker.d',run/'worker.json',run/'link.json',run/'link.log',run/'BUILD.json'):bind(p,'actual_build_report')
        bind(run/'worker.obj','new_object');bind(run/'bin/worker.exe','new_executable')
        command=json.loads((run/'worker.json').read_bytes());bind(command['argv'][0],'compiler_toolchain')
        link=json.loads((run/'link.json').read_bytes());inputs=[]
        for x in link['argv']:
            p=Path(x)
            if p.is_file() and p.suffix in ('.obj','.lib','.a'):inputs.append(bind(p,'static_link_input'))
        verbose=(run/'link.log').read_text();lines=[x for x in verbose.splitlines() if x.startswith('lld-link ')];assert len(lines)==1
        for x in argv(lines[0])[1:]:
            p=Path(x)
            if p.is_file() and p.suffix in ('.obj','.lib','.a'):inputs.append(bind(p,'integrated_link_input'))
        builds[core]=dict(executable_sha256=sha(run/'bin/worker.exe'),new_translation_units=1,dependencies=len(deps),static_link_inputs=inputs,
            compiler_argv=command['argv'],linker_argv=link['argv'],integrated_lld_argv=argv(lines[0]),working_directory_from_host_invocation=str(REPO),
            parent_complete_closure=dict(path=str(BASE/'freezes'/core/'BUILD_FREEZE.json'),sha256=sha(BASE/'freezes'/core/'BUILD_FREEZE.json'),files=4986),
            parent_closure_audit_sha256=sha(ROOT/'WINDOWS_CLOSURE_AUDIT.json'))
    for p in (WORK/'frontend-v2').iterdir():
        if p.is_file():bind(p,'complete_generated_frontend')
    environment_keys=['CUDA_VISIBLE_DEVICES','CUDA_DEVICE_ORDER','CUBLAS_WORKSPACE_CONFIG','CUDA_MODULE_LOADING','OMP_NUM_THREADS','MKL_NUM_THREADS']
    put(ROOT/'SOURCE_BINDINGS.json',dict(schema='rtx211.windows-source-closure.v1',builds=builds,files=files,
        numerical_core='Unchanged original Windows201-unit source-built archives with4986 inputs/core; both parent closures verified before any new GPU work.',
        original_R=dict(build_sha256=sha(BASE/'R-Qwen/BUILD.json'),executable_sha256=sha(BASE/'R-Qwen/bin/worker.exe'),modified=False),
        current_relevant_runtime_environment={k:os.environ.get(k) for k in environment_keys},runtime_environment_scope='Current before clean timing; actual per-worker numerical modules and native capabilities are bound separately.',
        source_epochs_retained=['frontend-v1 (geometry only)','frontend-v2 (full qualification and prospective clean epoch)']))
    print('Bound new compiler dependencies',len(files),'files; original numerical archives unchanged',flush=True)

if __name__=='__main__':main()
