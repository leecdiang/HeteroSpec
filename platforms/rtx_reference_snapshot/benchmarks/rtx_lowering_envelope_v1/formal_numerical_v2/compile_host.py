"""Offline compile through bounded CPU job; never executes GPU modes."""
import json,subprocess,sys
from common import V,load,save,sha
def main():
    command=load(V.parent/'repair_timer_v1/RELEASE_IDENTITY.json')['exact_link_command']
    args=[str(V/'native_formal.cpp') if x.endswith('/native_repair.cpp') else str(V/'lowering113_formal.exe') if x.endswith('/lowering113_repair.exe') else str(V/Path(x).name) if x.endswith(('/libggml.dll.a','/libggml-base.dll.a')) else x for x in command]
    result=subprocess.run([sys.executable,'-B',str(V/'cpu_job.py'),'--label','compile_shared_formal','--parallel-bound','8',*args],capture_output=True)
    save(V/'COMPILE.json',dict(command=args,exit_code=result.returncode,stdout=result.stdout.decode(errors='replace'),stderr=result.stderr.decode(errors='replace'),numerical_DLL_rebuilds=0,GPU_queries=0))
    assert result.returncode==0
    from pe_review import PE
    imports=PE(V/'lowering113_formal.exe').imports()
    assert 'ggml_init' in imports['ggml-base.dll'] and 'ggml_backend_load' in imports['ggml.dll']
    assert not any('ggml-base.a' in x or x.endswith('/ggml.a') for x in args)
    save(V/'LINK_IDENTITY.json',dict(executable_sha256=sha(V/'lowering113_formal.exe'),link_command=args,PE_imports=imports,route='A unchanged original shared core/registry',GPU_loads=0))
    print('PASS offline compile/import identity; no native GPU execution')
from pathlib import Path
if __name__=='__main__':main()
