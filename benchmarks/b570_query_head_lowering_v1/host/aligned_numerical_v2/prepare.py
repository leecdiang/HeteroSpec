"""Offline build + actual native wire/graph parsing + fresh CPU analysis tests.

Never launches aligned-host-v2.exe, any device tool, model, or graph computation.
All preparation attempts/source snapshots and logs are retained prospectively.
"""
import difflib
import io
import json
import pathlib
import shutil
import struct
import subprocess
import sys
import time
import unittest
import zipfile
from panel_common import HERE,ROOT,RUN_ID,RUN,MODES,LIMITS,load,save,sha,digest,encode,serialize,build_plan,modules,need
from reference import solve

BASE='74d8bee4fd738c67e2f08169beb5164bac5efe98'
OUT=ROOT/'host_outputs/aligned_numerical_v2'
OLD=pathlib.Path('C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1')
GIT='C:/hs/pr108-tools/git/cmd/git.exe'

def source_files():
    return [p for p in HERE.iterdir() if p.is_file() and (p.suffix in ('.py','.hpp','.cpp','.txt') or p.name in ('RULES.md','.gitattributes'))]

def overwrite_json(path,data,compact=False):
    with path.open('w',encoding='utf-8',newline='\n') as f:
        if compact:f.write(encode(data).decode('utf-8'))
        else:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')

def main():
    before=modules();need(not (HERE/'F0.json').exists(),'F0 already frozen; new preparation cannot overwrite it')
    need(not RUN.exists(),'new panel must remain unstarted')
    need(subprocess.check_output([GIT,'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==BASE,'fixed review base')
    need(not subprocess.check_output([GIT,'-C',str(ROOT),'diff','--name-only','HEAD'],text=True).strip(),'old tracked files changed')
    attempt=len(list((HERE/'preparation').glob('SOURCE_*.zip'))) if (HERE/'preparation').exists() else 0
    history=HERE/'preparation';history.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
    sourcezip=history/f'SOURCE_{attempt:02d}.zip'
    with zipfile.ZipFile(sourcezip,'x',zipfile.ZIP_DEFLATED) as z:
        for p in source_files():z.write(p,p.name)
    # Preserve every superseded unapproved binding/wire/metadata/reference object.
    previous=[p for p in HERE.iterdir() if p.is_file() and p.suffix=='.json']
    if previous:
        with zipfile.ZipFile(history/f'SUPERSEDED_{attempt:02d}.zip','x',zipfile.ZIP_DEFLATED) as z:
            for p in previous:z.write(p,p.name)
            for name in ('wires','references'):
                for p in (HERE/name).glob('*'):z.write(p,str(p.relative_to(HERE)))
    dep=OLD/'_host/pr97/dependencies';build=OUT/'build'
    commands=[['C:/Program Files/CMake/bin/cmake.exe','-S',str(HERE),'-B',str(build),'-G','Visual Studio 17 2022','-A','x64',
        '-DPINNED='+str(dep/'pinned-source'),'-DBASE_LIB='+str(dep/'pinned-build/ggml/src/Release/ggml-base.lib')],
        ['C:/Program Files/CMake/bin/cmake.exe','--build',str(build),'--config','Release']]
    logs=[]
    for command in commands:
        start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(dict(argv=command,returncode=r.returncode,elapsed_s=time.monotonic()-start,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:break
    success=all(x['returncode']==0 for x in logs)
    save(history/f'BUILD_{attempt:02d}.json',dict(success=success,logs=logs,source_archive_sha256=sha(sourcezip),GPU_host_launched=False))
    need(success,'offline build failure retained; do not run GPU host')
    runtime=build/'Release'
    for name in ('ggml-base.dll','ggml-vulkan.dll'):shutil.copy2(OLD/'_host/build/Release'/name,runtime/name)
    pinned=dep/'pinned-source';toolset=pathlib.Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64')
    build_inputs=list((pinned/'ggml/include').glob('*.h'))+list((pinned/'vendor/nlohmann').rglob('*.hpp'))
    build_inputs += [dep/'pinned-build/ggml/src/Release/ggml-base.lib',toolset/'cl.exe',toolset/'link.exe',pathlib.Path(commands[0][0])]
    frozen_source=pathlib.Path('C:/hs/b570-direct-id-v1-src');review=load(ROOT/'host/alignment_review_v1/FROZEN_SOURCE_REVIEW.json')
    backend=[]
    for record in review['sources']:
        p=frozen_source/record['path'];need(sha(p)==record['sha256'],'frozen numerical source identity drift')
        backend.append(dict(path=str(p),sha256=sha(p),role='read-only frozen numerical backend, not rebuilt'))
    overwrite_json(HERE/'BUILD_INPUTS.json',dict(files=[dict(path=str(p),sha256=sha(p),bytes=p.stat().st_size) for p in build_inputs],
        frozen_backend_sources=backend,backend_modified=False,backend_rebuilt=False,flags='/O2 /W4 /fp:precise',
        scope='Pinned GGML public headers, JSON header tree, import library and offline compiler/linker/CMake identities; executable and loaded DLL hashes are separately frozen'))
    prior=load(ROOT/'host/alignment_review_v1/DIAGNOSTIC_F0.json')
    for x in prior['dependencies']+prior['driver_files']:need(sha(x['path'])==x['sha256'],'frozen numerical DLL/driver drift')
    inputs=load(ROOT/'host/S1_INPUTS.json')
    for item in inputs:need(sha(item['path'])==item['sha256'],'original input changed')
    plan=build_plan(inputs);overwrite_json(HERE/'INPUTS.json',inputs);overwrite_json(HERE/'PLAN.json',plan)
    sources={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in source_files()}
    for name in ('native/query_head.h','host/common.py','host/run_s0.py','host/run_s1.py','host/inputs.py','core.py','plan.py','oracle.py','evidence.py'):
        sources[name]=sha(ROOT/name)
    runtime_files=[dict(path=str(runtime/name),sha256=sha(runtime/name)) for name in ('aligned-host-v2.exe','ggml-base.dll','ggml-vulkan.dll')]
    environment={k:v for k,v in sorted(__import__('os').environ.items()) if k.startswith(('GGML_','VK_','LLAMA_'))}
    need(environment==prior['environment'],'backend environment drift; report instead of silently adopting')
    binding=dict(run_id=RUN_ID,review_base=BASE,sources=sources,programs=runtime_files,driver_files=prior['driver_files'],
        environment=environment,plan_sha256=sha(HERE/'PLAN.json'),input_manifest_sha256=sha(HERE/'INPUTS.json'),limits=LIMITS,
        layout='Q0 for all modes; independent PQ q>1 mask slabs; original arithmetic/strides/inputs',
        primary='QH_C',required_alignment_bytes=64,alignment_basis='Observed previous diagnostic; current actual interface is unqueried and must be checked within charged hosts')
    overwrite_json(HERE/'EXECUTION_BINDING.json',binding);binding_sha=sha(HERE/'EXECUTION_BINDING.json')
    wires=HERE/'wires';wires.mkdir(exist_ok=True);manifest=[];paths=[]
    for slot in plan['slots']:
        path=wires/(slot['id']+'.wire');path.write_bytes(serialize(slot,inputs,binding_sha));paths.append(str(path))
        manifest.append(dict(slot_id=slot['id'],path='wires/'+path.name,sha256=sha(path),bytes=path.stat().st_size,
            command=[str(runtime/'aligned-host-v2.exe'),str(RUN/slot['id']/'REQUEST.wire'),str(RUN/slot['id']/'raw.jsonl')]))
    overwrite_json(HERE/'WIRES.json',manifest)
    wirelist=OUT/f'WIRE_LIST_{attempt:02d}.json';save(wirelist,paths)
    raw=OUT/f'CPU_NATIVE_{attempt:02d}.jsonl';command=[str(runtime/'aligned-metadata-v2.exe'),str(wirelist),str(raw)]
    start=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,timeout=120)
    save(history/f'CPU_NATIVE_PROCESS_{attempt:02d}.json',dict(argv=command,returncode=r.returncode,elapsed_s=time.monotonic()-start,
        stdout=r.stdout,stderr=r.stderr,CPU_executable_sha256=sha(runtime/'aligned-metadata-v2.exe'),GPU_host_launched=False,graph_computes=0))
    need(r.returncode==0,'actual native CPU wire parsing failed')
    rows=[json.loads(line) for line in raw.read_text().splitlines()];descriptors={}
    need(len(rows)==242 and rows[0]['event']=='CPU_START' and rows[-1]['event']=='CPU_CLOSE','all240 CPU graph descriptors')
    for row in rows[1:-1]:
        key=digest(row['cell'])+'/'+row['mode']
        if key in descriptors:need(descriptors[key]==row['graph'],'census and each execution graph must match')
        descriptors[key]=row['graph']
    need(len(descriptors)==80,'all80 repaired graphs')
    overwrite_json(HERE/'EXPECTED_GRAPHS.json',descriptors,True)
    cpuarchive=history/f'CPU_NATIVE_{attempt:02d}.zip'
    with zipfile.ZipFile(cpuarchive,'x',zipfile.ZIP_DEFLATED) as z:z.write(raw,raw.name)
    overwrite_json(HERE/'CPU_NATIVE_MANIFEST.json',dict(raw_path=str(raw),raw_sha256=sha(raw),archive_path=str(cpuarchive.relative_to(HERE)),
        archive_sha256=sha(cpuarchive),requests=161,metadata_graphs=240,graph_computes=0,device_queries=0))
    # Reuse the actual diagnostic's metadata as a source-shape check, not old
    # CPU success logs and never as new backend admission.
    with zipfile.ZipFile(ROOT/'host/alignment_review_v1/CPU_METADATA.zip') as z:
        older=[json.loads(line) for line in z.read('METADATA.jsonl').splitlines()]
    matches=0
    for row in older:
        if row.get('event')!='GRAPH_METADATA' or row['mode'] not in MODES:continue
        expected_policy=2 if row['mode']=='PQ' else 1
        if row['policy']!=expected_policy:continue
        current=descriptors[digest(row['cell'])+'/'+row['mode']]
        for a,b in zip(row['tensors'],current['tensors']):
            need(all(a[k]==b[k] for k in ('op','type','ne','nb','view_offset','op_parameters','bytes','view_root','src')),'unexpected arithmetic/storage drift from reviewed repair')
        need(len(row['tensors'])==len(current['tensors']),'same actual node inventory');matches+=1
    need(matches==80,'reviewed repair match complete')
    overwrite_json(HERE/'REPAIR_EQUIVALENCE.json',dict(graphs=matches,scope='Exact repaired metadata versus diagnostic CPU fixture; not new GPU support',
        Q0_and_PQ_slab_only=True,old_source_and_data_changed=False))
    refs=HERE/'references';refs.mkdir(exist_ok=True);refmanifest={}
    for item in inputs:
        reference=solve(pathlib.Path(item['path']).read_bytes());stages={}
        for stage in ('QK','softmax','AV','final'):
            file=refs/(item['id']+'-'+stage+'.f64');file.write_bytes(b''.join(struct.pack('<d',x) for x in reference[stage]))
            stages[stage]=dict(path=str(file.relative_to(HERE)),elements=len(reference[stage]),sha256=sha(file))
        refmanifest[item['id']]=dict(input_sha256=item['sha256'],stages=stages)
    overwrite_json(HERE/'REFERENCE_MANIFEST.json',dict(inputs=refmanifest,reference_source_sha256=sha(HERE/'reference.py'),
        scalar_FP64=True,scale_rounds_to_F32=True,source='Actual stored input bytes; no candidate mapping helpers',GPU_results=False))
    stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_panel.py')
    start=time.monotonic();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    save(history/f'CPU_TESTS_{attempt:02d}.json',dict(success=result.wasSuccessful(),methods=result.testsRun,elapsed_s=time.monotonic()-start,log=stream.getvalue(),
        metadata_programs_started=1,metadata_graphs=240,actual_GPU_launches=0,model_requests=0,graph_computes=0,
        source_archive_sha256=sha(sourcezip),modules_before=before,modules_after=modules()))
    need(result.wasSuccessful(),'fresh CPU tests failed; retained receipt')
    print(dict(success=True,CPU_methods=result.testsRun,formal_wires=161,CPU_descriptors=240,reviewed_graph_matches=matches,GPU_launches=0,preparation_attempt=attempt))

if __name__=='__main__':main()
