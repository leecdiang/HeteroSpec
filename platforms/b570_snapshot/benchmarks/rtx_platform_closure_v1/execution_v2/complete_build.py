exec((__import__('pathlib').Path(__file__).resolve().parent/'build_rtx.py').read_text(encoding='utf-8').split("if __name__")[0])
import sys
assert (BUILD/'bin/rtx-closure.exe').exists()
dlls=[]
for p in Path('D:/hs-qb-confirmation-v02/native/build/bin').glob('*.dll'):
    dest=BUILD/'bin'/p.name
    if not dest.exists():shutil.copyfile(p,dest)
    assert pin(p)['sha256']==pin(dest)['sha256'];dlls.append(pin(dest))
result=dict(status='BUILT_NO_MODEL_EXECUTION',executable=pin(BUILD/'bin/rtx-closure.exe'),DLLs=dlls,
    original_llama_archive=pin(OLD/'src/libllama.a'),new_llama_archive=pin(BUILD/'libllama.a'),compiler=pin(ZIG),
    original_source_files=[pin(SOURCE/'src'/n) for n in ('llama-graph.cpp','llama-context.cpp','hs_scope.h')],
    sources=[pin(p) for p in (BUILD/'source').iterdir()]+[pin(CODE/'worker.cpp')],
    preparation_processes=5,preparation_process_wall_seconds=None,
    preparation_logs=[pin(p) for p in BUILD.glob('*.log')],
    preparation_issue='Compilation/link completed. Cross-volume hardlink staging failed; copied unchanged DLL bytes instead. Compiler wall receipts were not persisted before staging error; no model process had started.',
    change='Two original C++ compilation units unchanged; dynamic layout selector header replaces cached environment selector. Numerical CUDA DLLs unchanged. Same executable and DLLs across arms.')
(CODE/'BUILD_MANIFEST.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
for p in (BASE/'build_rtx.py',Path(__file__)):
    shutil.copyfile(p,CODE/p.name)
print(json.dumps(result['executable']))
