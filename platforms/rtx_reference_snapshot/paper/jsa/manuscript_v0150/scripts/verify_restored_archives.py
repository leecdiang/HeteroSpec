#!/usr/bin/env python3
"""Restore every indexed logical file and verify its digest, including nested ZIPs.
This performs byte verification only; independent scientific auditors run separately.
"""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[1];STAGE=ROOT/'output/raw_restore'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def safe(name):
    p=PurePosixPath(name)
    assert not p.is_absolute() and '..' not in p.parts and '\\' not in name and ':' not in name,name
    return p

def inspect(z):
    names=z.namelist();assert len(names)==len(set(names))
    for n in names:safe(n)
    if 'MANIFEST.json' in names:
        raw=z.read('MANIFEST.json');m=json.loads(raw);rows=m['files'];assert len(rows)==m['logical_files']
        assert len({r['sha256'] for r in rows})==m['unique_objects']
        assert set(names)=={'MANIFEST.json'}|{'objects/'+r['sha256'] for r in rows}
        entries=[(r['path'],'objects/'+r['sha256'],r) for r in rows]
    else:
        raw=z.read('INDEX.json');m=json.loads(raw);rows=m['files'];assert isinstance(rows,dict)
        assert set(names)==set(rows)|{'INDEX.json'}
        entries=[(n,n,r) for n,r in rows.items()]
    assert len(entries)==len({n.casefold() for n,_,r in entries})
    for n,_,r in entries:safe(n)
    return raw,entries

def verify_zip(p,dest=None):
    with zipfile.ZipFile(p) as z:
        raw,entries=inspect(z);checked={}
        for name,member,r in entries:
            if member not in checked:
                h=hashlib.sha256();size=0
                target=dest/name if dest else None
                if target:target.parent.mkdir(parents=True,exist_ok=True)
                f=target.open('xb') if target else None
                try:
                    with z.open(member) as source:
                        for b in iter(lambda:source.read(1024*1024),b''):
                            h.update(b);size+=len(b)
                            if f:f.write(b)
                finally:
                    if f:f.close()
                checked[member]=(h.hexdigest(),size,target)
            digest,size,original=checked[member]
            assert digest==r['sha256'] and size==r['bytes'],name
            if dest and original!=dest/name:
                q=dest/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original,q)
        if dest:
            for name,_,r in entries:
                q=dest/name;assert q.stat().st_size==r['bytes'] and sha(q)==r['sha256'],name
    return dict(logical_files=len(entries),unique_members=len(checked),logical_bytes=sum(r['bytes'] for _,_,r in entries),index_sha256=hashlib.sha256(raw).hexdigest())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--archive');args=parser.parse_args()
    source=json.loads((ROOT/'review_access/RAW_ARCHIVE_ACCESS.json').read_text());results=[]
    if args.archive:source['archives']=[a for a in source['archives'] if a['id']==args.archive];assert source['archives']
    for a in source['archives']:
        base=STAGE/a['id'];p=base/'archive.zip'
        assert p.stat().st_size==a['archive_bytes'] and sha(p)==a['archive_sha256']
        with zipfile.ZipFile(p) as z:raw,entries=inspect(z)
        need=sum(r['bytes'] for _,_,r in entries)
        dest=base/'restored';receipt=base/'RESTORE_VERIFICATION.json'
        if dest.exists():
            assert {p.relative_to(dest).as_posix() for p in dest.rglob('*') if p.is_file()}=={n for n,_,r in entries},'Unexpected restored file set'
            assert not any(p.is_symlink() for p in dest.rglob('*'))
            for n,_,r in entries:assert (dest/n).stat().st_size==r['bytes'] and sha(dest/n)==r['sha256'],n
            if receipt.exists():
                result=json.loads(receipt.read_text());results.append(result);continue
        assert shutil.disk_usage(STAGE).free>need+1024**3,('Insufficient space',a['id'],need)
        already=dest.exists()
        if not already:dest.mkdir()
        result=dict(id=a['id'],archive_sha256=a['archive_sha256'],**verify_zip(p,None if already else dest))
        expected=list((ROOT/'output/review_access_stage/evidence'/a['id']).rglob('ARCHIVE_MANIFEST.json'))
        if a['id'].startswith('b570'):
            assert len(expected)==1
            public=expected[0].read_bytes()
            assert public.replace(b'\r\n',b'\n')==raw.replace(b'\r\n',b'\n'),'Manifest mismatch beyond line endings'
            result['repository_manifest_sha256']=hashlib.sha256(public).hexdigest()
            result['embedded_manifest_byte_equal_to_repository']=public==raw
            result['manifest_line_endings_only_difference']=public!=raw
        nested=[]
        for q in dest.rglob('*.zip'):
            with zipfile.ZipFile(q) as z:names=z.namelist();assert z.testzip() is None
            if 'INDEX.json' in names or 'MANIFEST.json' in names:
                rel=q.relative_to(dest).as_posix()
                try:nested.append(dict(path=rel,status="PASS_INDEXED_BYTES",**verify_zip(q)))
                except AssertionError:
                    assert a['id']=='rtx98' and rel=='local/CPU_DIAGNOSTIC/corrupt.zip'
                    control=json.loads((q.parent/'RECEIPT.json').read_bytes())
                    assert control['scope']=='SYNTHETIC CPU archive controls only; no scientific observations' and control['corrupted_member_rejected'] is True
                    nested.append(dict(path=rel,status="EXPECTED_REJECTION_SYNTHETIC_CORRUPTION_CONTROL",sha256=sha(q),evidence_receipt='local/CPU_DIAGNOSTIC/RECEIPT.json',scientific_observation=False))
        result.update(status='PASS_FULL_LOGICAL_FILE_RESTORE_AND_SHA256',nested_indexed_archives=nested,new_GPU_forwards=0)
        receipt.write_text(json.dumps(result,indent=2)+'\n');results.append(result);print(json.dumps(result),flush=True)
    report=dict(date='2026-10-13',scope='Six manuscript primary archives, including indexed nested source/runtime and inherited evidence. External model weights and old campaigns outside these manifests are not downloaded.',archives=results,total_top_level_logical_files=sum(r['logical_files'] for r in results),total_top_level_logical_bytes=sum(r['logical_bytes'] for r in results),new_GPU_forwards=0,scientific_rederivation='Recorded separately; byte integrity does not imply scientific validity.')
    if not args.archive:(ROOT/'review_access/RAW_RESTORE_VERIFICATION.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
