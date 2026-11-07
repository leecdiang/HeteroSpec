from pathlib import Path
from common import V,load,sha

def norm(p):return str(Path(p).resolve()).lower()

def verify_modules(native,record,f0,module_files):
    gate=load(native/'CORE_ADMITTED_BEFORE_CUDA.json');core=gate['core'];exports=load(V/'ABI_EXPORTS.json')
    assert core['sha256']==f0['numerical_DLLs']['ggml-base.dll'] and norm(core['path'])==norm(Path(f0['runtime_directory'])/'ggml-base.dll')
    assert core['ready'] and core['events'].count('dll_initializer_returned')==1
    base=core['module_handle']
    for name,fn in core['functions'].items():
        assert fn['address']==base+exports['core'][name]['RVA'] and norm(fn['owner_path'])==norm(core['path'])
    host=gate['host_import'];assert host['IAT_target']==core['functions']['ggml_init']['address'] and host['module_handle']==base and norm(host['owner_path'])==norm(core['path'])
    reg=gate['registry_import'];assert reg['sha256']==f0['numerical_DLLs']['ggml.dll'] and norm(reg['path'])==norm(Path(f0['runtime_directory'])/'ggml.dll')
    assert reg['backend_load_IAT_target']==reg['owner']+exports['registry']['ggml_backend_load']['RVA']
    plugin=load(native/'PLUGIN_CORE_IMPORTS.json');assert len(plugin)==41 and {p['symbol'] for p in plugin}==set(exports['plugin_core_symbols'])
    assert all(norm(p['owner_path'])==norm(core['path']) and p['target']==base+exports['core'][p['symbol']]['RVA'] for p in plugin)
    inventory={norm(p['path']):p for p in module_files};seen=set()
    for path in record['modules']:
        assert norm(path) in inventory,'every observed module must have a disk identity receipt'
        name=Path(path).name.lower()
        if name in {s.lower() for s in f0['numerical_DLLs']}:
            expected=next(h for n,h in f0['numerical_DLLs'].items() if n.lower()==name)
            assert norm(Path(path).parent)==norm(f0['runtime_directory']) and inventory[norm(path)]['sha256']==expected;seen.add(name)
    assert {'ggml-base.dll','ggml.dll','ggml-cuda.dll','cublas64_12.dll','cublaslt64_12.dll','cudart64_12.dll'}<=seen
    assert inventory[norm(f0['executable'])]['sha256']==f0['executable_sha256']
    assert norm(f0['executable']) in {norm(p) for p in record['modules']}
    return core

def process_identity(directory,prefix,f0,native_limit=60):
    proc=load(directory/(prefix+'.PROCESS.json'));life=load(directory/(prefix+'.LIFETIME.json'));events=load(directory/(prefix+'.JOB_EVENTS.json'))
    assert proc['pid']==life['pid']==events['registered_PID'] and type(proc['creation_filetime_100ns'])is int and proc['creation_filetime_100ns']>0
    assert proc['creation_filetime_100ns']==life['creation_filetime_100ns'] and life['error'] is None and life['exit_code']==0
    assert proc['creation_flags']==0x08000000|4 and proc['active_process_limit']==2 and proc['suspended_before_job_assignment']
    assert not events['errors'];started=[e for e in events['events'] if e['message']==6]
    assert {e['pid'] for e in started}==set(events['started_unique_PIDs']) and len(started)==life['job_total_processes']<=2
    assert sum(e['pid']==proc['pid'] for e in started)==1 and not list(directory.glob(prefix+'.*.OVERFLOW.json'))
    expected=f0['executable'] if prefix=='native' else f0['admission_policy']['nvidia_smi']
    for e in started:assert norm(e['image'])==norm(expected if e['pid']==proc['pid'] else f0['console_helper']['path'])
    assert events['console_helper_pin']['sha256']==f0['console_helper']['sha256']
    assert 0<=life['seconds']<= (native_limit if prefix=='native' else 10)
    return (proc['pid'],proc['creation_filetime_100ns'])
