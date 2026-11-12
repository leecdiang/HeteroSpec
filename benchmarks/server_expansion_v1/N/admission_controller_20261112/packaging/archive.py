"""Explicit public text archive and strict CPU replay. Never touches CUDA."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile
from support import digest_value, fresh, need, read, safe_relative, sha


def blob_hash(value):
    return hashlib.sha256(value).hexdigest()


def create(root, selection, output):
    root=Path(root).resolve();output=Path(output)
    need(not output.exists(), 'Archive already exists')
    need(selection['schema']=='hs.strong.public-selection.v1', 'Selection schema')
    need(selection['terminal_status'] in ('COMPLETE','FAILED','PARTIAL','NOT_ADMITTED'),
         'Refuse export of an active/unknown attempt')
    entries=[];payloads={};casefold=set()
    for item in selection['files']:
        name=safe_relative(item['path']).as_posix()
        need(name!='INDEX.json' and name.casefold() not in casefold, 'Archive filename collision')
        casefold.add(name.casefold())
        path=root/name
        need(path.resolve().is_relative_to(root) and not path.is_symlink(), 'Symlink/outside source')
        need(item['public_review']=='TEXT_REVIEWED_NO_PRIVATE_IDENTIFIERS', 'Unreviewed public payload')
        need(item['payload_kind']=='utf8-text', 'Numeric/weight payload not authorized for public archive')
        value=path.read_bytes();value.decode('utf-8',errors='strict')
        need(blob_hash(value)==digest_value(item['sha256']) and len(value)==item['bytes'],
             'Selection bytes changed after public review')
        for forbidden in selection.get('private_literals',[]):
            need(forbidden and forbidden.encode() not in value, 'Private identifier in public text')
        entries.append({k:item[k] for k in ('path','sha256','bytes','payload_kind')})
        payloads[name]=value
    withheld=[]
    for item in selection.get('withheld_numeric_payloads',[]):
        digest_value(item['sha256'])
        need(type(item['bytes']) is int and item['bytes']>0, 'Withheld payload size')
        withheld.append(dict(logical_id=item['logical_id'],sha256=item['sha256'],bytes=item['bytes'],
                             publicly_available=False))
    index=dict(schema='hs.strong.public-archive.v1',terminal_status=selection['terminal_status'],
               files=sorted(entries,key=lambda e:e['path']),withheld_numeric_payloads=withheld,
               public_replay_scope='public_text_only_not_independent_numeric_GPU_validation')
    payloads['INDEX.json']=(json.dumps(index,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    # Fixed metadata makes identical reviewed inputs produce identical bytes.
    with output.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',filename='',mtime=0) as gz:
            with tarfile.open(fileobj=gz,mode='w|',format=tarfile.USTAR_FORMAT) as tf:
                for name,value in sorted(payloads.items()):
                    t=tarfile.TarInfo(name);t.size=len(value);t.mode=0o644;t.mtime=0
                    tf.addfile(t,io.BytesIO(value))
    return dict(archive_sha256=sha(output),archive_bytes=output.stat().st_size,
                payload_files=len(entries),index_sha256=blob_hash(payloads['INDEX.json']))


def replay(archive, output, expected_sha256, max_payload_bytes=2_000_000_000):
    need(sha(archive)==digest_value(expected_sha256), 'Archive transport hash mismatch')
    output=Path(output);need(not output.exists(),'Replay requires a fresh directory')
    seen=set();payloads={};total=0
    with tarfile.open(archive,'r:gz') as tf:
        for member in tf:
            name=safe_relative(member.name).as_posix()
            need(member.isfile() and name.casefold() not in seen,'Duplicate/link/non-file archive member')
            seen.add(name.casefold());total+=member.size
            need(0<=member.size<=max_payload_bytes and total<=max_payload_bytes,'Archive payload limit')
            f=tf.extractfile(member);need(f is not None,'Missing payload')
            value=f.read(member.size+1);need(len(value)==member.size,'Truncated payload')
            payloads[name]=value
    need('INDEX.json' in payloads,'Missing archive index')
    index=json.loads(payloads['INDEX.json'])
    need(index['schema']=='hs.strong.public-archive.v1','Archive index schema')
    names=[e['path']for e in index['files']]
    need(len(names)==len(set(names)) and set(payloads)==set(names)|{'INDEX.json'},
         'Missing/extra fragment or duplicate index path')
    for e in index['files']:
        safe_relative(e['path']);value=payloads[e['path']]
        need(len(value)==e['bytes'] and blob_hash(value)==digest_value(e['sha256']),
             'Archive payload hash/size mismatch')
        need(e['payload_kind']=='utf8-text','Unexpected public payload kind')
        value.decode('utf-8',errors='strict')
    # Verify the complete archive before writing any restored file.
    output.mkdir(parents=True)
    for name,value in sorted(payloads.items()):
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True)
        with p.open('xb') as f:f.write(value)
    return dict(status='PUBLIC_TEXT_BYTES_RESTORED',files=len(names),
                independent_numeric_GPU_validation='NOT_RUN',
                unavailable_numeric_payloads=len(index['withheld_numeric_payloads']))


def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True)
    c=sub.add_parser('create');c.add_argument('--root',required=True)
    c.add_argument('--selection',required=True);c.add_argument('--out',required=True)
    r=sub.add_parser('replay');r.add_argument('--archive',required=True)
    r.add_argument('--sha256',required=True);r.add_argument('--out',required=True)
    a=p.parse_args()
    result=create(a.root,read(a.selection),a.out) if a.mode=='create' else replay(a.archive,a.out,a.sha256)
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
