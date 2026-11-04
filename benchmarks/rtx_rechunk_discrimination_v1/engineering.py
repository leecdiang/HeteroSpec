"""Bounded pre-freeze controls on the already exposed synthetic input only."""
from host import *
import coverage
def main():
    tokens=[113+(i*173)%2309 for i in range(320)]
    def unit(name,arm,capture,state=None):
        x=dict(id=name,tokens=tokens,head=253,arm=arm,cap=8,capture=capture)
        if state:x['state']=str(state)
        return x
    ref=run('engineering-r',OLD/'oracle02',[unit('r0','R',True),unit('r1','R',True)],'engineering')
    for name,build in [('old',OLD/'candidate07'),('new',ROOT/'candidate01')]:
        run('engineering-'+name,build,[unit(a+'/'+k,a,k=='heavy',ref/'r0/prefix.bin') for a in coverage.ARMS for k in ('heavy','off')],'engineering')
    rr=read(ref/'r0/receipt.json');v={p.name:sha(p) for p in (ref/'r0').glob('*.f32')};proof=[]
    targets=[('R-repeat',ref/'r1')]+[(epoch+'/'+a,ROOT/('engineering-'+epoch)/a/'heavy') for epoch in ('old','new') for a in coverage.ARMS]
    for name,p in targets:
        r=read(p/'receipt.json');off=r if name=='R-repeat' else read(p.parent/'off/receipt.json')
        row=dict(name=name,vectors_equal=v=={f.name:sha(f) for f in p.glob('*.f32')},state_equal=sha(ref/'r0/final.bin')==sha(p/'final.bin'),endpoint_equal=rr['output']==r['output']==off['output'],position_equal=rr['final_position']==r['final_position']==off['final_position'],heavy_service_s=r['service_s'],off_service_s=off['service_s'],heavy_observer_io_s=r['observer_io_s'])
        if name.startswith('new/'):
            for raw in (r,off):assert abs(raw['service_s']-sum(raw[k] for k in ('lookup_import_ready_s','append_execution_s','continuation_s')))<1e-8
        proof.append(row)
    put(ROOT/'ENGINEERING_CONTROLS.json',dict(requests=14,scope='Previously exposed synthetic H253/append67/cap8 only. Observed heavy/off windows and logged dump I/O are retained; no claim that their difference isolates clock overhead. All formal timings are capture-off with identical phase instrumentation.',proof=proof))
    assert all(all(v for k,v in x.items() if k.endswith('_equal')) for x in proof)
    print('engineering controls passed; 14 requests charged')
if __name__=='__main__':main()
