"""Content-addressed raw bundle; offline reconstruction without model or GPU."""
from audit import *
import zipfile,sys
from analyze import compute
def pack(out):
    index={};seen=set()
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        paths=[(p,p.relative_to(ROOT).as_posix()) for p in ROOT.rglob('*') if p.is_file() and p.suffix in ('.json','.log','.f32','.bin')]
        paths += [(p,'source/'+p.name) for p in HERE.iterdir() if p.suffix in ('.py','.cpp','.diff','.md')]
        paths += [(ROOT/'candidate01/worker.exe','candidate01/worker.exe')]
        for p,name in sorted(paths,key=lambda x:x[1]):
            h=sha(p);index[name]=dict(sha256=h,size=p.stat().st_size)
            if h not in seen:z.write(p,'blobs/'+h);seen.add(h)
        z.writestr('index.json',json.dumps(index,sort_keys=True))
    put(ROOT/'ARCHIVE.json',dict(sha256=sha(out),bytes=out.stat().st_size,logical_files=len(index),unique_blobs=len(seen)))
def verify(path):
    with zipfile.ZipFile(path) as z:
        ix=json.loads(z.read('index.json'));seen=set()
        for r in ix.values():
            if r['sha256'] in seen:continue
            with z.open('blobs/'+r['sha256']) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==r['sha256']
            seen.add(r['sha256'])
        def get(p):return json.loads(z.read('blobs/'+ix[p]['sha256']))
        def vectors(d):return {p[len(d):]:r['sha256'] for p,r in ix.items() if p.startswith(d) and p.endswith('.f32')}
        freeze=get('FREEZE.json')
        for p,h in freeze['files'].items():assert ix[p]['sha256']==h
        for p,h in freeze['sources'].items():assert ix['source/'+p]['sha256']==h
        assert ix['candidate01/worker.exe']['sha256']==get('candidate01/binding.json')['exe']
        n=0;panel=get('coverage.json')['selected']
        for i in range(8):
            ref=f'science-r-{i:02}/r0/';r=get(ref+'receipt.json');v=vectors(ref);assert len(v)==len(r['output'])
            for d in [f'science-r-{i:02}/r1/']+[f'science-qualification/{i:02}/{a}/heavy/' for a in ('QB','WB-cut','WB-rechunk')]:
                assert vectors(d)==v and ix[d+'final.bin']['sha256']==ix[ref+'final.bin']['sha256']
                rr=get(d+'receipt.json');assert rr['output']==r['output'] and rr['final_position']==r['final_position'];n+=1
            for p in ix:
                if not p.endswith('/receipt.json'):continue
                if not (p.startswith(f'science-qualification/{i:02}/') or any(p.startswith(f'science-session-{s}/{i:02}/') for s in range(2))):continue
                c=get(p);assert c['output']==r['output'] and c['pending_token']==r['pending_token'] and c['final_position']==r['final_position']
                assert [[x['head'],x['width']] for x in c['calls']]==panel[i]['plans'][c['arm']]
                assert abs(c['service_s']-sum(c[k] for k in ('lookup_import_ready_s','append_execution_s','continuation_s')))<1e-8
        assert compute(get)==get('ANALYSIS.json')
        launches=[get(p) for p in ix if p.endswith('/launch.json')];assert sum(x['requests'] for x in launches)==174
        return dict(status='ARCHIVE_ONLY_RECONSTRUCTION_PASS',files=len(ix),unique_blobs=len(seen),full_vector_state_comparisons=n,scientific_requests=160,all_stage_requests=174,measurements=48,paired_analysis_reconstructed=True,native_replication=False)
if __name__=='__main__':
    if sys.argv[1]=='pack':pack(Path(sys.argv[2]))
    else:print(json.dumps(verify(Path(sys.argv[2])),indent=2))
