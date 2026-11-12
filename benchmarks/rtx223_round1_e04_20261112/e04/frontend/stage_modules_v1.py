"""Stage pinned non-system DLL bytes only; no LoadLibrary or worker invocation."""
from pathlib import Path
import hashlib,json,shutil,datetime
from pe_identity_v2 import inspect
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
AUDIT=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx223-round1-resume-20261112-e03/audit/DISK_IDENTITIES.json')
OLD=Path('D:/rtx211-q8-20261109/loop4-v2/bin');OLD_B=Path('D:/rtx211-q8-20261109/packed-v2/bin')
CUDA=ROOT/'runtime/toolchain-v1/cuda/bin';MSVC=ROOT/'runtime/toolchain-v2/msvc/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64'
OUT=HERE/'expected-modules-v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(v,m):
    if not v:raise RuntimeError(m)
def put(p,j):
    with Path(p).open('x',encoding='utf8',newline='\n') as f:json.dump(j,f,indent=2)
def is_system(name):return name.startswith(('api-ms-','ext-ms-')) or name in {'kernel32.dll','kernelbase.dll','ntdll.dll','advapi32.dll','user32.dll','gdi32.dll','shell32.dll','ole32.dll','oleaut32.dll','ws2_32.dll','bcrypt.dll','secur32.dll','rpcrt4.dll','crypt32.dll','version.dll','winmm.dll','msvcrt.dll','shlwapi.dll','psapi.dll','normaliz.dll','imm32.dll','setupapi.dll','cfgmgr32.dll','dbghelp.dll'}
def main():
    OUT.mkdir(exist_ok=False);prior=json.loads(AUDIT.read_bytes());roles={v['role']:v for v in prior['inventory'] if v.get('role') in ('loop4','packed')}
    pins={}
    for role,v in roles.items():
        pins[role]={Path(x['path']).name.casefold():x['expected'] for x in v['disk_files'] if x.get('matches') is True and x.get('expected')}
    initial={'ggml-base.dll':Path('D:/rtx184-operator/cuda-v2/bin/ggml-base.dll'),'cudart64_12.dll':CUDA/'cudart64_12.dll','cublas64_12.dll':CUDA/'cublas64_12.dll','cublaslt64_12.dll':CUDA/'cublasLt64_12.dll','msvcp140.dll':MSVC/'msvcp140.dll','vcruntime140.dll':MSVC/'vcruntime140.dll','vcruntime140_1.dll':MSVC/'vcruntime140_1.dll'}
    queue=list(initial.items());selected={};externals=set();missing=set();edges=[]
    while queue:
        name,src=queue.pop(0);name=name.casefold()
        if name in selected:continue
        before=sha(src);old_matches={r:sha(r/name)==before for r in (OLD,OLD_B) if (r/name).is_file()}
        if name in pins['loop4'] or name in pins['packed']:
            need(pins['loop4'].get(name)==before==pins['packed'].get(name),'same-contract pinned module differs: '+name)
            identity='MATCHES_BOTH_PRIOR_LOOP4_PACKED_CONTRACT_PINS'
        else:
            need(old_matches and all(old_matches.values()),'new unpinned runtime differs from old Windows entries: '+name)
            identity='OLD_WINDOWS_ENTRY_DISK_MATCH_PRIOR_CONTRACT_PIN_NOT_RECORDED_NATIVE_UNQUALIFIED'
        target=OUT/name;shutil.copy2(src,target);need(sha(src)==before==sha(target),'module source/copy identity changed')
        pe=inspect(target);selected[name]={'path':str(target),'source':str(src),'bytes':target.stat().st_size,'sha256':before,'prior_contract_identity':identity,'prior_loop4_packed_expected':{role:pins[role].get(name) for role in pins},'old_entry_current_disk_matches':{str(k):v for k,v in old_matches.items()},'PE':pe}
        for dep in pe['imports']+pe['delay_imports']:
            dep=dep.casefold();edges.append({'from':name,'to':dep})
            if is_system(dep):externals.add(dep);continue
            if dep in selected:continue
            source=initial.get(dep)
            if source is None:
                candidates=[root/dep for root in (OLD,MSVC,CUDA) if (root/dep).is_file()]
                source=candidates[0] if candidates else None
            if source is None:missing.add(dep)
            else:queue.append((dep,source))
    put(OUT/'STAGED_DEPENDENCIES.json',{'schema':'heterospec.e04.expected-module-disk-closure.v1','status':'PINNED_DEPENDENCIES_STAGED_NUMERIC_DLL_PENDING' if not missing else 'INCOMPLETE_DISK_CLOSURE','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_audit':str(AUDIT),'prior_audit_sha256':sha(AUDIT),'modules':selected,'edges':edges,'external_system_or_API_set_imports':sorted(externals),'unresolved_non_system_imports':sorted(missing),'same_module_policy_for_arms':['A','B','C'],'R_Qwen_runtime_is_separate_role':True,'numeric_DLL':'PENDING_FINAL_BUILD','loaded_module_identity':'NOT_RUN','system_API_set_resolution':'NOT_RUN','dynamic_driver_and_plugin_loads':'NOT_RUN; not inferable from PE direct/delay imports','semantic_ABI_and_numerical_qualification':'NOT_RUN','normal_numeric_DLL_loads':0,'GPU_launches':0,'model_requests':0,'public_archive_policy':'DLL binary bytes excluded; retain identities/PE metadata only'})
    print(json.dumps({'staged_modules':len(selected),'unresolved_non_system':sorted(missing),'normal_numeric_DLL_loads':0}))
if __name__=='__main__':main()
