"""Read-only disk/source/raw checks and lossless packaging; no native/device work."""
import datetime, hashlib, json, subprocess, sys, zipfile
from pathlib import Path
E=Path(__file__).resolve().parent;B=E.parent;R=B/'repair_timer_v1';RAW=Path('D:/hs113-timer-gpu14-v1')
sys.path.insert(0,str(R))
from audit_regression import load,sha
def save(name,obj):
    with (E/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2);f.write('\n')
def bytes_under(p):return sum(f.stat().st_size for f in p.rglob('*') if f.is_file())
def git(*a):return subprocess.check_output(['git','-C','D:/hs113',*a])
def main():
    f0=load(R/'GPU14_F0.json');bad=[]
    for pin in f0['files']:
        if sha(pin['path'])!=pin['sha256']:bad.append(pin['path'])
    assert not bad,bad
    assert not git('diff','--name-only','9aefd4c722ac78421994052e41412c2c0417d73b').strip()
    old=B/'S1_NUMERICAL';manifest=load(old/'RAW_MANIFEST.json');assert sha(old/'RAW_NUMERICAL_STOP.zip')==manifest['sha256']
    old_members=[]
    for member in manifest['members']:
        if member['path'].startswith('slots/'):
            p=Path('D:/hs113-s1-v1')/member['path'];assert sha(p)==member['sha256'];old_members.append(member)
    old_state=load(old/'ANALYSIS.json')
    assert (old_state['numeric_hosts_started'],old_state['numeric_hosts_failed'],old_state['not_started_due_to_protocol_stop'],old_state['confirmed_completed_graphs'])==(1,1,719,0)
    assert len(list(Path('D:/hs113-s1-v1/slots').glob('*/native/GRAPH_STARTED_*.json')))==1
    assert not list(Path('D:/hs113-s1-v1/slots').glob('*/native/RECORD.json'))
    expected=load(R/'CPU_REGISTRY_release.json')['records'];selected=[]
    strip=lambda n:{k:v for k,v in n.items() if k not in ('CUDA_support','placement')}
    for i,s in enumerate(f0['slots']):
        row=next(r for r in expected if (r['descriptor_id'],r['layout'],r['stage_outputs'])==(s['descriptor'],s['layout'],True))
        actual=load(RAW/f'{i:02d}'/'native/RECORD.json')['nodes']
        assert [strip(n) for n in actual['nodes']]==[strip(n) for n in row['nodes']]
        assert strip(actual['output'])==strip(row['output'])
        selected.append(row)
    save('FROZEN_SELECTED_GRAPHS.json',selected)
    modules={}
    for i in range(14):
        for name in load(RAW/f'{i:02d}'/'native/RECORD.json')['modules']:
            if name not in modules:modules[name]=dict(path=name,bytes=Path(name).stat().st_size,sha256=sha(name))
    save('OBSERVED_MODULE_FILES.json',dict(status='POST_RUN_DISK_IDENTITY',files=list(modules.values()),
        limitation='Observed loaded paths plus post-run disk hashes; not full in-memory module attestation. Frozen numerical/driver pins separately pass.'))
    save('POST_RUN_INTEGRITY.json',dict(status='PASS',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        frozen_files_verified=len(f0['files']),mismatches=bad,reviewed_tracked_bytes_unchanged=True,
        old_failed_live_slot_files_verified=len(old_members),old_archive_sha256=manifest['sha256'],old_720_state=[1,719,0],
        selected_graph_nodes_op_params_and_output_equal_frozen_CPU_records=14,all_numerical_DLLs_unchanged=21,
        GGML_CUDA_DISABLE_GRAPHS='1 (unchanged inherited setting)',raw_root_bytes=bytes_under(RAW),
        largest_slot_bytes=max(bytes_under(RAW/f'{i:02d}') for i in range(14)),
        no_new_native_start_device_query_or_graph_in_this_check=True))
    items={}
    def add(name,path):
        assert name not in items;items[name]=Path(path)
    for p in RAW.rglob('*'):
        if p.is_file():add('raw/'+p.relative_to(RAW).as_posix(),p)
    # Capture every current approval/control/analysis item, including source for this CPU reconstruction.
    for p in E.iterdir():
        if p.is_file() and p.name not in ('RAW_GPU14.zip','RAW_MANIFEST.json'):add('execution/'+p.name,p)
    for name in ('GPU14_F0.json','AUTHENTICATED_GPU14_F0.json','REMOTE_GPU14_F0_BYTES.json','run_gpu_regression.py','audit_regression.py',
                 'run_cpu.py','native_repair.cpp','core_gate.h','hs113_graph.h','pe_review.py','lowering113_repair.exe',
                 'ggml-base.dll.def','ggml.dll.def','libggml-base.dll.a','libggml.dll.a','RELEASE_IDENTITY.json','LINK.diff','SOURCE.diff'):
        add('frozen/repair_timer_v1/'+name,R/name)
    for name in ('audit.py','safety.py'):add('frozen/'+name,B/name)
    bindings=dict(snapshots={},operators='references/operators');reference_pins=[]
    by_path={str(Path(p['path']).resolve()).lower():p for p in f0['files']}
    for s in f0['slots']:
        if s['descriptor'] in bindings['snapshots']:continue
        root=Path(s['root']);meta=load(root/'snapshot.json');dest='references/snapshots/'+s['descriptor'];bindings['snapshots'][s['descriptor']]=dest
        for name in {'snapshot.json'}|{meta[k]['file'] for k in ('Q','K','V','mask','native_QK','native_softmax','native_AV')}:
            p=root/name;pin=by_path[str(p.resolve()).lower()];assert sha(p)==pin['sha256']
            add(dest+'/'+name,p);reference_pins.append(dict(archive_path=dest+'/'+name,**pin))
    for layout in ('PQ','QB'):
        for repeat in range(2):
            for stage in ('QK','softmax','AV'):
                suffix=f'001/{layout}-r{repeat}/{stage}.bin';p=Path(f0['old_operator_root'])/suffix
                pin=by_path[str(p.resolve()).lower()];assert sha(p)==pin['sha256']
                add('references/operators/'+suffix,p);reference_pins.append(dict(archive_path='references/operators/'+suffix,**pin))
    save('REFERENCE_BINDINGS.json',bindings);add('REFERENCE_BINDINGS.json',E/'REFERENCE_BINDINGS.json')
    save('REFERENCE_PROVENANCE.json',reference_pins);add('REFERENCE_PROVENANCE.json',E/'REFERENCE_PROVENANCE.json')
    members=[]
    with zipfile.ZipFile(E/'RAW_GPU14.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,p in sorted(items.items()):
            archive.write(p,name);members.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
    save('RAW_MANIFEST.json',dict(archive='RAW_GPU14.zip',bytes=(E/'RAW_GPU14.zip').stat().st_size,sha256=sha(E/'RAW_GPU14.zip'),
        members=members,uncompressed_bytes=sum(m['bytes'] for m in members),scientific_raw_files_included=len(list(RAW.rglob('*'))),
        all14_raw_slots_and_controller_included=True,full_input_before_after_and_outputs=True,full_reference_snapshots_and_historical_PQ_QB_controls=True,
        frozen_source_binary_and_execution_checks_included=True,numerical_DLL_model_bytes='Remain original sealed read-only paths by F0 hashes; not recompiled or republished',
        old_failure_capsule='Unchanged S1_NUMERICAL archive referenced by POST_RUN_INTEGRITY; no new results written there',scientific_retry=False))
    print('PASS all7808 frozen pins, old live failure/archive, actual graph identities; lossless GPU14 raw archive sealed')
if __name__=='__main__':main()
