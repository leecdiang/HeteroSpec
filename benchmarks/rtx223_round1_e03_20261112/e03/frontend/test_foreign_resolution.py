"""Own CPU-mock DLL collision test; never load an actual numerical DLL."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,shutil
from cpu_loader_test import load_cpu_standin,need,sha
HERE=Path(__file__).resolve().parent
def main():
    out=HERE/'foreign-resolution-test-v1';out.mkdir(exist_ok=False)
    original=HERE/'cpu-loader-test-v1/isolated/ggml-cuda.dll';foreign=out/'ggml-cuda.dll';shutil.copy2(original,foreign);expected=sha(original)
    need(sha(foreign)==expected,'own CPU stand-in copy differs')
    k=C.WinDLL('kernel32',use_last_error=True);k.GetModuleHandleW.argtypes=[W.LPCWSTR];k.GetModuleHandleW.restype=W.HMODULE;k.LoadLibraryExW.argtypes=[W.LPCWSTR,W.HANDLE,W.DWORD];k.LoadLibraryExW.restype=W.HMODULE;k.FreeLibrary.argtypes=[W.HMODULE];k.FreeLibrary.restype=W.BOOL
    need(not k.GetModuleHandleW('ggml-cuda.dll'),'unknown preexisting numerical module; do not unload it')
    handle=k.LoadLibraryExW(str(foreign),None,0x100|0x800);need(bool(handle),'own CPU stand-in collision setup failed')
    refused=False;message=''
    try:
        try:load_cpu_standin(original,original,expected)
        except ValueError as exc:message=str(exc);refused='foreign module' in message
    finally:k.FreeLibrary(handle)
    record={'schema':'heterospec.e03.foreign-module-cpu-test.v1','status':'PASS' if refused else 'FAIL','own_foreign_CPU_module':str(foreign),'expected_CPU_module':str(original),'both_file_sha256':expected,'refusal':message,'unknown_or_other_user_modules_unloaded':False,'actual_CUDA_DLL_loads':0,'own_CPU_standin_loads':1,'native_qualification':'NOT_RUN','GPU_launches':0,'scope':'real Windows same-basename resolution using CPU-only stand-ins; not numerical runtime qualification'}
    (out/'RESULT.json').write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps(record,indent=2))
    if not refused:raise SystemExit(1)
if __name__=='__main__':main()
