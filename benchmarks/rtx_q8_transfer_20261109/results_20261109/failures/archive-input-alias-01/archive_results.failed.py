"""Lossless content-addressed archive, complete byte readback and public text packet."""
from pathlib import Path
import datetime,gzip,hashlib,json,os,shutil,time,zipfile
from admission import HERE,ROOT,REPO,put,sha
from execute import WORK,BASE

DEST=REPO.parent/'q8rtx211-evidence-20261109'

def main():
    started=time.monotonic();DEST.mkdir(exist_ok=False);files={}
    def add(name,p):
        p=Path(p).resolve();assert p.is_file() and not p.is_symlink()
        assert p.suffix.lower() not in ('.gguf','.key','.pem') and p.name.lower() not in ('.env','credentials')
        if name in files:assert files[name]==p
        files[name]=p
    for p in WORK.rglob('*'):
        if p.is_file() and not any(x in p.relative_to(WORK).parts for x in ('compiler-cache','temp')):add('work/'+p.relative_to(WORK).as_posix(),p)
    for p in ROOT.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.name!='scientific-records.json.gz':add('records/'+p.relative_to(ROOT).as_posix(),p)
    for p in HERE.iterdir():
        if p.is_file():add('scripts/'+p.name,p)
    for p in (BASE/'R-Qwen').rglob('*'):
        if p.is_file():add('original-R/'+p.relative_to(BASE/'R-Qwen').as_posix(),p)
    inherited=json.loads((ROOT/'CUMULATIVE_LEDGER_INITIAL.json').read_bytes())
    assert sha(BASE/'ledger.sqlite')==inherited['sha256']
    add('legacy/ledger.sqlite',BASE/'ledger.sqlite')
    for core in ('loop4','packed'):
        add('legacy/parent-closure-'+core+'.json',BASE/'freezes'/core/'BUILD_FREEZE.json')
    for i in range(4):add(f'legacy/original-R-free-r{i}.json',Path('D:/rtx188/runs/Qwen-old-free/native')/f'r{i}-heavy/receipt.json')
    closure=json.loads((ROOT/'SOURCE_BINDINGS.json').read_bytes());aliases={}
    for name,item in closure['files'].items():
        p=Path(name);assert sha(p)==item['sha256'];alias='compiler-inputs/'+item['sha256']+'/'+p.name;add(alias,p);aliases[name]=alias
    for name in ('LICENSE','LICENSE_SCOPE.txt','CONTRIBUTING.md'):
        p=REPO/name
        if p.exists():add('repository/'+name,p)
    archive=DEST/'complete-evidence.cas.zip';index=[];blobs={};public=[];textpath=DEST/'scientific-records.json.gz'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z, textpath.open('xb') as raw:
        with gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=1) as g:
            g.write(b'{"schema":"heterospec.rtx211.text-bundle.v1","records":[');first=True
            for name,p in sorted(files.items()):
                size=p.stat().st_size;digest=sha(p);blob='blobs/'+digest
                assert shutil.disk_usage(DEST).free>=10*1024**3+size+1024**3,'Archive system-volume reserve'
                if digest not in blobs:z.write(p,blob);blobs[digest]=dict(bytes=size,blob=blob)
                else:assert blobs[digest]['bytes']==size
                index.append(dict(path=name,sha256=digest,bytes=size,blob=blob))
                # No weights, credentials or unrelated host files are selected.
                excluded_public=name in ('records/cohort/rendered.jsonl','records/cohort/tokens.jsonl')
                if not excluded_public and (size<=128*1024**2 or p.name in ('LIVE_RECORDS.json','SAME_WORK_CLEAN_RECORDS.json')) and p.suffix.lower() not in ('.exe','.dll','.obj','.lib','.a','.sqlite','.f32','.bin','.gz','.zip','.bundle','.npy'):
                    try:data=p.read_bytes();text=data.decode('utf8')
                    except UnicodeDecodeError:continue
                    if '\x00' in text:continue
                    record=json.dumps(dict(path=name,text=text),sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
                    if not first:g.write(b',')
                    first=False;g.write(record);public.append(dict(path=name,bytes=size,sha256=digest))
            g.write(b']}')
    manifest=dict(schema='heterospec.rtx211.lossless-cas.v1',files=index,unique_blobs=blobs,compiler_aliases=aliases,
        source_work=str(WORK),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,logical_bytes=sum(x['bytes'] for x in index),logical_files=len(index),
        source_files_not_deleted=True,weights_included=False,raw_zip_scope='Complete selected new raw/source/runtime/compiler artifacts and original-R operands; immutable parent full numerical source remains explicitly hash-bound PR195 dependency.')
    put(DEST/'ARCHIVE_INDEX.json',manifest)
    # Read every stored byte back, then restore all logical paths by same-volume
    # hardlinks. Original experimental paths remain untouched.
    restore=DEST/'readback';restore.mkdir();seen=set();blobroot=restore/'.blobs';blobroot.mkdir()
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist())=={v['blob'] for v in blobs.values()}
        for digest,meta in blobs.items():
            p=blobroot/digest;h=hashlib.sha256();count=0
            with z.open(meta['blob']) as source,p.open('xb') as target:
                while data:=source.read(4*1024**2):
                    assert shutil.disk_usage(restore).free>=10*1024**3+len(data)+64*1024**2
                    h.update(data);count+=len(data);target.write(data)
            assert h.hexdigest()==digest and count==meta['bytes'];seen.add(digest)
    for item in index:
        p=restore/item['path'];assert p.resolve().is_relative_to(restore.resolve());p.parent.mkdir(parents=True,exist_ok=True);os.link(blobroot/item['sha256'],p)
        assert p.stat().st_size==item['bytes'] and os.path.samefile(blobroot/item['sha256'],p)
    assert len(seen)==len(blobs)
    put(ROOT/'ARCHIVE_READBACK.json',dict(passed=True,archive=str(archive),archive_sha256=manifest['archive_sha256'],index=str(DEST/'ARCHIVE_INDEX.json'),index_sha256=sha(DEST/'ARCHIVE_INDEX.json'),
        restored_root=str(restore),logical_files=len(index),logical_bytes=manifest['logical_bytes'],unique_blobs=len(blobs),all_blob_bytes_reread=True,all_logical_paths_restored=True,
        method='SHA256 content-addressed ZIP64; every unique blob decompressed/rehashed; every logical path restored by hardlink without deleting original data',wall_seconds=time.monotonic()-started))
    packet=ROOT/'public_archive';packet.mkdir(exist_ok=False);parts=[]
    with textpath.open('rb') as source:
        number=0
        while data:=source.read(512*1024):
            p=packet/f'scientific-records.json.gz.part-{number:04d}';p.write_bytes(data);parts.append(dict(name=p.name,bytes=len(data),sha256=sha(p)));number+=1
    put(packet/'PARTS.json',dict(joined_sha256=sha(textpath),joined_bytes=textpath.stat().st_size,parts=parts))
    put(packet/'TEXT_INDEX.json',dict(files=public,weights_included=False,raw_binary_scope='Private complete CAS archive retained and fully restored; public text/byte commitments do not independently requalify private numerical payloads.'))
    public_paths={v['path'] for v in public}
    put(packet/'BINARY_INDEX.json',dict(files=[x for x in index if x['path'] not in public_paths],archive_index_sha256=sha(DEST/'ARCHIVE_INDEX.json')))
    print(json.dumps(dict(archive=str(archive),archive_GiB=archive.stat().st_size/1024**3,logical_files=len(index),unique_blobs=len(blobs),text_parts=len(parts),wall_seconds=time.monotonic()-started)),flush=True)

if __name__=='__main__':main()
