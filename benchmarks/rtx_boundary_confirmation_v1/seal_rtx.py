"""CPU-only exact raw packaging, local restore and new-interpreter byte reanalysis."""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha
from prepare_rtx import root
def allocation(paths):
    unique={};logical=0;count=0
    for folder in paths:
        if not Path(folder).exists():continue
        for p in Path(folder).rglob('*'):
            if p.is_file():
                st=p.stat();logical+=st.st_size;count+=1;unique[st.st_dev,st.st_ino]=((st.st_size+4095)//4096)*4096+4096
    return dict(files=count,logical_bytes=logical,conservative_unique_allocation_bytes=sum(unique.values()),unique_files=len(unique),basis='unique file IDs;round data to4KiB plus4KiB per file metadata allowance;hardlinks counted once')
def package():
    raw=root();dest=Path(str(raw)+'-archive');dest.mkdir(exist_ok=False);index={};blobs={};metadata=[]
    for p in sorted(raw.rglob('*')):
        if not p.is_file():continue
        assert not p.is_symlink();rel=p.relative_to(raw).as_posix();digest=sha(p);binary=p.suffix=='.bin';index[rel]=dict(bytes=p.stat().st_size,sha256=digest,storage='blob' if binary else 'file')
        if binary:blobs.setdefault(digest,p)
        else:metadata.append((rel,p))
    save(dest/'MEMBERS.json',index);start=time.monotonic()
    with zipfile.ZipFile(dest/'raw.zip','x',zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
        z.write(dest/'MEMBERS.json','MEMBERS.json')
        for rel,p in metadata:assert sha(p)==index[rel]['sha256'];z.write(p,'files/'+rel)
        for digest,p in blobs.items():assert sha(p)==digest;z.write(p,'blobs/'+digest)
    usage=allocation([raw,dest]);assert usage['conservative_unique_allocation_bytes']<8*1024**3-512*1024**2
    receipt=dict(status='SEALED_LOCAL',archive_path=str(dest/'raw.zip'),archive_sha256=sha(dest/'raw.zip'),archive_bytes=(dest/'raw.zip').stat().st_size,member_manifest_sha256=sha(dest/'MEMBERS.json'),members=len(index),logical_member_bytes=sum(r['bytes'] for r in index.values()),unique_binary_blobs=len(blobs),unique_binary_bytes=sum(p.stat().st_size for p in blobs.values()),raw_location=str(raw),retention='RAW_LOCAL_ONLY',storage=usage,seconds=time.monotonic()-start,new_GPU_queries=0);save(dest/'ARCHIVE.json',receipt);print(json.dumps(receipt))
def restore():
    raw=root();archive=Path(str(raw)+'-archive');frozen=load(archive/'ARCHIVE.json');assert sha(archive/'raw.zip')==frozen['archive_sha256'];fresh=Path(str(raw)+'-fresh');fresh.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive/'raw.zip') as z:
        index=json.loads(z.read('MEMBERS.json'));assert index==load(archive/'MEMBERS.json');blobs=fresh/'binary_cas';blobs.mkdir()
        used={r['sha256'] for r in index.values() if r['storage']=='blob'}
        for digest in sorted(used):
            assert re.fullmatch('[a-f0-9]{64}',digest);data=z.read('blobs/'+digest);assert hashlib.sha256(data).hexdigest()==digest;(blobs/(digest+'.bin')).write_bytes(data)
        restored=fresh/'raw';restored.mkdir()
        for rel,row in index.items():
            path=PurePosixPath(rel);assert not path.is_absolute() and '..' not in path.parts and '\\' not in rel and ':' not in rel
            p=restored/rel;p.parent.mkdir(parents=True,exist_ok=True)
            if row['storage']=='blob':
                source=blobs/(row['sha256']+'.bin')
                try:os.link(source,p)
                except OSError as exc:
                    if getattr(exc,'winerror',None)!=1142:raise
                    shutil.copyfile(source,p)
            else:
                data=z.read('files/'+rel);assert hashlib.sha256(data).hexdigest()==row['sha256'];p.write_bytes(data)
            assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
    save(fresh/'RESTORE.json',dict(status='ALL_MEMBERS_EXACT',members=len(index),archive_sha256=frozen['archive_sha256'],manifest_sha256=frozen['member_manifest_sha256'],same_host=True,external_independent_review=False,storage=allocation([raw,archive,fresh])))
    assert allocation([raw,archive,fresh])['conservative_unique_allocation_bytes']<8*1024**3;print('restored',len(index),'members',fresh)

def sources():
    raw=root();dest=raw/'source_runtime';dest.mkdir(exist_ok=False);spec=load(raw/'RUN_SPEC.json')
    for p in V.iterdir():
        if p.is_file() and p.suffix in ['.py','.h','.cpp','.md','.json']:shutil.copyfile(p,dest/p.name)
    for name in ['collector.exe','address_cpu.exe','libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(V/'build'/name,dest/name)
    headers={}
    for source in [Path(spec['ggml_include']),Path(spec['vendor_include'])]:
        for p in source.rglob('*'):
            if p.is_file() and p.suffix in ['.h','.hpp']:
                out=dest/'external_headers'/source.name/p.relative_to(source);out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,out);headers[str(p)]=dict(sha256=sha(p),copy=out.relative_to(raw).as_posix())
    save(raw/'EXTERNAL_HEADERS.json',headers)
    actual={name:sha(Path(spec['runtime_directory'])/name) for name in spec['numerical_DLLs']};assert actual==spec['numerical_DLLs'];save(raw/'NUMERICAL_MODULES_POSTCHECK.json',dict(status='PASS',modules=actual,new_GPU_queries=0))

def replay():
    raw=root();fresh=Path(str(raw)+'-fresh');dest=Path(str(raw)+'-archive');spec=load(raw/'RUN_SPEC.json');environ=os.environ.copy();environ['HETEROSPEC_RUN_ROOT']=str(fresh/'raw');script=fresh/'raw/source_runtime/export_rtx.py';start=time.monotonic();p=subprocess.run([spec['python'],'-B',str(script),'--out',str(fresh/'reanalysis'),'--draws','4000'],env=environ,capture_output=True,timeout=900);save(fresh/'REPLAY_PROCESS.json',dict(exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),seconds=time.monotonic()-start,CPU_only=True));assert p.returncode==0,'fresh CPU replay failed'
    files=['observations.jsonl','HOSTS.csv','COVERAGE.csv','ANALYSIS.json']
    for name in files:assert (raw/'analysis_final'/name).read_bytes()==(fresh/'reanalysis'/name).read_bytes(),name
    left=load(raw/'analysis_final/AUDIT.json');right=load(fresh/'reanalysis/AUDIT.json');left.pop('raw_root_location_only');right.pop('raw_root_location_only');assert left==right
    save(dest/'FRESH_RECOMPUTE.json',dict(status='VERIFIED',all_member_bytes_exact=True,scientific_files_byte_equal=files,summary_equal_except_explicit_location=True,new_interpreter=True,same_host=True,external_independent_review=False,remote_raw_uploaded=False,new_GPU_calls=0))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['sources','package','restore','replay']);a=ap.parse_args();globals()[a.action]()
