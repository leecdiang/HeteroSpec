"""Export only changed numerical source plus exact origin and object bindings."""
from pathlib import Path
import argparse,hashlib,json,shutil

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((HERE/'SOURCE_PREPARED.json').read_bytes())['old_source_sha256']
final=json.loads((HERE/'FINAL_SOURCE_IDENTITIES.json').read_bytes())['source_files_sha256']
parser=argparse.ArgumentParser();parser.add_argument('--out',default='delta-v2');args=parser.parse_args()
target=HERE/args.out
if target.parent!=HERE:raise RuntimeError('isolated delta output required')
target.mkdir(exist_ok=False)
canonical=json.dumps(sorted(old.items()),separators=(',',':')).encode()
origin={'schema':'heterospec.e03.original-core-manifest.v1','profile':'pinned Windows packed source tree',
    'old_source_root_hint':'D:/rtx192-review-v2/native-v2/cores/packed','files':old,
    'canonical_member_manifest_sha256':hashlib.sha256(canonical).hexdigest(),
    'archive_reference':{'url':'https://github.com/leecdiang/HeteroSpec/releases/download/tpds-phase1-rtx-review-v2-evidence-20261107/rtx-phase1-source.zip',
        'sha256':'57cbfbfe43ae1c4b4ed5ba3f5261412daa2b5c14b712e76d868da55f4f8a4101',
        'scope':'Historical whole source kit locator. Exact old-core member hashes above are authoritative.'}}
(target/'ORIGIN_MANIFEST.json').write_text(json.dumps(origin,indent=2),encoding='utf8')
overrides=[]
for relative,h in final.items():
    if old.get(relative)==h:continue
    source=HERE/'final-source'/relative
    if sha(source)!=h:raise RuntimeError('final source changed: '+relative)
    dest=target/'files'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    if relative.endswith('hs_launch_budget.cu'):built=ROOT/'e03/launch_budget/hs_launch_budget.cpp'
    elif Path(relative).name in ('mmvq.cu','ggml-cuda.cu','hs_e03_runtime.cpp','hs_e03_runtime.hpp'):built=HERE/'stage-v4'/Path(relative).name
    elif Path(relative).name=='hs_launch_budget.hpp':built=ROOT/'e03/launch_budget/hs_launch_budget.hpp'
    else:built=HERE/'source'/relative
    overrides.append({'target_relative_path':relative,'delta_relative_path':dest.relative_to(target).as_posix(),'sha256':h,
        'old_sha256':old.get(relative),'as_built_source_or_configuration':str(built) if built.exists() else 'manual build configuration only',
        'as_built_file_sha_matches_final':sha(built)==h if built.exists() else None})
mapping={'schema':'heterospec.e03.runtime-source-overrides.v1','origin_manifest':'ORIGIN_MANIFEST.json','final_source_file_count':len(final),
    'overrides':overrides,'overrides_count':len(overrides),'uniform_future_rebuild_source':str(HERE/'final-source'),
    'as_built_header_variants':{'batch_v1_budget_header':{'path':str(HERE/'source/ggml/src/ggml-cuda/hs_launch_budget.hpp'),'sha256':sha(HERE/'source/ggml/src/ggml-cuda/hs_launch_budget.hpp')},
        'final_provider_header':{'path':str(ROOT/'e03/launch_budget/hs_launch_budget.hpp'),'sha256':sha(ROOT/'e03/launch_budget/hs_launch_budget.hpp')},
        'compatibility':'Only one additional C function declaration. Existing C signatures and snapshot struct unchanged; no inline implementation in header.',
        'diff':'../stage-v3/BUDGET_HEADER_ABI_DIFF.patch'},
    'universal_byte_identical_DLL_rebuild_claim':False,'native_numerical_qualification':'NOT_RUN'}
(target/'OVERRIDES.json').write_text(json.dumps(mapping,indent=2),encoding='utf8')
batch_identities=json.loads((HERE/'build-v1/SOURCE_IDENTITIES.json').read_bytes())
receipts=json.loads((HERE/'build-v3/COMPILE_RECEIPTS.json').read_bytes())
bindings={'schema':'heterospec.e03.as-built-runtime-bindings.v1','DLL':{'path':str(HERE/'build-v3/bin/ggml-cuda.dll'),'sha256':sha(HERE/'build-v3/bin/ggml-cuda.dll')},
    'object_count':len(receipts),'objects':receipts,'old_batch_source_and_headers_sha256':batch_identities,
    'old_batch_all_source_header_hashes_still_match':all(sha(HERE/'source'/p)==h for p,h in batch_identities.items()),
    'old_batch_changed_members':[{'path':p,'before_sha256':h,'current_sha256':sha(HERE/'source'/p)} for p,h in batch_identities.items() if sha(HERE/'source'/p)!=h],
    'reused_recorded_CUDA_catalog_unchanged_except_superseded_provider':all(sha(HERE/'source'/p)==h for p,h in batch_identities.items() if not p.replace('\\','/').endswith('/hs_launch_budget.cu')),
    'dependency_evidence_limit':'The 283-member CUDA catalog does not contain all non-CUDA .h files. Origin/current full-tree manifests bind those headers, but no exhaustive per-compiler dependency transcript or independent compile-start rehash of every target header is claimed.',
    'provider_change_scope':'Original batch provider object is superseded and not linked. Final DLL contains one newly compiled canonical final provider object; actor/time of source-copy sync is recorded separately if available.',
    'provider_sync_deviation':{'actor':'/root/resume_safety','exact_sync_time':'NOT_RECORDED','approximate_catalog_time_utc':'2026-11-12T09:09:38Z (approximate evidence bound only, not exact sync time)',
        'operation':'shutil.copy2(canonical hs_launch_budget.cpp, runtime/source/ggml/src/ggml-cuda/hs_launch_budget.cu)',
        'old_source_preserved':'e03/launch_budget/cpu-checks-v1/source_snapshot/hs_launch_budget.cpp',
        'old_source_sha256':'74e727d1a30dd9c09349371b9a937b25d489f861909234ccbbc3d33f3a4af90d',
        'effect':'First batch was not globally source-frozen for its superseded provider TU. No affected provider object is linked into final DLL.'},
    'fresh_stage_source':json.loads((HERE/'stage-v4/SOURCE.json').read_bytes()),
    'final_budget_provider':{'path':str(ROOT/'e03/launch_budget/hs_launch_budget.cpp'),'sha256':sha(ROOT/'e03/launch_budget/hs_launch_budget.cpp'),
        'HS_LB_CPU_TEST_ONLY':False,'linked_implementation_objects':1},
    'GPU_execution':'NOT_RUN','ordinary_DLL_LoadLibrary':'NOT_RUN_BLOCKED','source_delta_only_not_old_D_changes':True}
(HERE/'AS_BUILT_BINDINGS_FINAL.json').write_text(json.dumps(bindings,indent=2),encoding='utf8')
print(json.dumps({'delta_overrides':len(overrides),'delta_bytes':sum(p.stat().st_size for p in (target/'files').rglob('*') if p.is_file()),
    'old_core_files':len(old),'object_count':len(receipts),'old_batch_headers_unchanged':bindings['old_batch_all_source_header_hashes_still_match']}))
