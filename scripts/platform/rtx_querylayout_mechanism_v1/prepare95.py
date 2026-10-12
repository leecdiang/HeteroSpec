from common95 import *
import importlib.util,shutil
LOCAL.mkdir(exist_ok=True);PUB.mkdir(parents=True,exist_ok=True)
status('PARENT_AUTHENTICATED_RESTORE',new_forwards=0)
assert git('rev-parse','HEAD')==DESIGN_HEAD
tree=api('git/trees/'+DESIGN_HEAD+'?recursive=1');assert not tree.get('truncated');items={x['path']:x for x in tree['tree']}
bindings=['docs/experiments/rtx_querylayout_closeout_20261012/EXECUTION_PROMPT.md','docs/experiments/rtx_querylayout_closeout_20261012/PROTOCOL.md','docs/experiments/rtx_querylayout_closeout_20261012/README.md','benchmarks/rtx_consistency_contract_v1/query_batch_patch.py','benchmarks/rtx_consistency_phase2/scope_patch.py','paper/jsa/manuscript_v0145/sections/05_repair.tex','docs/experiments/rtx_postaudit_20261012/README.md','docs/experiments/rtx_postaudit_20261012/PAPER_ASSESSMENT.md','docs/experiments/rtx_postaudit_20261012/RTX_CROSSAUDIT.json','scripts/audit/rtx_pr91_crossaudit.py','scripts/audit/test_rtx_pr91_crossaudit.py']
receipt={}
for name in bindings:
    b=verified_blob(items[name]['sha']);p=LOCAL/'bindings'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    if (REPO/name).exists():assert (REPO/name).read_bytes()==b
    receipt[name]=dict(git_blob=items[name]['sha'],sha256=sha(p),bytes=len(b))
spec=importlib.util.spec_from_file_location('parent_independent',REPO/'scripts/audit/rtx_pr91_crossaudit.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
cache={};partroot=LOCAL/'parent-remote';partroot.mkdir()
for i,(oid,size,h) in enumerate(audit.PARTS):
    b=verified_blob(oid);assert len(b)==size and hashlib.sha256(b).hexdigest()==h
    p=partroot/f'part{i+1:03d}';p.write_bytes(b);cache['git/blobs/'+oid]=b
cas=partroot/'RAW_EVIDENCE.zip'
with cas.open('xb') as f:
    for i in range(len(audit.PARTS)):f.write((partroot/f'part{i+1:03d}').read_bytes())
assert sha(cas)==audit.CAS_SHA
root=LOCAL/'parent-restored';root.mkdir()
with zipfile.ZipFile(cas) as z:
    index=json.loads(z.read('INDEX.json'))['files']
    for n,a in index.items():
        p=(root/n).resolve();assert p.is_relative_to(root.resolve());b=z.read(n)
        assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
parentpub=root/'repository/benchmarks/rtx_evidence_closeout_v1'
native=LOCAL/'native';native.mkdir()
with zipfile.ZipFile(parentpub/'SOURCE_RUNTIME.zip') as z:
    idx=json.loads(z.read('INDEX.json'))['files']
    for n,a in idx.items():
        b=z.read(n);assert len(b)==a['bytes'] and hashlib.sha256(b).hexdigest()==a['sha256']
        if n.startswith('native/source/'):
            p=LOCAL/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    native_count=len(idx)
def get(path,raw=False):
    if raw and path in cache:return cache[path]
    return api(path,raw=True)
audit.get=get;sys.argv=['parent_independent','--output',str(LOCAL/'parent-cpu-independent')];audit.main()
cpu_differences=compare_parent_audit(read(LOCAL/'parent-cpu-independent/RTX_CROSSAUDIT.json'),read(LOCAL/'bindings/docs/experiments/rtx_postaudit_20261012/RTX_CROSSAUDIT.json'))
contract=read(parentpub/'MODEL_CONTRACT.json');build=read(parentpub/'NATIVE_BUILD.json');assets={}
for family,entry in contract['families'].items():
    pair={}
    for role in ['target','draft']:
        a=entry['models'][role];p=Path(a['path']);actual=sha(p);assert actual==a['sha256'];pair[role]=dict(path=str(p),sha256=actual,bytes=p.stat().st_size)
    assets[family]=pair
for name,h in build['numerical_DLL_sha256'].items():assert sha(Path('D:/HeteroSpec-PC/tools/llama-b10839')/name)==h
save(PUB/'ANCESTRY_RESTORE.json',dict(utc=now(),status='PASS',design_head=DESIGN_HEAD,audit_head=AUDIT_HEAD,parent_head=PARENT_HEAD,authenticated_fresh_parent_archive_sha256=sha(cas),archive_files_verified=len(index),source_runtime_files_verified=native_count,independent_crossaudit_exact_object_equal=not cpu_differences,crossaudit_scalar_differences=cpu_differences,crossaudit_ratio_tolerance=1e-12,all_native_arrays_and_nonfloating_fields_exact=True,bindings=receipt,models=assets,numerical_DLL_sha256=build['numerical_DLL_sha256'],new_forwards=0))
status('PARENT_RESTORED_AND_AUDITED',files=len(index),source_runtime_files=native_count,new_forwards=0)
