"""Restore a bounded CAS archive and verify every object before writing."""
import argparse,json,hashlib,zipfile
from pathlib import Path,PurePosixPath
def restore(archive,destination):
    root=Path(destination).resolve();root.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        index=json.loads(z.read('INDEX.json'));assert index['schema']=='heterospec.jsa.cas.v1'
        for entry in index['files']:
            rel=PurePosixPath(entry['path']);assert not rel.is_absolute() and '..' not in rel.parts and not any(':' in s for s in rel.parts)
            p=root.joinpath(*rel.parts);assert p.resolve().is_relative_to(root)
            b=z.read('objects/'+entry['sha256']);assert len(b)==entry['bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    return {'files':len(index['files']),'unique_objects':len({e['sha256'] for e in index['files']}),'index_sha256':hashlib.sha256(json.dumps(index,sort_keys=True).encode()).hexdigest()}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('archive');p.add_argument('destination');a=p.parse_args();print(json.dumps(restore(a.archive,a.destination)))
