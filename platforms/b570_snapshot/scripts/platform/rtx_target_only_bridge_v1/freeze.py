"""Freeze only after local qualification; receipt is written after the freeze commit."""
import subprocess
from common import *
def main():
    assert not (DOC/'FREEZE_RECEIPT.json').exists()
    subprocess.run([str(ASSET/'python311/python.exe'),str(pathlib.Path(__file__).with_name('verify.py')),'--namespace','engineering','--output',str(OUT/'engineering-verify')],check=True,cwd=ROOT)
    tests=subprocess.run([str(ASSET/'python311/python.exe'),str(pathlib.Path(__file__).with_name('test_verify.py'))],capture_output=True,text=True,cwd=ROOT);assert tests.returncode==0
    summary=load(OUT/'engineering-verify/SUMMARY.json');assert summary['status']=='PASS' and summary['runs']==12
    save(DOC/'QUALIFICATION.json',{**summary,'engineering_summary_sha256':sha(OUT/'engineering-verify/SUMMARY.json'),'negative_tests':tests.stderr,'utc':now(),'reuse':'byte-identical prior qualified numerical/capture frontend; no new interception; limited local4-task smoke'})
    sources=load(DOC/'SOURCE_BINDINGS.json')
    for name in ['scripts/platform/rtx_trajectory_cost_v4/native.py','scripts/platform/rtx_trajectory_cost_v4/native_runner.py','scripts/platform/rtx_target_verification_intervention_v1/execution.py','scripts/platform/rtx_target_verification_intervention_v1/native_observer.h','scripts/platform/rtx_target_verification_intervention_v1/build.py','scripts/platform/rtx_target_verification_intervention_v1/worker.cpp']:
        sources['files'][name]=sha(ROOT/name)
    save(DOC/'SOURCE_BINDINGS.json',sources)
    subprocess.run(['git','add','--sparse','--','scripts/platform/rtx_target_only_bridge_v1','benchmarks/rtx_target_only_bridge_v1'],check=True,cwd=ROOT)
    subprocess.run(['git','commit','-m','Freeze RTX target-only bridge protocol and qualified execution adapters'],check=True,cwd=ROOT)
    commit=git('rev-parse','HEAD')
    files={}
    for directory in [pathlib.Path(__file__).parent,DOC]:
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts and 'historical_raw' not in p.parts:files[p.relative_to(ROOT).as_posix()]=sha(p)
    save(DOC/'FREEZE_RECEIPT.json',{'commit':commit,'pinned_parent':PIN,'utc':now(),'formal_forwards_at_freeze':0,'files':files,'chronology_scope':'local commit/ledger; no independently trusted absolute experiment clock'})
    print(json.dumps({'status':'FROZEN','commit':commit,'files':len(files)}),flush=True)
if __name__=='__main__':main()
