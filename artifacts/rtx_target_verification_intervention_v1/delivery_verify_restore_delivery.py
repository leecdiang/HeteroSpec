"""Resume verified remote bytes into a short empty root; no model execution."""
import base64, hashlib, json, shutil, subprocess, sys
from pathlib import Path
ROOT=Path('D:/HeteroSpec-RTX-Target-V1');OUT=ROOT/'work/rtx-target-v1';DOC=ROOT/'benchmarks/rtx_target_verification_intervention_v1';ART=ROOT/'artifacts/rtx_target_verification_intervention_v1';HERE=OUT/'delivery-recovery-01'
sys.path.insert(0,str(ROOT/'scripts/platform/rtx_target_verification_intervention_v1'))
from restore import restore
from prepare import read,save,sha,utc
from execution import identity
import integrity as g
assert identity(28348) is None and identity(read(OUT/'STATUS.json')['controller_pid']) is None
g.check_freeze()
index=read(ART/'ARCHIVE.json');tarpath=HERE/'remote-readback-complete.tar.gz';partial=OUT/'remote-readback/raw-cas-v1.tar.gz'
assert sha(tarpath)==index['sha256'] and read(HERE/'PROGRESS.json')['parts_verified']==24
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();received=[]
with tarpath.open('rb') as f:
    for number,part in enumerate(index['parts'],1):
        data=f.read(part['bytes']);assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']
        oid=subprocess.check_output(['git','rev-parse',head+':'+part['path']],cwd=ROOT,text=True).strip()
        if number<=7:origin='retained first-attempt remote readback; byte hashes revalidated'
        else:
            paths=sorted(HERE.glob(f'part-{number:02d}-attempt-*.response.json'))
            response=None
            for response_path in reversed(paths):
                try:
                    candidate=read(response_path)
                    if candidate.get('sha')==oid and hashlib.sha256(base64.b64decode(candidate['content'])).hexdigest()==part['sha256']:
                        response=candidate;break
                except (json.JSONDecodeError,KeyError,ValueError):
                    continue
            assert response is not None;origin='successful GitHub API response retained and revalidated; failed attempts preserved'
        received.append({'path':part['path'],'blob':oid,'sha256':part['sha256'],'bytes':len(data),'origin':origin})
    assert not f.read(1)
save(DOC/'DELIVERY_RESTORE_FAILURE_01.json',{'utc':utc(),'cause':'Windows MAX_PATH exceeded in a deeply nested pinned upstream UI filename','partial_restore_retained':'work/rtx-target-v1/delivery-recovery-01/clean-restored','stderr_sha256':sha(HERE/'stderr.log'),'remote_archive_bytes_verified':True,'scientific_units_rerun':0})
dest=OUT/'remote01';assert not dest.exists()
manifest=read(ART/'MANIFEST.json');assert max(len(str(dest/name)) for name in manifest['files'])<260
restore(tarpath,dest)
with (HERE/'resumed-independent.stdout.log').open('wb') as so,(HERE/'resumed-independent.stderr.log').open('wb') as se:
    subprocess.run([sys.executable,str(dest/'scripts/platform/rtx_target_verification_intervention_v1/independent_verify.py'),'--root',str(dest),'--output',str(dest/'recompute')],stdout=so,stderr=se,check=True)
original=read(OUT/'independent-recompute/SUMMARY.json');again=read(dest/'recompute/SUMMARY.json')
fields=['planned','valid','invalid_units','unexecuted','failed_attempts','g0_arrays','sham_pairs','historical_comparisons','groups','known_cases','seal_mode','task_unit','graph_summary']
assert all(original[k]==again[k] for k in fields)
assert read(OUT/'independent-recompute/TASK_COMPARISONS.json')==read(dest/'recompute/TASK_COMPARISONS.json')
receipt={'status':'DELIVERY_COMPLETE','utc':utc(),'content_commit':head,'archive_sha256':index['sha256'],'readback':'all24 remote parts, clean short-root restore, independent raw verification PASS','parts':received,'scientific_fields_equal':fields,'pr':'https://github.com/leecdiang/HeteroSpec/pull/53','recovery':{'previous_failure':'DELIVERY_FAILURE_01.json','restore_failure':'DELIVERY_RESTORE_FAILURE_01.json','cause':'HTTP502 followed by Windows receiver path-length limit','original_partial_bytes':partial.stat().st_size,'original_partial_sha256':sha(partial),'original_partial_retained_unchanged':True,'helper_sha256':sha(HERE/'recover_transport.py'),'restore_resume_helper_sha256':sha(Path(__file__)),'frozen_source_modified':False,'scientific_units_rerun':0}}
save(HERE/'VERIFIED_RECEIPT.json',receipt);save(DOC/'DELIVERY_RECOVERY_01.json',receipt);save(DOC/'DELIVERY_RECEIPT.json',receipt)
g.check_freeze();g.event('DELIVERY_RECOVERY_PASS',content_commit=head,archive_sha256=index['sha256'],parts=24,scientific_units_rerun=0)
state=read(OUT/'STATUS.json');state.update(delivery='DELIVERY_COMPLETE',delivery_recovery_utc=utc(),heartbeat_utc=utc());save(OUT/'STATUS.json',state)
for p in [HERE/'recover_transport.py',Path(__file__)]:shutil.copy2(p,ART/('delivery_'+p.name))
print(json.dumps({'status':'DELIVERY_COMPLETE','verified_parts':24,'scientific_units_rerun':0}),flush=True)
