"""Actual GPU qualification of the independently rebuilt portable candidates."""
from qualify_rtx import *
CLEAN=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase192-clean-v1')

def main():
    assert read(CLEAN/'COMPLETE.json')['status']=='BOTH_NATIVE_CORES_AND_WORKERS_BUILT';proofs=[]
    for family in ('Qwen','Smol'):
        cc=cases(family);reserve=dict(requests=len(cc),token_rows=sum(sum(len(x['ids']) for x in c['forced']) for c in cc),operators=0)
        reference=ROOT/'runs'/f'{family}-v2-matrix-R'
        for arm,(recipe,lowering) in ARMS.items():
            label=f'clean-v1-{family}-{arm}';out=ROOT/'runs'/label;source=CLEAN/('runtime-'+recipe)
            if not out.exists():prior.execute(label,str(source),family,dict(lowering=lowering,cases=cc),reserve)
            else:assert (out/'COMPLETE.json').exists()
            assert read(out/'binding.json')['exe']==sha(source/'bin/worker.exe')
            q.compare_cases(reference,out,cc,family,label+'-QUALIFICATION');dedup()
            p=ROOT/(label+'-QUALIFICATION.json');proofs.append(dict(path=str(p),sha256=sha(p),family=family,arm=arm,build_manifest_sha256=sha(source/'BUILD.json')))
    put(ROOT/'CLEAN_BUILD_PROOF.json',dict(fresh_directory=str(CLEAN),build_complete=read(CLEAN/'COMPLETE.json'),source_manifest_sha256=sha(CLEAN/'SOURCE_MANIFEST.json'),native_GPU_qualifications=proofs,all_passed=True,scope='Fresh source-only directory rebuild of both native cores/frontends using existing pinned numerical DLL dependencies. All four combinations checked on both families at the6 fixed geometry cells; last-only vectors and complete committed active KV. This is same-host finite qualification, not external replication or a full D4 service rerun.',model_weights_or_historical_KV_needed_to_build=False,formal_performance_slots_replaced=0))
    print('Fresh portable native builds independently GPU-qualified for all four combinations/both families',flush=True)

if __name__=='__main__':main()
