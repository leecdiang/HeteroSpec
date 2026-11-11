"""Recompute every registered warmup, measurement, endpoint and contrast."""
import collections, math
from confirmation import ARMS, REF, CAND, check_seal, slot
from execute import ROOT, read, write, sha
from prepare_pool import digest
from audit import unpack

CONTRASTS={'M_QB/M_PQ':('M_QB','M_PQ'),'C_QB/C_PQ':('C_QB','C_PQ'),
           'M_QB/C_QB':('M_QB','C_QB'),'M_QB/R':('M_QB','R'),'C_QB/R':('C_QB','R')}
def geometric(values):return math.exp(math.fsum(math.log(x) for x in values)/len(values))
def recompute():
    check_seal()
    panel=read(ROOT/'UNSEEN.json');by_id={k:i for i,k in enumerate(panel)}
    order=read(ROOT/'COST_ORDER.json')
    rows=[];blocks=collections.defaultdict(dict)
    for period in range(3):
        ordered=sorted(panel,key=lambda x:digest(['qwen-cost-v1',period,x]))
        for block,ident in enumerate(ordered):
            shift=(int(digest(ident)[:8],16)+period)%5
            for pos,offset in enumerate((0,1,4,2,3)):
                index=period*40+5*block+pos
                arm=ARMS[(offset+shift)%5]
                assert order[index]==dict(session=period,id=ident,arm=arm)
                unit=ROOT/f'units/cost-{index:03d}'
                job=read(unit/'JOB.json');receipt=read(unit/'RECEIPT.json');sup=read(unit/'SUPERVISOR.json');native=read(unit/'native/result.json')
                assert receipt['success'] and receipt['requests']==2 and sup['job_accounting']['active_processes']==0
                assert job['runtime_sha256']==sha(ROOT/(REF if arm=='R' else CAND)/'FILES.json')
                assert native['normal_cleanup_returned'] and len(native['requests'])==2
                reference=read(ROOT/f'units/qual-{by_id[ident]}-R/native/result.json')['requests'][0]
                q=reference if arm=='R' else read(ROOT/f'units/qual-{by_id[ident]}-candidate/native/result.json')['requests'][ARMS.index(arm)-1]
                times=[]
                for i,stage in enumerate(('warmup','measured')):
                    s=job['slots'][i];r=native['requests'][i]
                    assert s==slot(panel[ident],arm,stage,clean=True) and r['slot_id']==s['slot_id'] and r['prompt_ids_sha256']==s['prompt_ids_sha256']
                    assert r['endpoint']==reference['endpoint'] and r['cycles']==q['cycles']
                    assert r['performance_eligible'] and not r['vectors'] and not r['target_caller_trace'] and not r['geometry_files'] and 'phase_seconds' not in r
                    unpack(r);times.append(r['service_seconds']);assert times[-1]>0 and math.isfinite(times[-1])
                process=sup['charged_seconds'];load=native['model_load_seconds']
                assert process+0.1>=sum(times)+load
                rows.append(dict(session=period,input=ident,arm=arm,warmup_seconds=times[0],measured_seconds=times[1],model_load_seconds=load,process_seconds=process,other_process_seconds=process-load-sum(times),host_owned_seconds=receipt['owned_seconds']))
                blocks[period,ident][arm]=times[1]
    assert len(rows)==120 and len(blocks)==24
    comparisons={}
    for label,(a,b) in CONTRASTS.items():
        ratios=[dict(session=k[0],input=k[1],ratio=v[a]/v[b]) for k,v in blocks.items()]
        comparisons[label]=dict(ratio=geometric([x['ratio'] for x in ratios]),sessions=[geometric([x['ratio'] for x in ratios if x['session']==s]) for s in range(3)],blocks_above_one=sum(x['ratio']>1 for x in ratios),blocks_below_one=sum(x['ratio']<1 for x in ratios),blocks=ratios)
    qualification=[read(p) for p in (ROOT/'units').glob('qual-*/RECEIPT.json')]
    preparation=dict(qualification_requests=sum(x['requests'] for x in qualification),qualification_host_owned_seconds=sum(x['owned_seconds'] for x in qualification),reference_native_model_load_seconds=sum(read(p)['model_load_seconds'] for p in (ROOT/'units').glob('qual-*-R/native/result.json')))
    report=dict(status='ALL_120_FIXED_PAIRS_RECONSTRUCTED',warmups=120,measurements=120,comparisons=comparisons,preparation=preparation,totals={k:math.fsum(x[k] for x in rows) for k in rows[0] if k.endswith('_seconds')},rows=rows,panel_sha256=sha(ROOT/'UNSEEN.json'),schedule_sha256=sha(ROOT/'COST_ORDER.json'))
    return report

if __name__=='__main__':
    write(ROOT/'COST.json',recompute())

