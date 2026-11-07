from common95 import *
assert not (PUB/'ANCESTRY_RESTORE.json').exists()
cpu_differences=compare_parent_audit(read(LOCAL/'parent-cpu-independent/RTX_CROSSAUDIT.json'),read(LOCAL/'bindings/docs/experiments/rtx_postaudit_20261012/RTX_CROSSAUDIT.json'))
root=LOCAL/'parent-restored';parentpub=root/'repository/benchmarks/rtx_evidence_closeout_v1'
contract=read(parentpub/'MODEL_CONTRACT.json');build=read(parentpub/'NATIVE_BUILD.json');assets={}
for family,entry in contract['families'].items():
    pair={}
    for role in ['target','draft']:
        a=entry['models'][role];p=Path(a['path']);actual=sha(p);assert actual==a['sha256'];pair[role]=dict(path=str(p),sha256=actual,bytes=p.stat().st_size)
    assets[family]=pair
for name,h in build['numerical_DLL_sha256'].items():assert sha(Path('D:/HeteroSpec-PC/tools/llama-b10839')/name)==h
tree=api('git/trees/'+DESIGN_HEAD+'?recursive=1');assert not tree.get('truncated');items={x['path']:x for x in tree['tree']};receipt={}
for p in (LOCAL/'bindings').rglob('*'):
    if p.is_file():
        name=p.relative_to(LOCAL/'bindings').as_posix();b=p.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==items[name]['sha'];receipt[name]=dict(git_blob=items[name]['sha'],sha256=sha(p),bytes=len(b))
cas=LOCAL/'parent-remote/RAW_EVIDENCE.zip'
assert sha(cas)=='6cef4902fb2983024b4eb0c4b9a8a6c97ffed770d18495141f94144e11bc7232'
save(PUB/'ANCESTRY_RESTORE.json',dict(utc=now(),status='PASS',design_head=DESIGN_HEAD,audit_head=AUDIT_HEAD,parent_head=PARENT_HEAD,authenticated_fresh_parent_archive_sha256=sha(cas),archive_files_verified=21794,source_runtime_files_verified=6890,independent_crossaudit_exact_object_equal=not cpu_differences,crossaudit_scalar_differences=cpu_differences,crossaudit_ratio_tolerance=1e-12,all_native_arrays_and_nonfloating_fields_exact=True,bindings=receipt,models=assets,numerical_DLL_sha256=build['numerical_DLL_sha256'],new_forwards=0,CPU_preparation_failure_retained='work/querylayout-prepare.stderr.log'))
status('PARENT_RESTORED_AND_AUDITED',files=21794,source_runtime_files=6890,new_forwards=0)
