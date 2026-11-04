"""Content-addressed raw archive and independent archive-only reconstruction."""
from host import *
import zipfile
def pack(filename='raw-evidence.zip',receipt='raw-archive.json'):
    delivery=Path('F:/rtx172-delivery');delivery.mkdir(exist_ok=True)
    out=delivery/filename;index={};unique=set()
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file() or p.suffix not in ('.json','.jsonl','.log','.f32','.bin','.cpp') or p.name=='archive-verification.json':continue
            h=sha(p);index[p.relative_to(ROOT).as_posix()]=dict(sha256=h,size=p.stat().st_size)
            if h not in unique:z.write(p,'blobs/'+h);unique.add(h)
        z.writestr('index.json',json.dumps(index,sort_keys=True))
    put(ROOT/receipt,dict(sha256=sha(out),bytes=out.stat().st_size,logical_files=len(index),unique_blobs=len(unique)))
def verify(path):
    with zipfile.ZipFile(path) as z:
        index=json.loads(z.read('index.json'));verified=set()
        for r in index.values():
            if r['sha256'] in verified:continue
            with z.open('blobs/'+r['sha256']) as f:h=hashlib.file_digest(f,'sha256').hexdigest()
            assert h==r['sha256'];verified.add(h)
        def get(p):return json.loads(z.read('blobs/'+index[p]['sha256']))
        def vectors(prefix):return {p[len(prefix):]:r['sha256'] for p,r in index.items() if p.startswith(prefix) and p.endswith('.f32')}
        comparisons=0
        for i in range(12):
            ref=f'cal-r-{i:02}/r0/';r=get(ref+'receipt.json');v=vectors(ref);assert len(v)==len(r['output'])
            for d in [f'cal-r-{i:02}/r1/']+[f'{epoch}-{i:02}/{a}-heavy/' for epoch in ('cal-q','cal-q04','cal-q07') for a in ('QB','WB-cut','WB-rechunk')]:
                if d+'receipt.json' not in index:continue # retained interrupted engineering slot
                assert vectors(d)==v;assert index[d+'final.bin']['sha256']==index[ref+'final.bin']['sha256'];c=get(d+'receipt.json');assert c['output']==r['output'] and c['final_position']==r['final_position'];comparisons+=1
        for phase,count,arms in [('common',12,('QB','WB-cut','WB-rechunk')),('main',32,('QB','WB-cut','WB-rechunk','AUTO')),('aligned',8,('QB','WB-cut','WB-rechunk'))]:
            for i in range(count):
                ref=f'{phase}-r-{i:02}/'+('R-r0/' if phase=='aligned' else 'r0/');r=get(ref+'receipt.json');v=vectors(ref)
                repeat=f'{phase}-r-{i:02}/'+('R-r1/' if phase=='aligned' else 'r1/')
                rr=get(repeat+'receipt.json')
                assert vectors(repeat)==v and index[repeat+'final.bin']['sha256']==index[ref+'final.bin']['sha256']
                assert rr['output']==r['output'] and rr['final_position']==r['final_position']
                for a in arms:
                    d=f'main-q-session/i{i:02}/{a}/heavy/' if phase=='main' else f'{phase}-q-{i:02}/'+a+'-heavy/'
                    assert vectors(d)==v and index[d+'final.bin']['sha256']==index[ref+'final.bin']['sha256']
                    c=get(d+'receipt.json');assert c['output']==r['output'] and c['final_position']==r['final_position']
                    off=d.replace('/heavy/','/off/') if phase=='main' else d.replace('-heavy/','-off/')
                    o=get(off+'receipt.json');assert o['output']==r['output'] and o['final_position']==r['final_position'];comparisons+=1
        records=get('COMMON_CALIBRATION.json')['records'];assert len(records)==144
        normalized=get('results.json');formal=normalized['records'];assert len(formal)==1024
        panel=get('common-panel.json');ids={r['id']:i for i,r in enumerate(panel['test'])}
        for row in formal:
            p=f"main-cost-s{row['session']}/i{ids[row['id']]:02}/{row['arm']}/{row['kind']}/receipt.json";r=get(p);assert r['service_s']==row['seconds']
        sys.path.insert(0,str(HERE.parents[1]/'tpds_prefix_reuse_v1'))
        import study
        recomputed=study.analyze(normalized,panel);assert recomputed==get('analysis.json')
        ledger=[get(p) for p in index if p.endswith('/launch.json')]
        result=dict(status='ARCHIVE_ONLY_RECONSTRUCTION_PASS',files=len(index),unique_blobs=len(verified),vector_state_comparisons=comparisons,calibration_slots=len(records),requests_started=sum(x['requests'] for x in ledger),formal_measurements=512,formal_warmups=512,bootstrap_reconstructed=True,not_third_party_native_replication=True)
        print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    if sys.argv[1]=='pack':pack()
    else:verify(Path(sys.argv[2]))
