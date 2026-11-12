"""Exercise Windows DLL path/disk identity with a bounded CPU-only stand-in."""
from pathlib import Path
import ctypes as C
from ctypes import wintypes as W
import hashlib,json,os,shutil,subprocess,time
from pe_identity import inspect

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)
def load_cpu_standin(path,expected_path,expected_sha):
    path=Path(path).resolve();expected_path=Path(expected_path).resolve()
    need(path==expected_path,'resolved path differs from independently frozen CPU mock path')
    need(sha(path)==expected_sha,'DLL disk SHA mismatch before LoadLibrary')
    pe=inspect(path)
    need('hs_e03_cpu_mock_marker' in pe['exports'],'refuse non-mock DLL before LoadLibrary')
    need(not any(any(word in name.lower() for word in ('cuda','cublas','nvidia','cudnn')) for name in pe['imports']),'refuse GPU-dependent DLL in CPU test')
    k=C.WinDLL('kernel32',use_last_error=True);k.LoadLibraryExW.argtypes=[W.LPCWSTR,W.HANDLE,W.DWORD];k.LoadLibraryExW.restype=W.HMODULE
    k.GetModuleHandleW.argtypes=[W.LPCWSTR];k.GetModuleHandleW.restype=W.HMODULE
    k.GetModuleFileNameW.argtypes=[W.HMODULE,W.LPWSTR,W.DWORD];k.GetModuleFileNameW.restype=W.DWORD
    k.GetProcAddress.argtypes=[W.HMODULE,C.c_char_p];k.GetProcAddress.restype=C.c_void_p;k.FreeLibrary.argtypes=[W.HMODULE];k.FreeLibrary.restype=W.BOOL
    def actual(module):
        text=C.create_unicode_buffer(32768);n=k.GetModuleFileNameW(module,text,len(text));need(0<n<len(text),'actual loaded path unavailable');return Path(text.value).resolve()
    prior=k.GetModuleHandleW(path.name)
    if prior:need(actual(prior)==path,'foreign module with numerical basename already loaded')
    handle=k.LoadLibraryExW(str(path),None,0x100|0x800)
    need(bool(handle),'CPU stand-in LoadLibrary failed '+str(C.get_last_error()))
    try:
        resolved=actual(handle);need(resolved==path and sha(resolved)==expected_sha,'actual loaded module path/hash differs')
        marker=k.GetProcAddress(handle,b'hs_e03_cpu_mock_marker');fn=k.GetProcAddress(handle,b'hs_e03_runtime_metadata');need(marker and fn,'mock identity exports missing')
        need(C.CFUNCTYPE(C.c_int)(marker)()==0x0303,'mock marker mismatch')
        metadata=json.loads(C.CFUNCTYPE(C.c_char_p)(fn)().decode('utf8'))
        need(metadata=={'schema':'heterospec.e03.cpu-loader-mock.v1','scope':'CPU_STANDIN_NOT_NUMERICAL_RUNTIME'},'wrong mock metadata')
        return {'actual_loaded_path':str(resolved),'disk_sha256':expected_sha,'metadata':metadata,'scope':'CPU_STANDIN_ONLY','numeric_route_observed':False,'native_qualification':'NOT_RUN'}
    finally:k.FreeLibrary(handle)

def main():
    out=HERE/'cpu-loader-test-v1';out.mkdir(exist_ok=False);bin=out/'isolated';bin.mkdir()
    vc=Path('D:/rtx184-tools/msvc/VC/Tools/MSVC/14.44.35207');sdk=Path('D:/rtx184-tools/msvc/Windows Kits/10');version='10.0.26100.0'
    env=os.environ.copy();env['PATH']=str(vc/'bin/Hostx64/x64')+os.pathsep+env.get('PATH','');env['INCLUDE']=';'.join(str(p) for p in [vc/'include',*[sdk/'Include'/version/x for x in ['ucrt','shared','um','winrt']]]);env['LIB']=';'.join(str(p) for p in [vc/'lib/x64',sdk/'Lib'/version/'ucrt/x64',sdk/'Lib'/version/'um/x64'])
    dll=bin/'ggml-cuda.dll';args=[str(vc/'bin/Hostx64/x64/cl.exe'),'/nologo','/O2','/MT','/LD',str(HERE/'cpu_loader_mock.c'),'/Fo:'+str(out/'cpu_loader_mock.obj'),'/Fe:'+str(dll),'/link','/IMPLIB:'+str(out/'cpu_loader_mock.lib')]
    began=time.monotonic();r=subprocess.run(args,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);(out/'build.log').write_bytes(r.stdout)
    build={'argv':args,'returncode':r.returncode,'seconds':time.monotonic()-began,'source_sha256':sha(HERE/'cpu_loader_mock.c'),'log_sha256':sha(out/'build.log')};need(r.returncode==0,'mock build failed')
    pe=inspect(dll);(out/'CPU_MOCK_PE.json').write_text(json.dumps(pe,indent=2),encoding='utf8');expected=sha(dll);cases=[]
    result=load_cpu_standin(dll,dll,expected);cases.append({'case':'actual CPU-only DLL metadata/path/disk hash','passed':True,'result':result})
    for name,path,frozen_path,digest,reason in [('wrong-disk-hash',dll,dll,'0'*64,'SHA mismatch'),('old-or-foreign-resolved-path',dll,out/'foreign/ggml-cuda.dll',expected,'resolved path differs')]:
        refused=False
        try:load_cpu_standin(path,frozen_path,digest)
        except ValueError as exc:refused=reason in str(exc)
        cases.append({'case':name,'passed':refused,'numeric_DLL_load_attempted':False})
    receipt={'schema':'heterospec.e03.cpu-loader-tests.v1','status':'PASS' if all(x['passed'] for x in cases) else 'FAIL','build':build,'cases':cases,'actual_CPU_standin_DLL_loads':1,'actual_numeric_CUDA_DLL_loads':0,'model_requests':0,'GPU_launches':0,'scope':'MOCK_ONLY; not actual numerical DLL binding, dispatcher selection, or GPU qualification'}
    (out/'RESULT.json').write_text(json.dumps(receipt,indent=2),encoding='utf8');print(json.dumps(receipt,indent=2))
    if receipt['status']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
