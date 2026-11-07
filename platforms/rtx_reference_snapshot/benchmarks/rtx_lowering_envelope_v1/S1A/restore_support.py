"""Restore authenticated support-only bytes and rederive every node predicate on CPU."""
import argparse, hashlib, importlib.util, json, zipfile
from pathlib import Path, PurePosixPath

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser()
    for name in ('archive','manifest','destination','analysis','commit','receipt'):p.add_argument('--'+name,required=True)
    a=p.parse_args(); archive=Path(a.archive); manifest=json.loads(Path(a.manifest).read_bytes())
    assert archive.stat().st_size==manifest['bytes'] and sha(archive)==manifest['sha256']
    root=Path(a.destination);root.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:
        names=z.namelist();assert len(names)==len(set(names))==len(manifest['members'])
        assert set(names)=={x['path'] for x in manifest['members']}
        for name in names:
            pp=PurePosixPath(name);assert not pp.is_absolute() and '..' not in pp.parts and ':' not in name and '\\' not in name
        z.extractall(root)
    for item in manifest['members']:
        f=root/item['path'];assert f.stat().st_size==item['bytes'] and sha(f)==item['sha256']
    spec=importlib.util.spec_from_file_location('restored_analysis',root/'code/analyze_support.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    report=mod.reconstruct(root)
    assert report==json.loads(Path(a.analysis).read_bytes()),'all rederived CPU analysis values must match'
    with (root/'RECOMPUTED_ANALYSIS.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
    assert (root/'RECOMPUTED_ANALYSIS.json').read_bytes()==Path(a.analysis).read_bytes()
    receipt=dict(status='PASS',authenticated_commit=a.commit,archive_sha256=manifest['sha256'],members_verified=len(manifest['members']),
                 complete_graphs=report['selection']['complete_graphs'],support_API_queries=report['support_API_queries'],
                 selection=report['selection']['selected_QH'],full_analysis_bytes_equal=True,destination=str(root),
                 new_GPU_initializations=0,new_graph_computes=0,new_model_requests=0,new_device_queries=0,
                 scope='CPU reconstruction from retained complete native support predicates, not repeated science or an external audit')
    with Path(a.receipt).open('x',encoding='utf-8',newline='\n') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
