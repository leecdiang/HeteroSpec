"""Pre-freeze calibration references and fixed-policy qualification only."""
from host import *
sys.path.insert(0,str(HERE.parents[1]/'tpds_prefix_reuse_v1'))
import study
def refs():
    rows=read(ROOT/'provisional-cohort.json')['calibration']
    for i,r in enumerate(rows):
        run(f'cal-r-{i:02}','oracle02',dict(mode='requests',capacity=4096,units=[dict(id=f'r{k}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm='R',cap=128,capture=True) for k in range(2)]),requests=2)
def qualify():
    rows=read(ROOT/'provisional-cohort.json')['calibration']
    for i,r in enumerate(rows):
        units=[dict(id=a+'-'+mode,tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=a,cap=128,capture=mode=='heavy',state=str(ROOT/f'cal-r-{i:02}/r0/prefix.bin')) for a in study.FIXED for mode in ('heavy','off')]
        run(f'cal-q-{i:02}','candidate02',dict(mode='requests',capacity=4096,units=units),requests=6)
def verify():
    proof=[]
    for i in range(12):
        ref=ROOT/f'cal-r-{i:02}/r0'; rr=read(ref/'receipt.json');v={p.name:sha(p) for p in ref.glob('*.f32')}
        for name,d in [('R-repeat',ROOT/f'cal-r-{i:02}/r1')]+[(a,ROOT/f'cal-q-{i:02}'/(a+'-heavy')) for a in study.FIXED]:
            r=read(d/'receipt.json');entry=dict(index=i,arm=name,vectors_equal=v=={p.name:sha(p) for p in d.glob('*.f32')},output_equal=rr['output']==r['output'],position_equal=rr['final_position']==r['final_position'],state_equal=sha(ref/'final.bin')==sha(d/'final.bin'),reference_vectors=v)
            if name!='R-repeat':entry['capture_off_equal']=r['output']==read(d.parent/(name+'-off')/'receipt.json')['output']
            proof.append(entry)
    put(ROOT/'calibration-qualification.json',proof)
    assert all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
if __name__=='__main__':
    for arg in sys.argv[1:]:globals()[arg]()
