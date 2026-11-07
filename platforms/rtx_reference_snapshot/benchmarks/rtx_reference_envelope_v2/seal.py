"""CPU-only deduplicated archive and exact-byte local fresh restore.

Raw telemetry remains in the author-approved D: evidence location. Git receives
compact summaries and hashes only. Every binary occurrence is represented; the
container stores each immutable byte string once. No scientific record is edited.
"""
import argparse,hashlib,json,os,re,shutil,subprocess,sys,time,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha
from run import root,dedup
def allocation(paths):
    unique={};logical=0;count=0
    for folder in paths:
        if not Path(folder).exists():continue
        for p in Path(folder).rglob('*'):
            if p.is_file():
                st=p.stat();logical+=st.st_size;count+=1;unique[st.st_dev,st.st_ino]=((st.st_size+4095)//4096)*4096+4096
    return dict(files=count,logical_bytes=logical,conservative_unique_allocation_bytes=sum(unique.values()),unique_files=len(unique),basis='unique file IDs;round data to4KiB plus4KiB per file metadata allowance;hardlinks counted once')
def sources():
    raw=root();s=load(raw/'RUN_SPEC.json');out=raw/'source_runtime';out.mkdir(exist_ok=False)
    for p in V.iterdir():
        if p.is_file() and p.suffix in ['.py','.h','.cpp','.md','.json','.jsonl','.csv']:shutil.copyfile(p,out/p.name)
    for name in ['native.exe','boundary.exe','libggml.dll.a','libggml-base.dll.a']:shutil.copyfile(V/'build'/name,out/name)
    dependencies={}
    for folder in [Path(s['ggml_include']),Path(s['vendor_include'])]:
        for p in folder.rglob('*'):
            if p.is_file() and p.suffix in ['.h','.hpp']:
                destination=out/'external_headers'/folder.name/p.relative_to(folder);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination);dependencies[str(p)]=dict(sha256=sha(p),copy=destination.relative_to(raw).as_posix())
    save(raw/'EXTERNAL_HEADER_INDEX.json',dependencies)
    # Recover exact runtime source bytes from each core formal freeze,not a
    # line-ending-normalized substitute. Old runtime headers are still unchanged.
    for stage in ['N1','T1']:
        f=load(raw/(stage+'_FREEZE.json'));target=raw/'formal_sources'/stage;target.mkdir(parents=True)
        for name,digest in f['files'].items():
            current=V/('build/'+name if name=='native.exe' else name)
            if sha(current)==digest:data=current.read_bytes()
            else:
                data=subprocess.check_output(['git','-C',str(V.parents[1]),'show',f['git']+':benchmarks/rtx_reference_envelope_v2/'+name])
            assert hashlib.sha256(data).hexdigest()==digest,'exact consumed source unavailable';(target/name).write_bytes(data)
    selected=[]
    for c in s['contexts']:selected.extend(c['inputs']);selected.extend(c['references'].values())
    plan=load(raw/'R1/PLAN.json')
    for c in plan['fixtures']:
        for folder in [Path(c['root'])]+list(map(Path,c['serial_roots'])):
            if not (folder/'BLOBS.json').exists():dedup(folder)
            selected.extend(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in folder.iterdir() if p.is_file() and p.suffix in ['.bin','.json'])
        p=Path(c['root'])/'ordinary_reference.bin';selected.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
    index={};cas=raw/'cas'
    for row in selected:
        source=Path(row['path']);digest=sha(source);assert digest==row['sha256'];target=cas/(digest+'.bin')
        if not target.exists():shutil.copyfile(source,target)
        assert sha(target)==digest;index[os.path.normcase(str(source.resolve()))]=dict(bytes=source.stat().st_size,sha256=digest,cas=target.relative_to(raw).as_posix())
    save(raw/'SOURCE_INDEX.json',index)
    after={name:sha(Path(s['runtime_directory'])/name) for name in s['numerical_DLLs']};assert after==s['numerical_DLLs'];save(raw/'NUMERICAL_MODULES_POSTCHECK.json',dict(status='PASS',modules=after,new_GPU_queries=0))
    print('source index',len(index),'entries')
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
    mapping={k:str(restored/row['cas']) for k,row in load(restored/'SOURCE_INDEX.json').items()}
    for original,row in load(restored/'SOURCE_INDEX.json').items():assert sha(mapping[original])==row['sha256']
    save(fresh/'SOURCE_MAP.json',mapping);save(fresh/'RESTORE.json',dict(status='ALL_MEMBERS_EXACT',members=len(index),archive_sha256=frozen['archive_sha256'],manifest_sha256=frozen['member_manifest_sha256'],source_map_entries=len(mapping),same_host=True,external_independent_review=False,storage=allocation([raw,archive,fresh])))
    assert allocation([raw,archive,fresh])['conservative_unique_allocation_bytes']<8*1024**3;print('restored',len(index),'members',fresh)
def replay():
    raw=root();archive=Path(str(raw)+'-archive');fresh=Path(str(raw)+'-fresh');script=fresh/'raw/source_runtime/final_analysis.py';s=load(raw/'RUN_SPEC.json');start=time.monotonic();p=subprocess.run([s['python']['path'],'-B',str(script),'--root',str(fresh/'raw'),'--out',str(fresh/'analysis'),'--source-map',str(fresh/'SOURCE_MAP.json')],capture_output=True,timeout=600);save(fresh/'REPLAY_PROCESS.json',dict(exit=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'),seconds=time.monotonic()-start,CPU_only=True));assert p.returncode==0
    original=raw/'analysis_verified';names=[p.name for p in original.iterdir() if p.suffix=='.csv' or p.name=='R1_SUMMARY.json'];checked=[]
    for name in names:assert (original/name).read_bytes()==(fresh/'analysis'/name).read_bytes(),name;checked.append(name)
    left=load(original/'SUMMARY.json');right=load(fresh/'analysis/SUMMARY.json');left.pop('raw_root');right.pop('raw_root');assert left==right
    save(archive/'FRESH_RECOMPUTE.json',dict(status='VERIFIED',archive_sha256=load(archive/'ARCHIVE.json')['archive_sha256'],all_restored_member_bytes_exact=True,scientific_tables_byte_equal=checked,summary_equal_except_explicit_restore_location=True,same_host_new_interpreter=True,external_independent_review=False,remote_raw_upload=False,new_GPU_queries=0));print('fresh recompute VERIFIED',len(checked),'tables')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['sources','package','restore','replay']);a=ap.parse_args();{'sources':sources,'package':package,'restore':restore,'replay':replay}[a.action]()
