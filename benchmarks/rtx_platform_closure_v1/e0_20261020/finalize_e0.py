"""Complete scoped ledger bindings and validate/package the E0 stop evidence."""
from pathlib import Path
import collections, csv, hashlib, json, shutil, subprocess, zipfile

HERE=Path(__file__).resolve().parent
REPO=HERE/'HeteroSpec-rtx-closure'
OUT=REPO/'benchmarks/rtx_platform_closure_v1/e0_20261020'
OUTPUTS=HERE.parent/'outputs'
BASE='ec6b97518a2f230330d79f1b0ba2ca97bc70cd6a'

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def pin(p):
    p=Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')

def main():
    reconciliation=read(OUT/'RTX_LEDGER_RECONCILIATION.json')
    bindings=[]
    reconciliation['later_RTX_scopes']=[x for x in reconciliation['later_RTX_scopes'] if x['pr'] not in (120,121)]
    for pr,dirname,rootname in (
        (120,'rtx_reference_envelope_v2','hs120-8a6bde3c-bc24-4f16-9e1e-9950965386d3'),
        (121,'rtx_boundary_confirmation_v1','hs121-0cd72634-266d-4b57-9b00-1d7df2327735'),
        (122,'rtx_mechanism_baselines_v1','hs122-5e483f69-dac1-41a4-a046-14401910e6e5'),
        (123,'rtx_dispatch_intervention_v1','hs123-57d3eed0-c107-4358-bc4a-ac1008a06e28')):
        src=Path(f'D:/hs{pr}/benchmarks')/dirname
        root=Path('D:/')/rootname
        rel=f'benchmarks/{dirname}/'+('execution/' if pr==123 else '')+'RESOURCE_SUMMARY.json'
        committed=subprocess.check_output(['git','show',f'{BASE}:{rel}'],cwd=REPO)
        local=src/('execution/' if pr==123 else '')/'RESOURCE_SUMMARY.json'
        if not local.exists():local=root/'RESOURCE_SUMMARY.json'
        local_bytes=local.read_bytes()
        assert local_bytes.replace(b'\r\n',b'\n')==committed.replace(b'\r\n',b'\n'),('resource summary differs beyond line endings',pr,str(local))
        target=OUT/f'ledgers/PR{pr}/RESOURCE_SUMMARY.json'
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(committed)
        bindings.append(dict(pr=pr,main_ref=BASE,main_path=rel,local=pin(local),
            main_bytes=len(committed),main_sha256=hashlib.sha256(committed).hexdigest(),
            byte_equal_to_main=local_bytes==committed,line_ending_normalized_equal=True,
            difference='NONE' if local_bytes==committed else 'CRLF_vs_LF_ONLY; original local hash retained'))
        if pr in (120,121):
            docs={}
            for name in ('RUN_SPEC.json','EXECUTION_POLICY.json','GPU_EXECUTION_CLOSED.json','ATTEMPTS.jsonl'):
                p=root/name
                if p.exists():
                    shutil.copyfile(p,OUT/f'ledgers/PR{pr}'/name)
                    docs[name]=pin(p)
            receipts=[pin(p) for p in sorted(root.glob('*_ENDED.json'))]
            if (root/'attempts').is_dir():
                receipts.extend(pin(p) for p in sorted((root/'attempts').rglob('*LIFETIME.json')))
                receipts.extend(pin(p) for p in sorted((root/'attempts').rglob('*JOB_EVENTS.json')))
            save(OUT/f'ledgers/PR{pr}/PROCESS_RECEIPT_HASHES.json',receipts)
            reconciliation['later_RTX_scopes'].append(dict(pr=pr,root=str(root),documents=docs,
                 process_receipt_index=f'ledgers/PR{pr}/PROCESS_RECEIPT_HASHES.json',resource_summary=read(target)))
    reconciliation['later_RTX_scopes'].sort(key=lambda x:x['pr'])
    assert [x['pr'] for x in reconciliation['later_RTX_scopes']]==[120,121,122,123]
    reconciliation['main_resource_summary_bindings']=bindings
    reconciliation['supplement']='PR120/121 summaries live in committed result folders rather than raw roots; finalize_e0.py completes and authenticates these bindings without re-running model work.'
    save(OUT/'RTX_LEDGER_RECONCILIATION.json',reconciliation)
    for name in ('HOST_CURRENT.csv','MODEL_PROCESS_SNAPSHOT.json','e0_audit.stdout.log','e0_audit.stderr.log'):
        shutil.copyfile(HERE/name,OUT/name)
    shutil.copyfile(__file__,OUT/'finalize_e0.py')

    checks={}
    identity=read(OUT/'RUNTIME_MODEL_DLL_AUDIT.json')
    checks['runtime_model_dll_26_of_26']=len(identity['checks'])==26 and all(x['status']=='KNOWN' for x in identity['checks'])
    historical=read(OUT/'HISTORICAL_RESTORATION.json')
    checks['all_19922_restoration_members_match']=sum(x['members'] for x in historical['restoration'])==19922 and all(set(x['status_counts'])=={'KNOWN'} for x in historical['restoration'])
    checks['all_5_original_archives_match']=len(historical['archives'])==5 and all(x['status']=='KNOWN' for x in historical['archives'])
    ledger=reconciliation['PR104']
    checks['PR104_ledger_matches_final_counts']=ledger['kind_counts']==dict(load=324,warmup=324,request=1296) and not ledger['duplicate_slots'] and ledger['process_receipts']==324 and abs(ledger['owned_seconds']-4968.994058199897)<1e-8
    checks['later_RTX_summaries_bound_to_main']=all(x['line_ending_normalized_equal'] for x in bindings)
    coverage=read(OUT/'REFERENCE_COVERAGE.json')['coverage']
    checks['reference_missing_not_relabelled']=all(x['full_vocab_logits_events']==0 and not x['f32_files'] for x in coverage)
    checks['PR104_E2_retained_request_count']=next(x for x in coverage if x['part']=='E2')['records']==1620
    with (OUT/'ALL_SLOTS.csv').open(encoding='utf-8',newline='') as f:slots=list(csv.DictReader(f))
    counts=collections.Counter((s['gate'],s['kind']) for s in slots)
    checks['all_164_unstarted_positions_visible']=len(slots)==164 and counts[('E1','qualification')]==12 and counts[('E2','warmup')]==64 and counts[('E2','measured')]==64 and sum(s['gate']=='E3' for s in slots)==24 and all('UNSTARTED' in s['status'] or 'NOT_STARTED' in s['status'] for s in slots)
    receipts=read(OUT/'PROCESS_RECEIPTS.json')
    checks['no_native_process_or_false_freeze']=receipts['native_process_starts']==0 and not read(OUT/'PREREGISTRATION_NOT_FROZEN.json')['native_execution_allowed'] and not (OUT/'PREREGISTRATION.json').exists()
    checks['scientific_questions_remain_unresolved']=read(OUT/'E0_DISPOSITION.json')['scientific_screen']=='NOT_EVALUATED'
    save(OUT/'VALIDATION.json',dict(status='PASS' if all(checks.values()) else 'FAIL',checks=checks,
                                  scope='Offline archival and disposition validation only; no model qualification or performance test'))
    assert all(checks.values()),checks
    design=[p for p in (OUT/'protocol136').iterdir() if p.is_file()]+[OUT/'audit_e0.py',OUT/'finalize_e0.py',OUT/'PROTOCOL_REVIEW.md']
    save(OUT/'DESIGN_SHA256.json',dict(status='REVIEWED_DESIGN_AND_E0_AUDIT_NOT_EXECUTION_FREEZE',files=[dict(path=str(p.relative_to(OUT)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(design)]))
    save(OUT/'EVIDENCE_SHA256.json',dict(files=[dict(path=str(p.relative_to(OUT)).replace('\\','/'),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='EVIDENCE_SHA256.json'],scope='All result files except this manifest; no native experiment data generated'))
    OUTPUTS.mkdir(exist_ok=True)
    archive=OUTPUTS/'HeteroSpec_RTX_E0_完整审计记录.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(OUT.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(OUT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('EVIDENCE_SHA256.json'))
        for row in manifest['files']:
            data=z.read(row['path']);assert len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256']
    shutil.copyfile(OUT/'RESULT.md',OUTPUTS/'HeteroSpec_RTX_E0_审阅结论.md')
    save(OUTPUTS/'HeteroSpec_RTX_E0_归档校验.json',dict(archive=pin(archive),members=sum(p.is_file() for p in OUT.rglob('*')),
         archive_reopened_and_all_manifest_members_verified=True,validation=read(OUT/'VALIDATION.json'),
         study_uuid=read(OUT/'AUDIT_IDENTITY.json')['study_uuid']))
    print(json.dumps(dict(checks=checks,archive=pin(archive)),ensure_ascii=False))

if __name__=='__main__':main()
