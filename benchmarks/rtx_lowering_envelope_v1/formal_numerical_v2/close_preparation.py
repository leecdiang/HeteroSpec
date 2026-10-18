"""Read-only artifact accounting and compact user delivery; no test or GPU run."""
import datetime,hashlib,json,shutil,subprocess
from pathlib import Path
from common import V,load,save,sha
OUT=Path('C:/Users/ASUS/Documents/Codex/2026-10-14/heterospec-pr-104-rtx-implementation-pq/outputs/PR113_FORMAL_NUMERICAL_V2')
def size(root):return sum(p.stat().st_size for p in root.rglob('*') if p.is_file())
def main():
    assert load(V/'FRESH_CPU_RESTORE.json')['status']=='PASS'
    f0=load(V/'F0.json');assert not Path(f0['execution_root']).exists() and not (V/'execution_ledger').exists()
    OUT.mkdir(exist_ok=False);copies=[]
    names=['RESULT.md','F0.json','F0_IDENTITY.json','PLAN.json','MATRIX.csv','BUDGET.json','SOURCE.diff','LINK_IDENTITY.json','SUPPORT_IMPACT.json',
        'CPU_NATIVE_TESTS.json','CPU_ANALYZER_TESTS_release.json','CPU_EXTRA_TESTS_release.json','CPU_LIFECYCLE_TESTS_release.json','CPU_CONTRACT_TESTS.json',
        'HISTORY_UNCHANGED.json','RAW_PREPARATION_MANIFEST.json','AUTHENTICATED_F0.json','AUTHENTICATED_PREPARATION.json','FRESH_CPU_RESTORE.json']
    for name in names:
        shutil.copyfile(V/name,OUT/name);assert sha(OUT/name)==sha(V/name);copies.append(dict(name=name,bytes=(V/name).stat().st_size,sha256=sha(V/name)))
    save(V/'DELIVERY.json',dict(destination=str(OUT),files=copies,archive_location=str(V/'RAW_PREPARATION.zip'),archive_not_duplicated=True))
    roots=[V,Path('D:/hs113-v2-preparation-authenticated-v1'),Path('D:/hs113-v2-preparation-fresh-v1'),OUT]
    measured=[dict(path=str(p),bytes=size(p)) for p in roots]
    objects=subprocess.check_output(['git','-C','D:/hs113','rev-list','--objects','d4df9f1abaec3b5de4e7331c8ca9820432bc0bcf..HEAD'])
    ids=b'\n'.join(line.split(b' ',1)[0] for line in objects.splitlines())+b'\n'
    stats=subprocess.check_output(['git','-C','D:/hs113','cat-file','--batch-check=%(objectsize)'],input=ids);git_bytes=sum(int(x) for x in stats.splitlines())
    bound=sum(x['bytes'] for x in measured)+2*git_bytes+8*1024**2
    assert bound<512*1024**2,(bound,measured,git_bytes)
    jobs=[load(p) for p in (V/'ledger').glob('*-EXIT.json')]
    charged=sum(x['charged_child_seconds_upper_bound']*(1 if x.get('accounts_console_helpers') else 2) for x in jobs)
    assert len(jobs)==100 and abs(charged-1793.0910068001976)<.001
    save(V/'CLOSURE_ACCOUNTING.json',dict(status='PASS',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),directories=measured,
        new_Git_objects_uncompressed_bytes=git_bytes,Git_storage_allowance_bytes=2*git_bytes,closure_metadata_reserve_bytes=8*1024**2,
        preparation_artifact_conservative_bound_bytes=bound,preparation_allowance_bytes=512*1024**2,
        completed_CPU_registered_jobs=len(jobs),CPU_corrected_conservative_child_seconds=charged,CPU_engineering_ceiling_seconds=1800,
        expected_native_negative_exits=60,unexpected_CPU_job_control_failures=2,pre_execution_text_quoting_failures=2,offline_compilations=4,
        delivery_hash_archive_transport_reconstruction_seconds=dict(seal=load(V/'PREPARATION_SEAL.json')['seconds'],readback_and_reconstruction=load(V/'FRESH_CPU_RESTORE.json')['delivery_seconds']),
        delivery_scope='Ordinary Git/hash/archive/transport and receipt reconstruction; no additional engineering/native/GPU executions. Logical artifact files, not whole-system caches or allocated NTFS clusters.',
        whitespace_check_note='Default Git whitespace check reports one frozen blank line with spaces in native_formal.cpp and its SOURCE.diff. Preserve the exact reviewed source/binary/F0 bytes; no functional source edit after freeze.',
        F0_sha256=sha(V/'F0.json'),new_GPU_queries=0,new_CUDA_loads=0,new_graph_computes=0,new_model_requests=0,formal_execution_root_absent=True,GPU_authorization='NOT_GRANTED'))
    for name in ('DELIVERY.json','CLOSURE_ACCOUNTING.json'):shutil.copyfile(V/name,OUT/name)
    print('PASS compact delivery and preparation artifact bound',bound,'<',512*1024**2,'; no new GPU/native execution')
if __name__=='__main__':main()
