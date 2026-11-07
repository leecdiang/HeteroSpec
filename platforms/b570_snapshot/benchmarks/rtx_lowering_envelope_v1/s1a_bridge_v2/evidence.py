"""CPU-only lossless raw package/fresh restore, separate from owned GPU stage."""
import argparse,hashlib,json,zipfile
from pathlib import Path,PurePosixPath
from common import V,load,save,sha
ESSENTIAL=('F0.json','PLAN.json','REFERENCE_INDEX.json','CPU_GRAPH_EXPECTED.json','ABI_EXPORTS.json',
    'analyzer.py','raw_math.py','common.py','native_formal.cpp','formal_gate.h','hs113_graph.h','core_gate.h','lowering113_formal.exe',
    'readiness_policy.py','READINESS_REVIEW.md','run_bridge.py','bounded.py','lifecycle.py','cpu_job.py','evidence.py','offline.py','AMENDMENT.md','BUDGET_FINAL.json','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json')

def package(root,out,frozen=V):
    root=Path(root);out=Path(out);assert not out.exists()
    members=[(p,'raw/'+p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file()]
    members += [(Path(frozen)/n,'frozen/'+n) for n in ESSENTIAL]
    assert sum(p.stat().st_size for p,n in members if n.startswith('frozen/'))<=16*1024**2
    manifest={n:dict(bytes=p.stat().st_size,sha256=sha(p)) for p,n in members}
    out.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,n in members:
            assert not p.is_symlink();z.write(p,n)
        z.writestr('MANIFEST.json',json.dumps(manifest,sort_keys=True,separators=(',',':'))+'\n')
    return dict(archive_sha256=sha(out),archive_bytes=out.stat().st_size,members=len(manifest))

def restore(archive,out):
    out=Path(out);assert not out.exists();out.mkdir(parents=True)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();assert len(names)==len(set(names)) and len(names)<30000
        assert sum(p.file_size for p in z.infolist())<512*1024**2,'restored raw/frozen byte cap'
        manifest=json.loads(z.read('MANIFEST.json'));assert set(names)==set(manifest)|{'MANIFEST.json'}
        for n in names:
            p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and '\\' not in n and ':' not in n
            dest=out/str(p);dest.resolve().relative_to(out.resolve());dest.parent.mkdir(parents=True,exist_ok=True)
            data=z.read(n)
            if n!='MANIFEST.json':assert len(data)==manifest[n]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[n]['sha256']
            with dest.open('xb') as f:f.write(data)
    return dict(members_verified=len(manifest),archive_sha256=sha(archive),fresh_directory=str(out))

def main():
    p=argparse.ArgumentParser();p.add_argument('--action',choices=('package','restore'),required=True);p.add_argument('--root',type=Path);p.add_argument('--archive',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    r=package(a.root,a.output) if a.action=='package' else restore(a.archive,a.output)
    print(json.dumps(r))
if __name__=='__main__':main()
