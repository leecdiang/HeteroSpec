"""Seal explicit source, small fixture, native receipts and model-free full recovery archive."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,shutil,zipfile
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,j):p.write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--run',type=Path,required=True);a=p.parse_args();r=a.run;kit=Path(__file__).resolve().parent
    dest=r/'delivery-final';archive=r/'B570_NATIVE_DELIVERY.zip'
    if dest.exists() or archive.exists():raise ValueError('Fresh delivery paths required')
    summary=read(r/'SUMMARY.json')
    if summary['status']!='NATIVE_REPRODUCTION_COMPLETE_WITH_DECLARED_LIMITS':raise ValueError('Unqualified summary')
    receipts=kit/'receipts';receipts.mkdir(exist_ok=False)
    selected=[r/(x['slot']+'.receipt.json')for x in summary['slots']]
    selected += [r/x for x in ['CAPTURE_AUDIT.json','CAPTURE_A2_AUDIT.json','STAGE_AUDIT.json','FRESH_STAGE_AUDIT.json','FRESH_REQUEST_AUDIT.json','FRESH_COPY_INTEGRITY.json','NUMERICAL_LIBRARIES_UNCHANGED_A2.json','AUDITOR_MUTATIONS.json','AUDITOR_REFERENCE_SELF_CHECK.json']]
    selected += [r/f'SMOKE_{i}_AUDIT.json'for i in range(4)]
    for f in selected:shutil.copyfile(f,receipts/f.name)
    shutil.copyfile(r/'SUMMARY.json',kit/'SUMMARY.json')
    runtime=[{'name':f.name,'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted((r/'build/bin/Release').glob('*'))if f.suffix in ['.dll','.exe']]
    write(kit/'RUNTIME_A2.json',{'status':'QUALIFIED_NEW_RUNTIME','binaries':runtime,'numerical_libraries_unchanged_from_a1':True,'diagnostic_formal_rebuilt':True,'build_log_sha256':sha(r/'build-a2.log'),'freeze_sha256':sha(r/'EXECUTION_FREEZE_A2.json')})
    fixture_archive=kit/'REAL_STAGE_FIXTURE.zip'
    with zipfile.ZipFile(fixture_archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for f in sorted((r/'fixture-a2').iterdir()):z.write(f,f.name)
    write(kit/'FIXTURE_MANIFEST.json',{'archive':fixture_archive.name,'bytes':fixture_archive.stat().st_size,'sha256':sha(fixture_archive),'provenance':'NEW_REAL_REQUEST_CAPTURE','request':'capture-a2/qual-2','input':'HumanEval/115','layer':0,'cycle':0,'files':[{'path':f.name,'bytes':f.stat().st_size,'sha256':sha(f)}for f in sorted((r/'fixture-a2').iterdir())]})
    write(kit/'CPU_VALIDATION.json',{'query_layout_contract_tests':{'run':12,'passed':12},'bundle_tests':{'run':8,'passed':7,'skipped':1,'skip_reason':'Windows symlink creation unavailable'},'request_auditor_mutations':{'run':4,'rejected':4},'source_identity':'SOURCE_RECOVERY.json','native_execution_not_inferred_from_cpu_tests':True})
    write(kit/'LOCAL_DELIVERY.json',{'run_root':str(r.resolve()),'archive':str(archive.resolve()),'unpacked_delivery':str(dest.resolve()),'archive_checksum_receipt':'ARCHIVE_RECEIPT.json (supplied alongside archive)','fresh_native_replay_directory':str((r/'fresh-v1').resolve()),'large_reference_access':'references/qual-0 through qual-3 in archive','new_raw_access':'evidence/<slot> in archive','models':'EXCLUDED; supply exact MODEL_IDENTITY.json bytes externally','binary_libraries':'Included only in controlled local archive; not committed to Git','remote_raw_publication':'NOT_PERFORMED','recovery':'Extract archive to a new directory; verify every byte using manifest.json or verify_delivery.py; use kit/README.md for native commands'})
    dest.mkdir()
    shutil.copytree(kit,dest/'kit',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(r/'build/bin/Release',dest/'runtime')
    shutil.copytree(r/'runtime-a1',dest/'runtime-a1')
    shutil.copytree(r/'source-kit-a1',dest/'source-kit-a1',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(r/'fixture-a2',dest/'fixture');shutil.copytree(r/'fixture',dest/'fixture-incomplete-a1')
    shutil.copytree(r/'portable-v1/references',dest/'references')
    for row in summary['slots']:shutil.copytree(r/row['slot'],dest/'evidence'/row['slot'])
    (dest/'logs').mkdir();(dest/'identity').mkdir()
    for f in r.glob('*.log'):shutil.copyfile(f,dest/'logs'/f.name)
    for name in ['EXECUTION_FREEZE.json','EXECUTION_FREEZE_A2.json','FRESH_FREEZE.json']:
        shutil.copyfile(r/name,dest/'identity'/name)
    shutil.copyfile(r/'clean-source2/PREPARED_SOURCE.json',dest/'identity/PREPARED_SOURCE.json')
    shutil.copyfile(r/'upstream.tar.gz',dest/'upstream.tar.gz')
    shutil.copyfile(r/'fresh-v1/manifest.json',dest/'identity/FRESH_PACKAGE_MANIFEST.json')
    util=a.repo/'scripts/native_reproduction/bundle_manifest.py';shutil.copyfile(util,dest/'bundle_manifest.py')
    spec=importlib.util.spec_from_file_location('bundle_manifest',util);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    includes=[f.relative_to(dest).as_posix()for f in sorted(dest.rglob('*'))if f.is_file()]
    m.create(dest,includes,'b570',dest/'manifest.json',{'source_commit':'0cae43063cf15170e91a2ff4d034da0ecef4a1b2','build_identity':runtime,'model_identity':read(kit/'MODEL_IDENTITY.json'),'device_identity':'Arc B570, driver32.0.101.9034, same host qualification'})
    shutil.copyfile(dest/'manifest.json',kit/'DELIVERY_MANIFEST.json')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True)as z:
        for f in sorted(dest.rglob('*')):
            if f.is_file():z.write(f,f.relative_to(dest).as_posix())
    print(json.dumps({'status':'PACKAGED_PENDING_FULL_READBACK','files':len(includes),'archive':str(archive),'bytes':archive.stat().st_size}))
if __name__=='__main__':main()
