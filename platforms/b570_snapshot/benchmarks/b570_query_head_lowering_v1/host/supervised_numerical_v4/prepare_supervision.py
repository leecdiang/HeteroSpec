"""Offline identity-only native build and actual CPU fault tests, never GPU."""
import datetime
import difflib
import io
import pathlib
import shutil
import subprocess
import sys
import time
import unittest
import zipfile
from legacy import HERE,OLD,ROOT,OUT,RUN,RUN_ID,BASE,GIT,load,save,sha,modules,need

def source_files():return sorted([p for p in HERE.iterdir() if p.is_file() and p.suffix in ('.py','.txt','.cpp')]+list((HERE/'generated').glob('*')))

def main():
    need(not (HERE/'F0.json').exists() and not RUN.exists(),'no frozen F0/run may be overwritten')
    need(subprocess.check_output([GIT,'-C',str(ROOT),'rev-parse','HEAD'],text=True).strip()==BASE,'fixed reviewed base')
    need(not subprocess.check_output([GIT,'-C',str(ROOT),'diff','--name-only',BASE],text=True).strip(),'no old tracked mutation')
    history=HERE/'preparation';history.mkdir(exist_ok=True);attempt=len(list(history.glob('SOURCE_*.zip')))
    generated=HERE/'generated';generated.mkdir(exist_ok=True)
    old=(OLD/'fixture.hpp').read_bytes();literal=b'b570-aligned-numerical-v2-20261015-01';need(old.count(literal)==1,'one hardcoded interface identity')
    (generated/'host.cpp').write_bytes((OLD/'host.cpp').read_bytes());(generated/'fixture.hpp').write_bytes(old.replace(literal,RUN_ID.encode()))
    with zipfile.ZipFile(history/f'SOURCE_{attempt:02d}.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in source_files():z.write(p,str(p.relative_to(HERE)))
    OUT.mkdir(exist_ok=True);build=OUT/'build'
    deps=pathlib.Path('C:/hs/b570-geometry-p0/benchmarks/b570_geometry_state_codesign_v1/_host/pr97/dependencies')
    commands=[['C:/Program Files/CMake/bin/cmake.exe','-S',str(HERE),'-B',str(build),'-G','Visual Studio 17 2022','-A','x64','-DPINNED='+str(deps/'pinned-source'),'-DBASE_LIB='+str(deps/'pinned-build/ggml/src/Release/ggml-base.lib')],
        ['C:/Program Files/CMake/bin/cmake.exe','--build',str(build),'--config','Release']]
    logs=[]
    for command in commands:
        begin=time.monotonic();r=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace')
        logs.append(dict(command=command,wall_seconds=time.monotonic()-begin,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
        if r.returncode:break
    save(history/f'BUILD_{attempt:02d}.json',dict(logs=logs,native_host_launched=False));need(all(x['returncode']==0 for x in logs),'offline build failed')
    oldf0=load(OLD/'F0.json')
    for d in oldf0['dependencies']:
        need(sha(d['path'])==d['sha256'],'old numerical DLL drift');shutil.copy2(d['path'],build/'Release'/pathlib.Path(d['path']).name)
    save(history/f'NATIVE_EQUIVALENCE_{attempt:02d}.json',dict(host_cpp_exact=True,fixture_only_run_id_literal=True,
        old_host_cpp_sha256=sha(OLD/'host.cpp'),new_host_cpp_sha256=sha(generated/'host.cpp'),
        old_fixture_sha256=sha(OLD/'fixture.hpp'),new_fixture_sha256=sha(generated/'fixture.hpp'),
        unchanged_query_head_sha256=sha(ROOT/'native/query_head.h'),numerical_DLLs=oldf0['dependencies'],
        native_executable=dict(path=str(build/'Release/supervised-host-v4.exe'),sha256=sha(build/'Release/supervised-host-v4.exe')),native_launched=False))
    import test_supervision
    evidence=OUT/'CPU_TESTS'/f'attempt_{attempt:02d}';evidence.mkdir(parents=True,exist_ok=False);test_supervision.EVIDENCE=evidence
    stream=io.StringIO();suite=unittest.defaultTestLoader.loadTestsFromModule(test_supervision);begin=time.monotonic();before=modules()
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    process_receipts=[load(p) for p in evidence.rglob('LIFECYCLE.json')]
    metadata=[load(p) for p in evidence.glob('SERIALIZER/PROCESS.json')]
    save(history/f'CPU_TESTS_{attempt:02d}.json',dict(success=result.wasSuccessful(),methods=result.testsRun,wall_seconds=time.monotonic()-begin,log=stream.getvalue(),
        actual_CPU_children=sum(p['pid'] is not None for p in process_receipts),actual_CPU_control_workers=sum(len(p['control_processes']) for p in process_receipts),
        pre_spawn_rejections=sum(p['pid'] is None for p in process_receipts),
        additional_CPU_metadata_processes=len(metadata),metadata_processes=metadata,storage_watch_threads_per_supervised_child_max=2,
        source_hashes={str(p.relative_to(HERE)).replace('\\','/'):sha(p) for p in source_files()},
        evidence_root=str(evidence),native_GPU_hosts_started=0,device_queries=0,graph_computes=0,modules_before=before,modules_after=modules()))
    print(stream.getvalue());need(result.wasSuccessful(),'CPU fault tests failed, evidence retained; no GPU launch')

if __name__=='__main__':main()
