from calibrate import *
def qualified(i,folder):
    ref=ROOT/f'common-r-{i:02}/r0';rr=read(ref/'receipt.json');v={p.name:sha(p) for p in ref.glob('*.f32')};result=[]
    for arm in study.FIXED:
        heavy=folder/(arm+'-heavy');off=folder/(arm+'-off');h=read(heavy/'receipt.json');o=read(off/'receipt.json')
        result.append(dict(index=i,arm=arm,vectors_equal=v=={p.name:sha(p) for p in heavy.glob('*.f32')},output_equal=rr['output']==h['output']==o['output'],position_equal=rr['final_position']==h['final_position']==o['final_position'],state_equal=sha(ref/'final.bin')==sha(heavy/'final.bin'),physical_head=h['physical_dense_head'],vectors=v))
    return result
def qualify():
    rows=read(ROOT/'common-cohort.json')['calibration'];proof=[]
    for i,r in enumerate(rows):
        units=[dict(id=a+'-'+mode,tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=a,cap=128,capture=mode=='heavy',state=str(ROOT/f'common-r-{i:02}/r0/prefix.bin')) for a in study.FIXED for mode in ('heavy','off')]
        d=run(f'common-q-{i:02}','candidate07',dict(mode='requests',capacity=4096,units=units),requests=6);proof+=qualified(i,d)
    put(ROOT/'COMMON_CALIBRATION_QUALIFICATION.json',proof)
    assert all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
def cost():
    proof=read(ROOT/'COMMON_CALIBRATION_QUALIFICATION.json');assert len(proof)==36 and all(all(v for k,v in r.items() if k.endswith('equal')) for r in proof)
    rows=read(ROOT/'common-cohort.json')['calibration']
    for s in range(2):
        units=[]
        for i,r in enumerate(rows):
            for a in range(3):
                arm=study.FIXED[(i+s+a)%3]
                for kind in ('warmup','measure'):units.append(dict(id=f'i{i:02}/{arm}/{kind}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm=arm,cap=128,capture=False,state=str(ROOT/f'common-r-{i:02}/r0/prefix.bin')))
        run(f'common-cost-s{s}','candidate07',dict(mode='requests',capacity=4096,units=units),requests=72)
def references():
    cohort=read(ROOT/'common-cohort.json')
    for link,r in zip(cohort['reference_reuse'],cohort['calibration']):
        i=link['index'];out=ROOT/f'common-r-{i:02}'
        if link['previous_index'] is not None:
            old=Path(link['original_reference']);inputs=read(old/'input.json')['units']
            assert all(u['tokens']==r['request_ids'] and u['head']==study.lcp(r['cached_ids'],r['request_ids']) for u in inputs)
            out.mkdir()
            for role in ('r0','r1'):
                previous='r'+str(int(role[-1]))
                shutil.copytree(old/previous,out/role,copy_function=os.link)
            put(out/'REUSED_ORIGINAL_REFERENCE.json',dict(source=str(old),reference_native=read(old/'launch.json')['exe'],reason='exact same input tokens, head, capacity, output flags and immutable scalar original; no new R replaces old R'))
        else:
            run(f'common-r-{i:02}','oracle02',dict(mode='requests',capacity=4096,units=[dict(id=f'r{k}',tokens=r['request_ids'],head=study.lcp(r['cached_ids'],r['request_ids']),arm='R',cap=128,capture=True) for k in range(2)]),requests=2)
if __name__=='__main__':
    for arg in sys.argv[1:]:globals()[arg]()
