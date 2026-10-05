"""Restore content-addressed experiment files without overwriting other bytes."""
import argparse,hashlib,json,zipfile
from pathlib import Path

def main():
    ap=argparse.ArgumentParser();ap.add_argument('archive',type=Path);ap.add_argument('destination',type=Path);a=ap.parse_args()
    root=a.destination.resolve();root.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(a.archive) as z:
        index=json.loads(z.read('INDEX.json'))
        for entry in index['files']:
            p=(root/entry['path']).resolve();assert p.is_relative_to(root), 'Unsafe archive path'
            b=z.read('objects/'+entry['sha256']);assert len(b)==entry['bytes'] and hashlib.sha256(b).hexdigest()==entry['sha256']
            if p.exists():assert p.is_file() and p.read_bytes()==b, 'Existing different file: '+str(p)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    print('Restored '+str(len(index['files']))+' verified files.')

if __name__=='__main__':main()
