from calibrate import *
def qualified(i,folder):
    ref=ROOT/f'cal-r-{i:02}/r0';rr=read(ref/'receipt.json');v={p.name:sha(p) for p in ref.glob('*.f32')};result=[]
    for arm in study.FIXED:
        heavy=folder/(arm+'-heavy');off=folder/(arm+'-off');h=read(heavy/'receipt.json');o=read(off/'receipt.json')
        result.append(dict(index=i,arm=arm,vectors_equal=v=={p.name:sha(p) for p in heavy.glob('*.f32')},output_equal=rr['output']==h['output']==o['output'],position_equal=rr['final_position']==h['final_position']==o['final_position'],state_equal=sha(ref/'final.bin')==sha(heavy/'final.bin'),physical_head=h['physical_dense_head'],vectors=v))
    return result
def qualify():
    rows=read(ROOT/'provisional-cohort.json')['calibration'];proof=[]
    for i,r in enumerate(rows):
        units=[dict(id=a+'-'+mode,tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=a,cap=128,capture=mode=='heavy',state=str(ROOT/f'cal-r-{i:02}/r0/prefix.bin')) for a in study.FIXED for mode in ('heavy','off')]
        d=run(f'cal-q04-{i:02}','candidate05',dict(mode='requests',capacity=4096,units=units),requests=6);proof+=qualified(i,d)
    put(ROOT/'calibration-qualification04.json',proof)
    assert all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
def cost():
    proof=read(ROOT/'calibration-qualification04.json');assert len(proof)==36 and all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
    rows=read(ROOT/'provisional-cohort.json')['calibration']
    for s in range(2):
        units=[]
        for i,r in enumerate(rows):
            for a in range(3):
                arm=study.FIXED[(i+s+a)%3]
                for kind in ('warmup','measure'):units.append(dict(id=f'i{i:02}/{arm}/{kind}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=arm,cap=128,capture=False,state=str(ROOT/f'cal-r-{i:02}/r0/prefix.bin')))
        run(f'cal-cost04-s{s}','candidate05',dict(mode='requests',capacity=4096,units=units),requests=72)
if __name__=='__main__':
    for arg in sys.argv[1:]:globals()[arg]()
