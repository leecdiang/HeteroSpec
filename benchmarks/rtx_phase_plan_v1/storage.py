"""Verified lossless cold storage. Never called by the clean native worker."""
from pathlib import Path
import hashlib,json,os,time,zlib,shutil
ROOT=Path('D:/rtx188')
STORE=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/phase188-archive')
SECONDARY=Path('F:/rtx188-cold')
_index=None

def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write_new(p,j):
    with p.open('x',encoding='utf8') as f:json.dump(j,f,indent=2)
def index():
    global _index
    if _index is None:
        _index={}
        for p in STORE.glob('manifest-*.json'):
            for row in json.loads(p.read_bytes())['files']:_index[str(Path(row['path']).resolve()).casefold()]=row
    return _index
def unpack(row):
    parts=[]
    for h in row['chunks']:
        raw=zlib.decompress(chunk_path(h).read_bytes());assert hashlib.sha256(raw).hexdigest()==h;parts.append(raw)
    raw=b''.join(parts);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];return raw

def chunk_path(h):
    p=STORE/'chunks'/h[:2]/h
    return p if p.exists() else SECONDARY/'chunks'/h[:2]/h

def relocate_cold_chunks():
    """Bounded lossless relocation, separate from native output volumes."""
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    SECONDARY.mkdir(exist_ok=True);began=time.monotonic();before={p:shutil.disk_usage(p).free for p in ['C:/','D:/','E:/','F:/']}
    rows=[];size=0
    for p in sorted((STORE/'chunks').glob('*/*')):
        if size+p.stat().st_size>2.25*1024**3:break
        rows.append(dict(path=str(p),bytes=p.stat().st_size,chunk=p.name));size+=p.stat().st_size
    assert before['F:/']-size>=18*1024**3
    write_new(ROOT/'COLD_RELOCATION_PLAN.json',dict(files=rows,maximum_bytes=2.25*1024**3,cold_only_F_free_floor=18*1024**3,native_output_D_E_floor_unchanged=20*1024**3,C_system_floor_unchanged=10*1024**3,before_blind_test_outputs=True,old_F_sources_and_results_untouched=True))
    for r in rows:
        p=Path(r['path']);q=SECONDARY/'chunks'/r['chunk'][:2]/r['chunk'];q.parent.mkdir(parents=True,exist_ok=True)
        assert shutil.disk_usage(SECONDARY).free-r['bytes']>=18*1024**3
        if not q.exists():shutil.copy2(p,q)
        assert digest(p)==digest(q) and hashlib.sha256(zlib.decompress(q.read_bytes())).hexdigest()==r['chunk']
        p.unlink()
    write_new(ROOT/'COLD_ARCHIVE_RELOCATION.json',dict(files=len(rows),compressed_bytes=size,wall_s=time.monotonic()-began,before=before,after={p:shutil.disk_usage(p).free for p in before},all_chunk_bytes_verified_before_retirement=True,native_floors_unchanged=True))
    print('Cold relocation verified; C free GiB',shutil.disk_usage('C:/').free/1024**3,flush=True)
def read_bytes(path):
    p=Path(path)
    return p.read_bytes() if p.exists() else unpack(index()[str(p.resolve()).casefold()])
def paths():
    candidates=[]
    for base in (ROOT/'runs',ROOT/'final-runtime-original-R-view',ROOT/'resumed-views'):
        candidates += [p for p in base.rglob('sequence.bin') if p.is_file()]
    candidates += [p for p in (ROOT/'evidence-cas').glob('*/*') if p.is_file()]
    return candidates
def retire(rows,key):
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists(),'archive only between GPU attempts'
    manifest=STORE/('manifest-'+key+'.json');write_new(manifest,dict(files=rows,compression='zlib',chunk_size=1024*1024,logical_paths_preserved_as_identifiers=True))
    checked=set()
    for row in rows:
        p=Path(row['path']);assert p.resolve().is_relative_to(ROOT.resolve());st=p.stat();identity=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
        if identity not in checked:assert digest(p)==row['sha256'];assert hashlib.sha256(unpack(row)).hexdigest()==row['sha256'];checked.add(identity)
    # The complete reconstructible manifest and all chunk/file checks precede
    # retirement of every logical alias, including same-volume CAS hardlinks.
    for row in rows:Path(row['path']).unlink()
    write_new(STORE/('retirement-'+key+'.json'),dict(manifest_sha256=digest(manifest),removed_aliases=len(rows),verified_unique_payloads=len(checked)))
    global _index
    _index=None
def archive_qwen_states():
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    began=time.monotonic();before=shutil.disk_usage(ROOT).free;STORE.mkdir(exist_ok=True);selected={};payloads={}
    for p in (ROOT/'runs').glob('Qwen-matrix-*/native/*/captures/*/sequence.bin'):
        st=p.stat();identity=(st.st_dev,st.st_ino)
        if identity in selected:continue
        h=digest(p);chunks=[];full=hashlib.sha256()
        with p.open('rb') as f:
            while raw:=f.read(1024*1024):
                full.update(raw);ch=hashlib.sha256(raw).hexdigest();q=STORE/'chunks'/ch[:2]/ch;q.parent.mkdir(parents=True,exist_ok=True)
                if not q.exists():
                    assert shutil.disk_usage(STORE).free>=10*1024**3,'retain originals if cold-store reserve is reached'
                    q.write_bytes(zlib.compress(raw,1))
                assert zlib.decompress(q.read_bytes())==raw;chunks.append(ch)
        assert full.hexdigest()==h;row=dict(sha256=h,bytes=st.st_size,chunks=chunks);assert hashlib.sha256(unpack(row)).hexdigest()==h;selected[identity]=row;payloads[h]=row
    rows=[]
    for p in paths():
        st=p.stat();row=selected.get((st.st_dev,st.st_ino))
        if row is not None:rows.append(dict(row,path=str(p.resolve())))
    retire(rows,'qwen-engineering-states-v1')
    write_new(ROOT/'COLD_ARCHIVE_RECEIPT.json',dict(store=str(STORE),unique_payloads=len(payloads),logical_aliases=len(rows),unique_logical_bytes=sum(r['bytes'] for r in payloads.values()),freed_output_bytes=shutil.disk_usage(ROOT).free-before,wall_s=time.monotonic()-began,cold_volume_free_floor=10*1024**3,output_volumes_free_floor=20*1024**3,all_raw_bytes_reconstructible=True,shared_native_rule_unchanged=True))
    print('Cold archive verified; D free GiB',shutil.disk_usage(ROOT).free/1024**3,flush=True)
def retire_known():
    byhash={r['sha256']:r for r in index().values()};rows=[]
    for p in paths():
        h=p.name if p.parent.parent==ROOT/'evidence-cas' else digest(p)
        if h in byhash:rows.append(dict(byhash[h],path=str(p.resolve())))
    if rows:retire(rows,'known-'+str(time.time_ns()))

def retire_chunk_covered_final_states():
    """Preserve new serialized combinations of already saved exact chunks."""
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    began=time.monotonic();before=shutil.disk_usage(ROOT).free
    known={h for row in index().values() for h in row['chunks']};selected={}
    for p in (ROOT/'runs').glob('Qwen-exact-version-matrix-*/native/*/captures/*/sequence.bin'):
        s=p.stat();identity=(s.st_dev,s.st_ino)
        if identity in selected:continue
        chunks=[];full=hashlib.sha256();covered=True
        with p.open('rb') as f:
            while raw:=f.read(1024**2):
                h=hashlib.sha256(raw).hexdigest();full.update(raw);chunks.append(h)
                if h not in known:covered=False;break
        if covered:selected[identity]=dict(sha256=full.hexdigest(),bytes=s.st_size,chunks=chunks)
    rows=[]
    for p in paths():
        s=p.stat();row=selected.get((s.st_dev,s.st_ino))
        if row is not None:rows.append(dict(row,path=str(p.resolve())))
    if rows:retire(rows,'chunk-covered-final-'+str(time.time_ns()))
    write_new(ROOT/('FINAL_MATRIX_STORAGE-'+str(time.time_ns())+'.json'),dict(logical_aliases=len(rows),unique_payloads=len(selected),freed_output_bytes=shutil.disk_usage(ROOT).free-before,new_cold_payload_bytes=0,wall_s=time.monotonic()-began,all_original_file_hashes_verified=True))
    print('Exact-state chunk reuse freed GiB',(shutil.disk_usage(ROOT).free-before)/1024**3,flush=True)

def archive_smol_states():
    """Storage-only recovery; stop adding cold bytes above the system reserve."""
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    began=time.monotonic();before=shutil.disk_usage(ROOT).free;selected={};payloads={}
    candidates=list((ROOT/'runs').glob('Smol-matrix-*/native/*/captures/*/sequence.bin'))
    candidates+=list((ROOT/'runs').glob('Smol-old-free/native/*/target/state/*/sequence.bin'))
    candidates+=list((ROOT/'runs').glob('Smol-*-development/native/*/target/state/*/sequence.bin'))
    for p in sorted(candidates):
        st=p.stat();identity=(st.st_dev,st.st_ino)
        if identity in selected:continue
        h=digest(p);chunks=[]
        if shutil.disk_usage(STORE).free-st.st_size<11.5*1024**3:break
        with p.open('rb') as f:
            while raw:=f.read(1024*1024):
                ch=hashlib.sha256(raw).hexdigest();q=chunk_path(ch)
                if not q.exists():q=STORE/'chunks'/ch[:2]/ch
                q.parent.mkdir(parents=True,exist_ok=True)
                if not q.exists():q.write_bytes(zlib.compress(raw,1))
                assert zlib.decompress(q.read_bytes())==raw;chunks.append(ch)
        row=dict(sha256=h,bytes=st.st_size,chunks=chunks);assert hashlib.sha256(unpack(row)).hexdigest()==h
        selected[identity]=row;payloads[h]=row
    rows=[]
    for p in paths():
        st=p.stat();row=selected.get((st.st_dev,st.st_ino))
        if row is not None:rows.append(dict(row,path=str(p.resolve())))
    assert rows,'no safely archivable payloads'
    key='smol-engineering-'+str(time.time_ns());retire(rows,key)
    write_new(ROOT/(key+'.json'),dict(unique_payloads=len(payloads),logical_aliases=len(rows),freed_output_bytes=shutil.disk_usage(ROOT).free-before,wall_s=time.monotonic()-began,all_raw_bytes_reconstructible=True,shared_native_rule_unchanged=True))
    print('Smol cold archive verified; D free GiB',shutil.disk_usage(ROOT).free/1024**3,flush=True)

if __name__=='__main__':archive_qwen_states()
