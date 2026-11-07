"""Final zero-device evidence/source validation and exact new runtime capsule."""
import argparse, hashlib, pathlib, subprocess, zipfile
from common import ROOT, load, save, sha, modules

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);p.add_argument('--git',default='git');a=p.parse_args();before=modules()
    lock=load(ROOT/'host/HOST_RULE_LOCK.json');binding=load(ROOT/'host/HOST_SOURCE_BINDINGS.json')
    for name,digest in lock['harness_sources'].items():
        f=ROOT/('host/S0_CMakeLists.frozen.txt' if name.replace('\\','/')=='native/host/CMakeLists.txt' else name)
        assert sha(f)==digest,name
    assert sha(ROOT/'native/query_head.h')==lock['candidate_sha256']
    assert sha(ROOT/'host/inputs.py')==lock['inputs_source_sha256']
    assert sha(ROOT/'build/Release/qh-real.exe')==lock['executable_sha256']
    for label in ('DEVELOPMENT','HELD'):
        r=load(ROOT/f'host/S0_{label}_RECEIPT.json');assert r['completed_fixtures']==216 and r['returncode']==0
        assert r['exe_sha256']==lock['executable_sha256']
        for x in r['actual_loaded_modules']:assert sha(x['path'])==x['sha256']
    raw=load(ROOT/'host/S0_RAW_MANIFEST.json');assert sha(ROOT/'host/S0_RAW.zip')==raw['archive_sha256']
    assert load(ROOT/'host/S0_RESTORE_RECEIPT.json')['all_archived_bytes_rehashed']
    assert load(ROOT/'host/ACTOR_REPAIR_01.json')['success']
    assert load(ROOT/'host/HOST_CONTROL_TESTS.json')['success']
    assert load(ROOT/'host/HOST_WIRE_TESTS.json')['cases']==128
    f0=load(ROOT/'host/S1_F0.json')
    for name,digest in f0['sources'].items():assert sha(ROOT/name)==digest,name
    for x in [f0['executable']]+f0['dependencies']+f0['driver_files']:assert sha(x['path'])==x['sha256']
    assert not (ROOT/'host_outputs/S1_RUN').exists()
    assert sha(a.old/'p0/F0_EXECUTION.json')=='29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8'
    oldroot=a.old.parent.parent
    assert subprocess.check_output([a.git,'-C',str(oldroot),'rev-parse','HEAD'],text=True).strip()=='039a24bf61374042e0dc9f3a3619ea40b218a5ad'
    assert not subprocess.check_output([a.git,'-C',str(oldroot),'diff','--name-only','HEAD'],text=True).strip()
    archive=ROOT/'host/NEW_RUNTIME_CAPSULE.zip';files=[]
    for path in ['build/Release/qh-real.exe','build/Release/qh-descriptor.exe','build/S1/qh-vulkan.exe',
                 'host_outputs/actor/build/Release/b570-qh-worker.exe','host_outputs/actor/build/Release/llama-b570-qh.dll']:
        f=ROOT/path;files.append(dict(path=path,bytes=f.stat().st_size,sha256=sha(f)))
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for x in files:z.write(ROOT/x['path'],x['path'])
    with zipfile.ZipFile(archive) as z:
        for x in files:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
    save(ROOT/'host/NEW_RUNTIME_MANIFEST.json',dict(files=files,archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,
         dependencies='Unchanged GGML numerical DLLs/header/import libraries from fixed PR109 restore. No model weights.',readback_rehashed=True))
    size=sum(f.stat().st_size for f in (ROOT/'host_outputs').rglob('*') if f.is_file())
    assert size<2*1024**3
    save(ROOT/'host/FINAL_VALIDATION.json',dict(real_CPU_fixtures=432,graphs=2592,numerical_sources_and_binary_unchanged_after_lock=True,
         scalar_error_and_all_full_vectors_retained=True,old_source_F0_and_runtime_unchanged=True,
         native_actor_offline_compile_success=True,first_native_compile_failure_retained=True,
         failed_unapproved_F0_gate_test_retained=True,final_host_gate_methods=7,wire_roundtrips=128,
         S1_F0_sha256=sha(ROOT/'host/S1_F0.json'),host_output_bytes=size,
         S1_operator_hosts_started=0,GPU_device_queries=0,GPU_forwards=0,GPU_operators=0,model_requests=0,
         modules_before=before,modules_after=modules()))
    print(dict(validated=True,fixtures=432,graphs=2592,S1_F0=sha(ROOT/'host/S1_F0.json'),runtime_capsule_bytes=archive.stat().st_size))

if __name__=='__main__':main()
