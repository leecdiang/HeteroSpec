"""Packaging-only deduplication; frozen execution/analysis sources stay unchanged."""
import hashlib,json,pathlib,re,shutil,subprocess,tarfile,sys
from datetime import datetime,timezone
from restore import read,write,sha,restore
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1';DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
HERE=pathlib.Path(__file__).parent
def main():
    if (OUT/'ARCHIVE.json').exists():raise RuntimeError('An archive index already exists; do not silently replace it')
    receipt=read(DOC/'ARCHIVE_RECEIPT.json');original=pathlib.Path(receipt['clean_extraction'])
    old=read(OUT/'capsule/CONTENTS.json');files={};excluded=[]
    stage=pathlib.Path('C:/hs/b570-prefill-delivery-staging');stage.mkdir(parents=True,exist_ok=True)
    sources={}
    for name,h in old.items():
        if name.startswith('benchmarks/b570_prefill_diagnostic_v1/'):
            # The original clean-extraction verifier regenerated its derived
            # reports. Final authoritative metadata below supersedes that
            # working copy; immutable measurement files still require old SHA.
            continue
        if '/runtime/' in name:
            excluded.append({'path':name,'sha256':h,'reason':'rebuildable runtime binary; repository data policy'});continue
        p=original/name
        assert sha(p)==h,name
        sources[name]=p
    # Final post-archive metadata overlays only metadata, never raw attempts/arrays.
    for p in DOC.glob('*'):
        if p.is_file():sources[p.relative_to(ROOT).as_posix()]=p
    for name in ['STATE.json','STATUS.json','RUN_LEDGER.jsonl','RESUME.md','QUEUE.json','INPUTS.json','CONTROLLER_LAUNCH.json']:
        p=OUT/name
        if p.exists():sources[p.relative_to(ROOT).as_posix()]=p
    for p in (OUT/'audits').glob('*.json'):sources[p.relative_to(ROOT).as_posix()]=p
    for p in HERE.glob('*.py'):sources[p.relative_to(ROOT).as_posix()]=p
    extra=stage/'provenance';extra.mkdir(exist_ok=True)
    write(extra/'LOCAL_CAPSULE_PROVENANCE.json',{'archive_sha256':receipt['sha256'],'archive_bytes':receipt['bytes'],'original_contents':old,
      'excluded':excluded,'original_capsule':'retained in full on local persistent disk; remote portable archive preserves all original scientific raw file bytes and final metadata; compression/deduplication changes container bytes',
      'metadata_overlay':'Final closeout/report/status/ledger/audit metadata overlays pre-closeout archive snapshot; all measurement records unchanged'})
    sources['provenance/LOCAL_CAPSULE_PROVENANCE.json']=extra/'LOCAL_CAPSULE_PROVENANCE.json'
    pinned=pathlib.Path('C:/hs/b570-direct-id-v1-src')
    for name in ['LICENSE','common/sampling.cpp','common/sampling.h','include/llama.h','src/llama-context.cpp','examples/speculative/speculative.cpp']:
        sources['provenance/pinned_source/'+name]=pinned/name
    license_note=extra/'LICENSE_SCOPE.md';license_note.write_text('Repository license remains pending; this archive is uploaded only to the existing private repository. Included pinned llama.cpp source retains the ggml MIT license. Fixed HumanEval prompt IDs/text are bounded experiment inputs; no complete dataset or model weights are included. Machine-local paths are retained as provenance.\n',encoding='utf-8')
    sources['provenance/LICENSE_SCOPE.md']=license_note
    unique={};total=0;secret_flags=[]
    # Never print candidate secret values. Record only paths if a concrete pattern is detected.
    patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}\b'),re.compile(rb'\bgithub_pat_[A-Za-z0-9_]{40,}\b'),re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}\b')]
    for name,p in sorted(sources.items()):
        h=sha(p);size=p.stat().st_size;total+=size
        files[name]={'sha256':h,'bytes':size,'source':'original immutable snapshot' if p.is_relative_to(original) else 'final metadata or pinned provenance'}
        if p.suffix.lower() in ['.py','.cpp','.h','.md','.json','.txt','.csv']:
            content=p.read_bytes()
            if any(rx.search(content) for rx in patterns):secret_flags.append(name)
        if h not in unique:
            dest=stage/'blobs'/h[:2]/h;dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():assert sha(dest)==h and dest.stat().st_size==size
            else:shutil.copyfile(p,dest)
            unique[h]={'bytes':size,'path':str(dest)}
    if secret_flags:raise RuntimeError('Secret-pattern review needed for paths: '+repr(secret_flags))
    manifest={'schema':'heterospec.b570.prefill.cas.manifest.v1','study':'B570_PREFILL_DIAGNOSTIC_V1','created_utc':datetime.now(timezone.utc).isoformat(),
      'execution_closeout_commit':'86ea11604ac178f2117e1def246c54e313e07b64','files':files,'excluded':excluded,
      'file_bytes':total,'unique_blobs':len(unique),'unique_bytes':sum(x['bytes'] for x in unique.values()),
      'secret_pattern_scan':'PASS; no supported private-key/GitHub/OpenAI token pattern; values not logged',
      'privacy_scope':'Existing private leecdiang/HeteroSpec repository; original authoritative username/local paths retained as provenance',
      'raw_preservation':'All arrays, endpoints, traces, attempt logs, KV before/restored/source-after, pending logits and legacy expected arrays preserved bytewise; deduplicated files restore to distinct ordinary files'}
    write(stage/'MANIFEST.json',manifest)
    archive=stage/'evidence-cas.tar.gz'
    with tarfile.open(archive,'w:gz',compresslevel=3) as tf:
        tf.add(stage/'MANIFEST.json',arcname='MANIFEST.json',recursive=False)
        for h in sorted(unique):tf.add(unique[h]['path'],arcname='blobs/'+h[:2]+'/'+h,recursive=False)
    parts=[]
    with archive.open('rb') as f:
        while True:
            block=f.read(48*1024*1024)
            if not block:break
            h=hashlib.sha256(block).hexdigest();dest=OUT/(h+'.part')
            if dest.exists():assert sha(dest)==h
            else:
                tmp=dest.with_suffix('.part.tmp');tmp.write_bytes(block);tmp.replace(dest)
            parts.append({'path':dest.name,'sha256':h,'bytes':len(block)})
    index={'schema':'heterospec.b570.prefill.cas.archive.v1','created_utc':datetime.now(timezone.utc).isoformat(),
      'archive_sha256':sha(archive),'archive_bytes':archive.stat().st_size,'parts':parts,'manifest_sha256':sha(stage/'MANIFEST.json'),
      'manifest_files':len(files),'file_bytes':total,'unique_blobs':len(unique),'unique_bytes':manifest['unique_bytes'],
      'original_local_capsule_sha256':receipt['sha256'],'original_local_capsule_bytes':receipt['bytes'],'excluded':excluded,
      'restore':'python scripts/platform/b570_prefill_delivery_v1/restore.py --archive artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json --dest C:/hs/prefill-restored --receipt restore-receipt.json',
      'remote_status':'content is not considered delivered until remote read-back verification receipt exists'}
    write(OUT/'ARCHIVE.json',index);write(OUT/'REMOTE_MANIFEST.json',manifest)
    (OUT/'.gitattributes').write_text('*.part -text\n',encoding='ascii')
    write(DOC/'PACKAGING_IDENTITY.json',{'phase':'post-outcome packaging only','created_utc':index['created_utc'],'scripts':{p.name:sha(p) for p in HERE.glob('*.py')},
      'frozen_execution_sources_changed':False,'original_arrays_changed':False,'archive_index_sha256':sha(OUT/'ARCHIVE.json'),'remote_manifest_sha256':sha(OUT/'REMOTE_MANIFEST.json'),
      'part_size_max_bytes':48*1024*1024,'repository_data_policy':'docs/data_policy.md; source/processed records plus bounded explicit paper-critical raw archive; rebuildable binaries excluded'})
    print(json.dumps({'phase':'PACKAGED','archive_bytes':index['archive_bytes'],'parts':len(parts),'files':len(files),'unique_blobs':len(unique)},indent=2),flush=True)
    restored=pathlib.Path('C:/hs/b570-prefill-portable-local')
    restore(OUT/'ARCHIVE.json',restored,DOC/'PORTABLE_LOCAL_VERIFICATION.json')
if __name__=='__main__':main()
