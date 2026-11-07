"""M1 extension of the successor's allowlisted scientific text exporter.

Same raw/derived SHA distinction and private binary index. Adds M1's capability
negative receipts and source/build bindings; never traverses the host inventory.
Run only after timing has ended. No native scientific check is replaced here.
"""
from pathlib import Path
import argparse, gzip, hashlib, json, re, shutil, sys

def main():
    p=argparse.ArgumentParser()
    for key in ('work','out','builds','runtime'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();sys.path.insert(0,str(a.runtime.resolve()));from common import need,read,save,sha
    w=a.work.resolve();out=a.out.resolve();need(read(w/'PIPELINE_STATUS.json')['status']=='COMPLETE','No export during timing')
    need(not out.exists() and not out.is_relative_to(w),'New external export epoch');out.mkdir(parents=True)
    # Copy exact build receipts into this lane for relative archive identities;
    # the actual linked archives and originals remain at their existing paths.
    sources=[(a.builds.resolve()/role,f'build-{role}-01') for role in ('loop4','packed')]
    sources += [(a.builds.resolve().parent/'m1-dispatch-build-01'/role,f'build-dispatch-{role}-01') for role in ('loop4','packed')]
    for source,name in sources:
        dest=w/name;need(not dest.exists(),'Preserve export preparation epochs');dest.mkdir()
        for name in ('BUILD.json','DEPENDENCIES.json'):
            shutil.copy2(source/name,dest/name)
        for phase in ('compile','link'):
            shutil.copytree(source/phase,dest/phase)
    replacements=[(str(w.parent),'<PRIVATE_ROOT>'),(str(Path.home()),'<HOME>')]
    def clean(s):
        for old,new in replacements:s=s.replace(old,new)
        s=re.sub(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}','<ALLOCATED_GPU_UUID>',s)
        s=re.sub(r'("(?:allocation_id|authorization_id)"\s*:\s*)"[^"\n]*"',r'\1"<EXPLICIT_PRIVATE_ALLOCATION>"',s)
        return s
    chosen=set()
    for name in ('ledger.jsonl','PRIOR_ACCOUNTING.json','BINDING.json','PIPELINE_STATUS.json','pipeline-events.jsonl',
                 'capability-negatives-phase-01.log','confirmation-phase-01.log'):
        if (w/name).is_file():chosen.add(w/name)
    chosen.update(w.glob('helper-*.log'))
    prefixes=['inputs-01','qualification-01','qualification-dispatch-01','capability-negatives-01','panel-01',*[name for _,name in sources]]
    for prefix in prefixes:
        chosen.update(p for p in (w/prefix).rglob('*') if p.is_file() and p.suffix in ('.json','.jsonl','.log','.txt'))
    records=[];index=[]
    for path in sorted(chosen):
        relative=str(path.relative_to(w));raw=path.read_bytes();text=raw.decode('utf8');public=clean(text);encoded=public.encode()
        need(not re.search(r'(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])',public),'Unreviewed IPv4-shaped value: '+relative)
        need(not any(x in public for x in ('X-Amz-','https://cdn-lfs','xet-hf','Authorization: Bearer')),'Network credential material entered allowlist')
        if path.suffix=='.json':json.loads(public)
        if path.suffix=='.jsonl':
            for row in public.splitlines():json.loads(row)
        records.append(dict(path=relative,text=public));index.append(dict(path=relative,raw_bytes=len(raw),raw_sha256=hashlib.sha256(raw).hexdigest(),
            exported_bytes=len(encoded),exported_sha256=hashlib.sha256(encoded).hexdigest(),transformed=text!=public))
    captures=[]
    for directory in sorted(w.glob('qualification-*')):
        for path in sorted(directory.rglob('*')):
            if path.is_file() and path.suffix in ('.f32','.bin'):captures.append(dict(path=str(path.relative_to(w)),bytes=path.stat().st_size,sha256=sha(path)))
    data=json.dumps(dict(schema='linux-transfer.public-text-bundle.v1',records=records),ensure_ascii=False,separators=(',',':')).encode()
    bundle=out/'scientific-records.json.gz'
    with bundle.open('xb') as f:
        with gzip.GzipFile(filename='',fileobj=f,mode='wb',mtime=0) as z:z.write(data)
    save(out/'TEXT_INDEX.json',dict(files=index,bundle_sha256=sha(bundle),uncompressed_bytes=len(data),public_text_is_derived=True))
    save(out/'BINARY_CAPTURE_INDEX.json',dict(files=captures,count=len(captures),bytes=sum(x['bytes'] for x in captures),public_raw_capture_archive=False,
        scope='Every new M1 native binary capture; historical independent R captures remain bound to predecessor public indices'))
    save(out/'EXPORT_SCOPE.json',dict(text_files=len(index),binary_captures=len(captures),raw_records_retained_privately=True,
        original_hash_fields_unchanged=True,text_index_sha256=sha(out/'TEXT_INDEX.json'),binary_index_sha256=sha(out/'BINARY_CAPTURE_INDEX.json'),bundle_sha256=sha(bundle),
        exporter_derived_from_commit='592abdfe9267fd97ecbde18cd0ee9a1bfc319e20',exporter_qualified_source_sha256=sha(a.runtime/'export_evidence.py'),
        excluded=['company inventory/configuration','credentials','other processes or users','model weights','executables and numerical archives'],
        no_public_binary_archive_readback_claim=True))
    print(json.dumps(dict(text_files=len(index),binary_captures=len(captures),bundle_bytes=bundle.stat().st_size)),flush=True)

if __name__=='__main__':main()
