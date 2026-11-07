"""Delivery-only recovery; never executes a model or edits frozen study files."""
import base64, hashlib, json, shutil, subprocess, sys, time
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path('D:/HeteroSpec-RTX-Target-V1')
OUT=ROOT/'work/rtx-target-v1'
DOC=ROOT/'benchmarks/rtx_target_verification_intervention_v1'
ART=ROOT/'artifacts/rtx_target_verification_intervention_v1'
HERE=OUT/'delivery-recovery-01'
sys.path.insert(0,str(ROOT/'scripts/platform/rtx_target_verification_intervention_v1'))
from restore import restore
from execution import identity
from prepare import save, read, sha, utc
import integrity as g

state=read(OUT/'STATUS.json')
assert state['status']=='VERIFIED_COMPLETE' and state['completed']==645
assert identity(state['controller_pid']) is None and not (OUT/'LOCK.json').exists()
g.check_freeze()
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
index=read(ART/'ARCHIVE.json')
original_receipt=read(DOC/'DELIVERY_RECEIPT.json')
assert original_receipt['status']=='DELIVERY_PARTIAL' and 'CalledProcessError' in original_receipt['error']
for name in ['DELIVERY_RECEIPT.json','FINAL_LOCAL_SEAL.json']:
    p=DOC/name if name=='DELIVERY_RECEIPT.json' else OUT/name
    shutil.copy2(p,HERE/('previous-'+name))
shutil.copy2(DOC/'DELIVERY_RECEIPT.json',DOC/'DELIVERY_FAILURE_01.json')
partial=OUT/'remote-readback/raw-cas-v1.tar.gz'
partial_bytes=partial.stat().st_size
partial_sha=sha(partial)
tarpath=HERE/'remote-readback-complete.tar.gz'
received=[]
with partial.open('rb') as old,tarpath.open('xb') as dest:
    for number,part in enumerate(index['parts'],1):
        oid=subprocess.check_output(['git','rev-parse',head+':'+part['path']],cwd=ROOT,text=True).strip()
        if old.tell()+part['bytes']<=partial_bytes:
            data=old.read(part['bytes'])
            origin='retained first-attempt remote readback; bytes revalidated'
        else:
            origin='new GitHub API remote readback'
            for attempt in range(1,3):
                response=HERE/f'part-{number:02d}-attempt-{attempt}.response.json'
                err=HERE/f'part-{number:02d}-attempt-{attempt}.stderr.log'
                with response.open('xb') as so,err.open('xb') as se:
                    proc=subprocess.run(['gh','api',f'repos/leecdiang/HeteroSpec/git/blobs/{oid}'],stdout=so,stderr=se,timeout=600)
                if proc.returncode==0:break
                print(json.dumps({'part':number,'attempt':attempt,'transport_error':err.read_text(errors='replace')}),flush=True)
                if attempt==2:raise RuntimeError('bounded delivery retry failed')
                time.sleep(3)
            row=read(response);assert row['sha']==oid and row['encoding']=='base64'
            data=base64.b64decode(row['content'])
        assert len(data)==part['bytes'] and hashlib.sha256(data).hexdigest()==part['sha256']
        dest.write(data);dest.flush()
        received.append({'path':part['path'],'blob':oid,'sha256':part['sha256'],'bytes':len(data),'origin':origin})
        save(HERE/'PROGRESS.json',{'parts_verified':number,'planned_parts':len(index['parts']),'bytes_verified':dest.tell(),'utc':utc()})
        print(json.dumps({'parts_verified':number,'bytes_verified':dest.tell()}),flush=True)
assert sha(partial)==partial_sha and sha(tarpath)==index['sha256']
restored=HERE/'clean-restored'
restore(tarpath,restored)
with (HERE/'independent.stdout.log').open('wb') as so,(HERE/'independent.stderr.log').open('wb') as se:
    subprocess.run([sys.executable,str(restored/'scripts/platform/rtx_target_verification_intervention_v1/independent_verify.py'),'--root',str(restored),'--output',str(restored/'recompute')],stdout=so,stderr=se,check=True)
original=read(OUT/'independent-recompute/SUMMARY.json');again=read(restored/'recompute/SUMMARY.json')
fields=['planned','valid','invalid_units','unexecuted','failed_attempts','g0_arrays','sham_pairs','historical_comparisons','groups','known_cases','seal_mode','task_unit','graph_summary']
assert all(original[k]==again[k] for k in fields)
assert read(OUT/'independent-recompute/TASK_COMPARISONS.json')==read(restored/'recompute/TASK_COMPARISONS.json')
receipt={'status':'DELIVERY_COMPLETE','utc':utc(),'content_commit':head,'archive_sha256':index['sha256'],'readback':'all24 remote parts, clean restore, independent raw verification PASS','parts':received,'scientific_fields_equal':fields,'pr':'https://github.com/leecdiang/HeteroSpec/pull/53','recovery':{'previous_failure':'DELIVERY_FAILURE_01.json','cause':'GitHub HTTP502 at first readback part8','original_partial_bytes':partial_bytes,'original_partial_sha256':partial_sha,'original_partial_retained_unchanged':True,'helper_sha256':sha(Path(__file__)),'frozen_source_modified':False,'scientific_units_rerun':0}}
save(HERE/'VERIFIED_RECEIPT.json',receipt)
save(DOC/'DELIVERY_RECOVERY_01.json',receipt)
save(DOC/'DELIVERY_RECEIPT.json',receipt)
g.check_freeze()
g.event('DELIVERY_RECOVERY_PASS',content_commit=head,archive_sha256=index['sha256'],parts=24,scientific_units_rerun=0)
state.update(delivery='DELIVERY_COMPLETE',delivery_recovery_utc=utc(),heartbeat_utc=utc())
save(OUT/'STATUS.json',state)
shutil.copy2(Path(__file__),ART/'delivery_recovery_01.py')
print(json.dumps({'status':'DELIVERY_COMPLETE','verified_parts':24,'scientific_units_rerun':0}),flush=True)
