"""Authenticated repair/F0 readback and CPU-only fresh raw reconstruction.

Does not run any native executable, device query, plugin or graph computation.
"""
import argparse,hashlib,importlib.util,json,subprocess,sys,urllib.request,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
    target=Path('D:/hs113-timer-repair-authenticated-v1');target.mkdir(exist_ok=False)
    token=subprocess.run(['gh','auth','token'],capture_output=True,check=True).stdout.decode().strip();assert token
    received=[]
    for name in ('GPU14_F0.json','RAW_REPAIR.zip','RAW_REPAIR_MANIFEST.json','RELEASE_IDENTITY.json','CPU_TIMER_TESTS_final.json','authenticate_repair.py'):
        url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/repair_timer_v1/'+name+'?ref='+a.commit
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-immutable-byte-readback'})
        with urllib.request.urlopen(req,timeout=60) as response:
            assert response.status==200 and response.headers.get('Content-Encoding','identity')=='identity';data=response.read()
        with (target/name).open('xb') as f:f.write(data)
        assert data==(R/name).read_bytes()
        received.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),endpoint=url))
    save(R/'AUTHENTICATED_GPU14_F0.json',dict(authenticated_commit=a.commit,sha256=sha(target/'GPU14_F0.json'),bytes=(target/'GPU14_F0.json').stat().st_size,authenticated_remote_bytes=True,GPU_authorization='NOT_GRANTED',transport='GitHub raw API, in-memory token, identity encoding; token not recorded'))
    with (R/'REMOTE_GPU14_F0_BYTES.json').open('xb') as f:f.write((target/'GPU14_F0.json').read_bytes())
    save(R/'AUTHENTICATED_REPAIR_RAW.json',dict(authenticated_commit=a.commit,files=received,authenticated_remote_bytes=True))
    manifest=json.loads((target/'RAW_REPAIR_MANIFEST.json').read_bytes());assert sha(target/'RAW_REPAIR.zip')==manifest['sha256']
    fresh=Path('D:/hs113-timer-repair-fresh-restore-v1');fresh.mkdir(exist_ok=False)
    with zipfile.ZipFile(target/'RAW_REPAIR.zip') as z:
        names=z.namelist();assert len(names)==len(set(names))==len(manifest['members'])
        assert set(names)=={r['path'] for r in manifest['members']}
        for name in names:
            p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name
        z.extractall(fresh)
    for r in manifest['members']:
        p=fresh/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
    sys.path.insert(0,str(fresh));spec=importlib.util.spec_from_file_location('restored_timer_auditor',fresh/'test_cpu.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    for p in sorted((fresh/'cpu_results_final').glob('positive_A[0-9].json')):module.audit(json.loads(p.read_bytes()))
    negative=list((fresh/'cpu_results_final').glob('*.json'));native_negatives=[json.loads(p.read_bytes()) for p in negative if not p.name.endswith('.controller.json') and not p.name.startswith('positive_A')]
    assert len(native_negatives)==5 and all(not r['admitted'] and r['expected_rejection'] for r in native_negatives)
    registry=json.loads((fresh/'CPU_REGISTRY_release.json').read_bytes());expected=json.loads((fresh/'reference/SUPPORT_REGISTRY_S0.json').read_bytes())
    assert registry['records']==expected['records'] and registry['graphs']==1680 and registry['GPU_initializations']==registry['graph_computes']==0
    from pe_review import PE
    imports=PE(fresh/'lowering113_repair.exe').imports();assert 'ggml_init' in imports['ggml-base.dll'] and 'ggml_backend_load' in imports['ggml.dll']
    old=json.loads((fresh/'reference/OLD_720_ANALYSIS.json').read_bytes());assert (old['numeric_hosts_started'],old['numeric_hosts_failed'],old['not_started_due_to_protocol_stop'],old['confirmed_completed_graphs'])==(1,1,719,0)
    f0=json.loads((fresh/'GPU14_F0.json').read_bytes());assert len(f0['slots'])==14 and f0['limits']['support_API_queries']==166
    assert [s['group'] for s in f0['slots']]==['common_q1']*6+['q2_diagnostic']*8
    save(R/'FRESH_RESTORE.json',dict(status='PASS',authenticated_data_commit=a.commit,archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
        restored_final_real_CPU_positive_receipts_reaudited=3,negative_receipts_reaudited=5,full_CPU_graph_records_equal=1680,PE_shared_imports_verified=True,
        original_720_state_retained=[1,719,0],GPU14_slots=14,support_queries_planned=166,GPU14_authorization='NOT_GRANTED',
        new_native_starts=0,new_GPU_plugin_loads=0,new_device_queries=0,new_graph_computes=0,new_model_requests=0,
        scope='CPU reconstruction of full raw and actual native CPU receipts, not fresh device execution or universal numerical admission',destination=str(fresh)))
    print('PASS authenticated F0/raw,295 restored members,3 actual-positive/5negative receipts,1680 graph records; GPU14 not started')
if __name__=='__main__':main()
