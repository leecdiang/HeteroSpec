"""Verify content inventory and Git checkpoint object identities, then scientific evidence."""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

def tree_entry(data,name):
    offset=0
    while offset<len(data):
        end=data.index(b'\0',offset);label=data[offset:end].split(b' ',1)[1].decode('utf-8');oid=data[end+1:end+21].hex()
        if label==name:return oid
        offset=end+21
    raise ValueError('Missing Git tree path: '+name)

def main(root):
    root=Path(root);inventory=json.loads((root/'SHA256_INVENTORY.json').read_text(encoding='utf-8'))
    for rel,expected in inventory['files'].items():
        actual=hashlib.file_digest((root/rel).open('rb'),'sha256').hexdigest()
        if actual!=expected:raise ValueError('Included bytes mismatch: '+rel)
    proof=json.loads((root/'provenance/git_checkpoints.json').read_text(encoding='utf-8'));objects=root/'provenance/git_objects'
    def check(oid,kind):
        data=(objects/oid).read_bytes()
        if hashlib.sha1((kind+' '+str(len(data))+'\0').encode()+data).hexdigest()!=oid:raise ValueError('Git object mismatch: '+oid)
        return data
    for oid,commit in proof['commits'].items():
        data=check(oid,'commit');lines=data.decode('utf-8').splitlines()
        if lines[0]!='tree '+commit['tree'] or [line.split()[1] for line in lines if line.startswith('parent ')]!=commit['parents']:raise ValueError('Commit metadata mismatch')
        for rel,record in commit['files'].items():
            tree=commit['tree']
            for part in rel.split('/')[:-1]:tree=tree_entry(check(tree,'tree'),part)
            blob=tree_entry(check(tree,'tree'),rel.split('/')[-1])
            if blob!=record['blob']:raise ValueError('Checkpoint file not in committed tree')
            check(blob,'blob')
    print('Included byte inventory and Git checkpoint objects: PASS')
    return subprocess.run([sys.executable,str(root/'scripts/platform/b570_mechanism_v08/verify.py'),'--root',str(root)]).returncode

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);args=parser.parse_args();raise SystemExit(main(args.root))
