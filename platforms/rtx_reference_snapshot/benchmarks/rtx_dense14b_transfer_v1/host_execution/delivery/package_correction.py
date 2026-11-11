import hashlib,json,shutil,zipfile
from pathlib import Path
base=Path('D:/rtx155'); repo=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr155')
dst=base/'closeout_correction_v2'; study=repo/'benchmarks/rtx_dense14b_transfer_v1'; host=study/'host_execution'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
old=json.loads((base/'epoch01/INDEPENDENT_RECOMPUTE.json').read_text());new=json.loads((dst/'INDEPENDENT_RECOMPUTE.json').read_text())
excluded={'QK_geometry','placement_note'}
for k in old:
    if k not in excluded:assert old[k]==new[k],k
assert digest(dst/'UNSTARTED_SLOTS.json')==digest(base/'epoch01/UNSTARTED_SLOTS.json')
sources=[base/'staging/native/build_source/worker.cpp',base/'build01/source/ggml/src/ggml-cuda/ggml-cuda.cu',base/'build01/source/ggml/src/ggml-backend.cpp']
correction={'version':2,'status':'REFERENCE_COUNTEREXAMPLE','native_requests_added':0,'all_numeric_outcomes_and_source_record_hashes_unchanged':True,'superseded_v1_report_sha256':digest(base/'epoch01/INDEPENDENT_RECOMPUTE.json'),'v2_report_sha256':digest(dst/'INDEPENDENT_RECOMPUTE.json'),'error':'v1 interpreted buffer device ownership as actual QK execution backend and claimed all-GPU. This is unsupported.','source_finding':'worker.cpp:55,69 reads buffer-type device. ggml-cuda.cu:1297-1326 uses CPU buffer_from_ptr for CUDA_Host, whose device is CUDA device0. ggml-backend.cpp:89-92 returns buffer-type device. Actual scheduler execution backend cannot be recovered from these labels.','corrected_scope':'Weight placement and QK shapes verified; actual QK compute backend unresolved. Original placement audit remains failed; no CPU/GPU compute coverage or operator-level cause claimed.','preservation':'Primary archive and COUNTEREXAMPLE_DECISIONS.zip remain byte-identical v1 artifacts. This supplement supersedes only placement interpretation and derived reports. No freeze, panel, raw, native binary or reference was changed.','source_files':[{'path':str(p),'sha256':digest(p)} for p in sources]}
save(dst/'CORRECTION_V2.json',correction)
for p in sources:shutil.copy2(p,dst/p.name)
for p in [host/'RESULTS.md',host/'PAPER_ADDENDUM.md',study/'AMENDMENTS.md',repo/'scripts/experiments/rtx_dense14b_transfer_v1/closeout_host.py']:shutil.copy2(p,dst/p.name)
prov=json.loads((host/'RECOMPUTE_PROVENANCE.json').read_text());prov.update({'version':2,'superseded_script_sha256':prov['script_sha256'],'script_sha256':digest(dst/'closeout_host.py'),'result':'Original pilot remains UNQUALIFIED. Both previous placement interpretations are unsupported; actual QK compute backend unresolved. Numerical counterexamples unchanged.','correction_sha256':digest(dst/'CORRECTION_V2.json')})
save(dst/'RECOMPUTE_PROVENANCE.json',prov)
for name in ['INDEPENDENT_RECOMPUTE.json','RECOMPUTE_PROVENANCE.json','CORRECTION_V2.json']:shutil.copy2(dst/name,host/name)
archive=base/'CLOSEOUT_CORRECTION_V2.zip';assert not archive.exists()
members=[]
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(dst.iterdir()):
        z.write(p,p.name);members.append({'path':p.name,'bytes':p.stat().st_size,'sha256':digest(p)})
with zipfile.ZipFile(archive) as z:
    for m in members:assert hashlib.sha256(z.read(m['path'])).hexdigest()==m['sha256']
save(base/'CLOSEOUT_CORRECTION_V2_MANIFEST.json',{'archive':archive.name,'bytes':archive.stat().st_size,'sha256':digest(archive),'files':members,'native_requests_added':0})
print('Correction packaged',archive.stat().st_size,len(members),'files; all numeric fields unchanged')
