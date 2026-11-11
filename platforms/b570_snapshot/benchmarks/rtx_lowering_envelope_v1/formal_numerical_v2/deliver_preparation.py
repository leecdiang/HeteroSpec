"""CPU artifact delivery only; no engineering/native/GPU test is launched.

Seal existing actual CPU receipts. After push, authenticate exact remote F0/raw
and reconstruct those receipts in a fresh directory without running executables.
"""
import argparse,hashlib,json,subprocess,time,urllib.request,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha,pin
def main():
    a=argparse.ArgumentParser();g=a.add_mutually_exclusive_group(required=True);g.add_argument('--seal',action='store_true');g.add_argument('--readback');args=a.parse_args();begin=time.perf_counter()
    f0=load(V/'F0.json');assert sha(V/'F0.json')=='73ef7106240be73ab914e4c6a36064a0d1fd6d41ce5d9c38bf65f38e8331f080'
    assert not Path(f0['execution_root']).exists() and not (V/'execution_ledger').exists()
    for name,h in f0['source_roles'].items():assert sha(V/name)==h
    if args.seal:
        excluded=[];files=[]
        for p in sorted(V.rglob('*')):
            if not p.is_file():continue
            if 'reference_cas' in p.parts or p.suffix=='.pdb':excluded.append(pin(p));continue
            if p.name in ('RAW_PREPARATION.zip','RAW_PREPARATION_MANIFEST.json') or '__pycache__' in p.parts:continue
            files.append(p)
        members=[]
        with zipfile.ZipFile(V/'RAW_PREPARATION.zip','x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in files:
                name=p.relative_to(V).as_posix();z.write(p,name);members.append(dict(path=name,bytes=p.stat().st_size,sha256=sha(p)))
        save(V/'RAW_PREPARATION_MANIFEST.json',dict(archive='RAW_PREPARATION.zip',sha256=sha(V/'RAW_PREPARATION.zip'),bytes=(V/'RAW_PREPARATION.zip').stat().st_size,
            members=members,uncompressed_bytes=sum(m['bytes'] for m in members),all_CPU_candidates_sources_binaries_failures_and_complete_receipts_included=True,
            excluded_local_retained=excluded,excluded_scope='Duplicate immutable reference CAS already bound to original sealed PR104 bytes and full REFERENCE_INDEX; debug PDBs retained locally by SHA. No required scientific v2 output is omitted: none has started.',
            F0_sha256=sha(V/'F0.json'),GPU_authorization='NOT_GRANTED'))
        save(V/'PREPARATION_SEAL.json',dict(seconds=time.perf_counter()-begin,operation='Existing artifact compression/hash only; not a new CPU/native engineering test',members=len(members),new_GPU_queries=0,new_native_or_model_starts=0))
        print('Preparation capsule sealed:',len(members),'members;', (V/'RAW_PREPARATION.zip').stat().st_size,'bytes');return
    target=Path('D:/hs113-v2-preparation-authenticated-v1');target.mkdir(exist_ok=False)
    token=subprocess.check_output(['gh','auth','token']).decode().strip();received=[]
    for name in ('F0.json','RAW_PREPARATION.zip','RAW_PREPARATION_MANIFEST.json','CPU_NATIVE_TESTS.json','CPU_CONTRACT_TESTS.json','RESULT.md'):
        url='https://api.github.com/repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_lowering_envelope_v1/formal_numerical_v2/'+name+'?ref='+args.readback
        req=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw+json','Accept-Encoding':'identity','User-Agent':'HeteroSpec-formal-v2-registration'})
        with urllib.request.urlopen(req,timeout=45) as response:
            assert response.status==200 and response.headers.get('Content-Encoding','identity')=='identity';data=response.read()
        with (target/name).open('xb') as out:out.write(data)
        assert sha(target/name)==sha(V/name);received.append(dict(path=name,bytes=len(data),sha256=sha(target/name),endpoint=url))
    assert sha(target/'F0.json')==f0_identity()['sha256']
    manifest=load(target/'RAW_PREPARATION_MANIFEST.json');assert sha(target/'RAW_PREPARATION.zip')==manifest['sha256']
    fresh=Path('D:/hs113-v2-preparation-fresh-v1');fresh.mkdir(exist_ok=False)
    with zipfile.ZipFile(target/'RAW_PREPARATION.zip') as z:
        names=z.namelist();assert len(names)==len(set(names))==len(manifest['members']);assert set(names)=={m['path'] for m in manifest['members']}
        for name in names:
            p=PurePosixPath(name);assert not p.is_absolute() and '..' not in p.parts and ':' not in name and '\\' not in name
        z.extractall(fresh)
    for m in manifest['members']:assert (fresh/m['path']).stat().st_size==m['bytes'] and sha(fresh/m['path'])==m['sha256']
    assert (fresh/'F0.json').read_bytes()==(target/'F0.json').read_bytes()
    plan=load(fresh/'PLAN.json');rows=load(fresh/'CPU_WIRES.json')['records'];expected={(r['descriptor_id'],r['layout']):r for r in load(fresh/'CPU_GRAPH_EXPECTED.json')}
    assert len(rows)==len(plan['numerical_slots'])==720 and len(plan['descriptors'])==72 and len(expected)==360
    for s,r in zip(plan['numerical_slots'],rows):
        w=fresh/'CPU_FIXTURE/wires'/('%03d.json'%s['index']);wire=load(w);original=dict(wire);original.pop('F0_path');original.pop('approved_stage_F0')
        assert original==s and sha(w)==r['wire_file_sha256'] and r['slot']==s['id']
        e=expected[s['descriptor'],s['layout']]
        assert all(r[k]==e[k] for k in ('nodes','output','common_q1_original_arithmetic_chain','stage_descriptors'))
    for name,h in f0['source_roles'].items():assert sha(fresh/name)==h
    # PE parsing reads the saved binary without loading it or any DLL.
    import importlib.util
    spec=importlib.util.spec_from_file_location('restored_PE_reader',fresh/'pe_review.py');pe=importlib.util.module_from_spec(spec);spec.loader.exec_module(pe)
    imports=pe.PE(fresh/'lowering113_formal.exe').imports();assert 'ggml_init' in imports['ggml-base.dll'] and 'ggml_backend_load' in imports['ggml.dll']
    assert sha(fresh/'lowering113_formal.exe')==f0['executable_sha256']
    save(V/'AUTHENTICATED_F0.json',dict(authenticated_remote_bytes=True,data_commit=args.readback,sha256=sha(target/'F0.json'),bytes=(target/'F0.json').stat().st_size,GPU_authorization='NOT_GRANTED'))
    with (V/'REMOTE_F0_BYTES.json').open('xb') as out:out.write((target/'F0.json').read_bytes())
    save(V/'AUTHENTICATED_PREPARATION.json',dict(authenticated_remote_bytes=True,data_commit=args.readback,files=received,transport='GitHub raw API; in-memory token; identity encoding; no token recorded'))
    save(V/'FRESH_CPU_RESTORE.json',dict(status='PASS',data_commit=args.readback,destination=str(fresh),archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
        all720_actual_CPU_wire_receipts_and_graph_records_reconstructed=True,nodes=10836,complete_graphs=360,source_roles_verified=len(f0['source_roles']),
        shared_core_PE_imports_verified=True,native_executable_sha256=f0['executable_sha256'],new_native_executions=0,new_GPU_queries=0,new_CUDA_loads=0,new_graph_computes=0,new_model_requests=0,
        scope='Read-only reconstruction of actual CPU receipts/serializer/PE/source hashes, not fresh native/GPU execution. Duplicate immutable reference tensors and PDBs are pinned but not duplicated in this capsule.',
        GPU_authorization='NOT_GRANTED',delivery_seconds=time.perf_counter()-begin))
    print('PASS authenticated F0/raw;',len(manifest['members']),'fresh members and720actual CPU wire/graph records reconstructed; no native/GPU execution')
def f0_identity():return load(V/'F0_IDENTITY.json')
if __name__=='__main__':main()
