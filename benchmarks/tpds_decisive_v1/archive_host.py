"""Lossless chunk archival of finished qualification payloads, with restore."""
from build_host import *
import hashlib,zlib,os,sys
STORE=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/rtx184-evidence')
def archive(ix,normalized_only=False):
    from native_adapter import RUNS
    from qualify_host import QUAL
    suffix='' if ix==0 else '-root'+str(ix);bases=[]
    for arm in ('M','D1','D2','D4'):
        case=QUAL/(arm+suffix);assert (case/'QUALIFICATION.json').exists()
        # Keep clean timing-history qualification executable after archival:
        # only native bulk records are archived, normalized final bank remains.
        bases.extend([case/'candidate/cas',case/'free/cas',case/'bank/cas'])
        if not normalized_only:bases.extend([RUNS/('development-v3-'+arm+suffix),RUNS/('forced-v2-'+arm+suffix)])
    if ix and not normalized_only: bases += [RUNS/('old-r'+suffix+('-v3' if ix==1 else '')),RUNS/('observer-r'+suffix)]
    key='root'+str(ix)+('-normalized' if normalized_only else '')
    STORE.mkdir(exist_ok=True);manifest=STORE/(key+'.json');assert not manifest.exists();rows=[];chunks=set();new_bytes=0;inodes={}
    for base in bases:
        for p in sorted(base.rglob('*')):
            if not p.is_file() or not (p.suffix in ('.bin','.f32') or 'cas' in p.parts):continue
            stat=p.stat();identity=(stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns)
            if identity in inodes:
                rows.append(dict(inodes[identity],path=str(p.resolve())));continue
            full=hashlib.sha256();parts=[];size=0
            with p.open('rb') as f:
                while data:=f.read(1024*1024):
                    full.update(data);size+=len(data);h=hashlib.sha256(data).hexdigest();q=STORE/'chunks'/h[:2]/h;q.parent.mkdir(parents=True,exist_ok=True)
                    if not q.exists():
                        packed=zlib.compress(data,1)
                        with q.open('xb') as w:w.write(packed)
                        new_bytes+=len(packed)
                    assert zlib.decompress(q.read_bytes())==data
                    parts.append(h);chunks.add(h)
            record=dict(path=str(p.resolve()),sha256=full.hexdigest(),bytes=size,chunks=parts);rows.append(record);inodes[identity]=record
    put(manifest,dict(schema=1,compression='zlib',chunk_size=1024*1024,files=rows,unique_chunks=len(chunks),new_storage_bytes=new_bytes,logical_bytes=sum(x['bytes'] for x in rows),reason='completed payloads archived losslessly; all capture manifests, hashes, prefixes, and qualification receipts remain directly available'))
    allowed=[p.resolve() for p in bases];removed=[];verified=set()
    for r in rows:
        p=Path(r['path']);assert any(p.is_relative_to(base) for base in allowed);s=p.stat();identity=(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns);assert identity in inodes
        if identity not in verified:assert sha(p)==r['sha256'];verified.add(identity)
        p.unlink();removed.append(str(p))
    # A CAS alias may be the last remaining full-file link. Remove only aliases
    # proven reconstructible above; other normalized hardlinks remain valid.
    pool=Path('D:/rtx184-cas').resolve()
    for h in {r['sha256'] for r in rows}:
        p=pool/h[:2]/h;assert p.is_relative_to(pool)
        if p.exists():assert sha(p)==h;p.unlink()
    put(STORE/(key+'-retirement.json'),dict(manifest_sha256=sha(manifest),removed_payload_paths=removed,capture_manifests_preserved=True))
    print('archived root',ix,'logical GB',sum(x['bytes'] for x in rows)/2**30,'new stored GB',new_bytes/2**30,flush=True)
def restore(ix):
    m=json.loads((STORE/(ix+'.json')).read_bytes())
    for r in m['files']:
        p=Path(r['path']);assert any(p.resolve().is_relative_to(Path(b).resolve()) for b in ('D:/rtx184-runs','D:/rtx184-qualification'))
        if p.exists():assert sha(p)==r['sha256'];continue
        p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:
            for h in r['chunks']:
                data=zlib.decompress((STORE/'chunks'/h[:2]/h).read_bytes());assert hashlib.sha256(data).hexdigest()==h;f.write(data)
        assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256']
if __name__=='__main__':
    if sys.argv[1]=='restore':restore(sys.argv[2])
    else:archive(int(sys.argv[2]),sys.argv[1]=='normalized')
