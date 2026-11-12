"""Read-only PE/volume and external artifact binding; never load numerical modules."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,datetime
from ctypes import wintypes as W
from pe_identity_e04 import inspect

HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def put(p,j):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:json.dump(j,f,indent=2)
def volume(path):
    kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetVolumeInformationW.argtypes=[W.LPCWSTR,W.LPWSTR,W.DWORD,C.POINTER(W.DWORD),C.POINTER(W.DWORD),C.POINTER(W.DWORD),W.LPWSTR,W.DWORD]
    kernel.GetVolumeInformationW.restype=W.BOOL
    root=Path(path).resolve().anchor;name=C.create_unicode_buffer(1024);fs=C.create_unicode_buffer(1024);serial=W.DWORD();component=W.DWORD();flags=W.DWORD()
    need(kernel.GetVolumeInformationW(root,name,len(name),C.byref(serial),C.byref(component),C.byref(flags),fs,len(fs)),'volume information unavailable')
    return {'root':root,'serial_hex':f'{serial.value:08x}','filesystem':fs.value,'volume_label':name.value,'scope':'local volume identity, not physical-device attestation'}
def host(run):
    run=Path(run).resolve();build=json.loads((run/'BUILD.json').read_bytes());freeze=json.loads((run/'FREEZE.json').read_bytes())
    need(build['status']=='PASS_FROZEN_BUILD_NOT_NATIVE_QUALIFIED','frontend frozen build did not pass')
    records=[]
    for output in build['outputs']:
        info=inspect(output['exe']);need(info['sha256']==output['exe_sha256'],'frontend EXE changed after build')
        banned=[x for x in info['imports'] if any(word in x.casefold() for word in ('cuda','cudart','cublas','ggml','nvcuda','nvrtc'))]
        need(not banned,'numerical direct import found: '+repr(banned))
        info.update(core=output['core'],numeric_direct_import_check='PASS',worker_execution='NOT_RUN',initializer_execution='NOT_RUN',scope='offline imports only; no EXE, TLS/CRT initializer, model, or numerical DLL executed')
        records.append(info)
    roots=sorted({Path(e['path']).anchor for e in freeze['entries']})
    output={'schema':'heterospec.e04.frontend-host-artifacts.v1','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'build':str(run/'BUILD.json'),'build_sha256':sha(run/'BUILD.json'),'freeze':str(run/'FREEZE.json'),'freeze_sha256':sha(run/'FREEZE.json'),'postfreeze_sha256':sha(run/'POSTFREEZE.json'),'codegen_input_bytes':sum(e['bytes'] for e in freeze['entries']),'frozen_input_count':len(freeze['entries']),'volumes':[volume(x) for x in roots],'PEs':records,'pe_inspector_sha256':sha(HERE/'pe_identity_e04.py'),'new_worker_EXE_runs':0,'normal_numeric_DLL_loads':0,'GPU_launches':0,'model_requests':0,'native_gate':'BLOCKED','scope':'new frontend TU compile/link; existing pinned core/CRT archives retained as binary dependencies; Python and mutable Windows runtime DLLs outside freeze scope'}
    put(HERE/'HOST_ARTIFACTS_v4.json',output);return output
def bind(host_path,dll,native_build,native_freeze):
    h=json.loads(Path(host_path).read_bytes());p=inspect(dll)
    need(p['is_dll'],'runtime artifact is not DLL')
    names=('hs_e03_runtime_metadata','hs_e03_select_arm','hs_launch_budget_configure_v1','hs_launch_budget_snapshot_v1')
    need(all(name in p['exports'] for name in names),'runtime ABI exports missing')
    for e in h['PEs']:need(sha(e['path'])==e['sha256'],'frontend identity changed before binding')
    value={'schema':'heterospec.e04.frontend-numeric-artifact-binding.v1','host_manifest':str(Path(host_path).resolve()),'host_manifest_sha256':sha(host_path),'numeric_DLL':p,'native_build_manifest':str(Path(native_build).resolve()),'native_build_manifest_sha256':sha(native_build),'native_freeze_manifest':str(Path(native_freeze).resolve()),'native_freeze_manifest_sha256':sha(native_freeze),'binding_kind':'EXTERNAL_DISK_ARTIFACT_ONLY','EXEs_and_DLL_have_no_compiled_hash_cycle':True,'native_gate':'BLOCKED','numeric_DLL_OS_load':'NOT_RUN','A_B_C_native_path_selection':'NOT_RUN','GPU_qualification':'NOT_RUN','GPU_launches':0,'model_requests':0}
    put(HERE/'DEPLOYMENT_BINDING_v1.json',value);return value
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('action',choices=('host','bind','inspect'));a.add_argument('--run');a.add_argument('--dll');a.add_argument('--out');a.add_argument('--host');a.add_argument('--native-build');a.add_argument('--native-freeze');v=a.parse_args()
    if v.action=='host':result=host(v.run)
    elif v.action=='bind':result=bind(v.host,v.dll,v.native_build,v.native_freeze)
    else:result=inspect(v.dll);put(v.out,result)
    print(json.dumps({'status':'PASS_DISK_ONLY','normal_numeric_DLL_loads':0,'GPU_launches':0}))
