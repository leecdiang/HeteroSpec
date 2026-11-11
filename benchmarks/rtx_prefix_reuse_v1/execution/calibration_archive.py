"""Archive-only calibration reconstruction, including actual heavy/off controls."""
from host import *
import zipfile
def verify(path):
    with zipfile.ZipFile(path) as z:
        index=json.loads(z.read('index.json'));seen=set()
        assert not any(p.startswith('main-') for p in index),'not a pre-test archive'
        for r in index.values():
            h=r['sha256']
            if h in seen:continue
            with z.open('blobs/'+h) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==h
            seen.add(h)
        def get(p):return json.loads(z.read('blobs/'+index[p]['sha256']))
        def vectors(d):return {p[len(d):]:r['sha256'] for p,r in index.items() if p.startswith(d) and p.endswith('.f32')}
        comparisons=0;vector_comparisons=0
        for i in range(12):
            ref=f'common-r-{i:02}/r0/';rr=get(ref+'receipt.json');v=vectors(ref)
            for arm,d in [('R-repeat',f'common-r-{i:02}/r1/')]+[(a,f'common-q-{i:02}/{a}-heavy/') for a in ('QB','WB-cut','WB-rechunk')]:
                r=get(d+'receipt.json');assert vectors(d)==v and index[d+'final.bin']['sha256']==index[ref+'final.bin']['sha256'];assert r['output']==rr['output'] and r['final_position']==rr['final_position']
                if arm!='R-repeat':
                    off=get(f'common-q-{i:02}/{arm}-off/receipt.json');assert off['output']==rr['output'] and off['final_position']==rr['final_position']
                comparisons+=1;vector_comparisons+=len(v)
        cal=get('COMMON_CALIBRATION.json');assert len(cal['records'])==144
        panel=get('common-panel.json');ids={r['id']:i for i,r in enumerate(panel['calibration'])}
        for row in cal['records']:
            r=get(f"common-cost-s{row['session']}/i{ids[row['id']]:02}/{row['arm']}/{row['kind']}/receipt.json");assert row['seconds']==r['service_s']
        result=dict(status='RESTORED_ARCHIVE_CALIBRATION_PASS',sha256=sha(path),files=len(index),unique_blobs=len(seen),root_route_comparisons=comparisons,full_vector_comparisons=vector_comparisons,calibration_slots=144,main_exposure=0,native_replication=False)
        print(json.dumps(result,indent=2));return result
if __name__=='__main__':
    if sys.argv[1]=='pack':
        import archive;archive.pack('calibration-raw.zip','calibration-archive.json')
    else:verify(Path(sys.argv[2]))
