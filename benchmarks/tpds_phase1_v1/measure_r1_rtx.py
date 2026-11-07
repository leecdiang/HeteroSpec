"""Fixed 96+96 known-token append matrix on qualified frozen native bytes."""
from qualify_rtx import *
from analyze import analyze_structural
import build_freeze

def verify_freezes():
    for recipe in ('loop4','packed'):
        d=ROOT/'freezes'/recipe
        build_freeze.verify(read(d/'BUILD_INPUTS.json'),read(d/'BUILD_FREEZE.json'))
    pre=ROOT/'PRE_OUTPUT_FREEZE.json'
    if pre.exists():
        frozen=read(pre)
        for path,h in frozen['files'].items():assert sha(path)==h,('Frozen schedule/input changed',path)
        for name,h in frozen['host_python_files'].items():assert sha(HERE/name)==h,('Frozen host execution/analysis source changed',name)

def verify_observed_modules(recipe,out):
    expected=read(ROOT/'freezes'/recipe/'BUILD_FREEZE.json')['loaded_modules']
    actual=read(out/'ACTUAL_MODULES.json')['modules_after']
    def values(rows):return {str(Path(r['path']).resolve()).casefold():r['sha256'] for r in rows}
    assert values(expected)==values(actual),'Actual loaded modules differ from the qualified freeze'

def main():
    assert read(ROOT/'R1_PUBLISHED.json')['independent_readback_passed']
    assert read(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json')['passed']
    plan=read(ROOT/'R1-STRUCT-SCHEDULE.json');assert len(plan)==192
    dest=ROOT/'R1-STRUCT';dest.mkdir(exist_ok=False)
    start=time.monotonic();verify_freezes();records=[];paid=[]
    put(dest/'PREFLIGHT.json',dict(wall_s=time.monotonic()-start,complete_build_inputs_verified=True,protocol_version='review-v2',source_inputs_sha256=sha(ROOT/'R1-STRUCT-SCHEDULE.json'),qualification_sha256=sha(ROOT/'NATIVE_QUALIFICATION_COMPLETE.json')))
    for i in range(0,len(plan),2):
        pair=plan[i:i+2];a,b=pair;assert a['kind']=='warmup' and b['kind']=='measurement' and a['arm']==b['arm']
        family=a['family'];t=tape(family);h=a['head'];w=a['width'];recipe,lowering=ARMS[a['arm']]
        probes=[dict(name=x['slot_id'],prefix=t[:h],ids=t[h:h+w]) for x in pair]
        label='R1-'+a['slot_id'];out=finished(label,recipe,family,dict(lowering=lowering,residency='matched',draft=False,draft_width=1,append_probes=probes),dict(requests=2,token_rows=2*(h+w),operators=0))
        verify_observed_modules(recipe,out)
        reference=str(ROOT/f'{family}-v2-matrix-{a["arm"]}-QUALIFICATION.json')
        for slot in pair:
            p=out/'native'/slot['slot_id']/'receipt.json';r=read(p)
            assert r['capacity']==slot['capacity'] and r['head']==h and r['width']==w and r['copied_requested_rows']==1 and r['requested_outputs']=='last'
            assert all(v==0 for v in r['append_observer_calls'].values())
            assert r['graphs_built']+r['graphs_reused']==sum(r['physical_widths'])
            assert r['append_ms']>0 and r['append_ms']==(r['append_end_us']-r['append_begin_us'])/1000
            records.append(dict(slot_id=slot['slot_id'],status='COMPLETE',qualified=True,service_s=r['append_ms']/1000,reference_id=family+'-immutable-original-R-C1024-v2-matrix',window='append_after_valid_state',native_timing_field='append_ms/1000',qualification=reference,native_receipt=str(p),native_receipt_sha256=sha(p)))
        paid.append(dict(attempt=str(out),preparation_s=[read(out/'native'/x['slot_id']/'receipt.json')['preparation_s'] for x in pair],host_wall_s=read(out/'exit.json')['seconds']))
        print('Fixed R1 pair',i//2+1,'/96 complete',family,a['arm'],a['root'],flush=True)
    verify_freezes();put(dest/'RECORDS.json',records);put(dest/'RESULTS.json',analyze_structural(plan,records));put(dest/'COMPLETE.json',dict(measurements=96,warmups=96,paid_pairs=paid,coordinator_wall_s=time.monotonic()-start,all_slots_kept=True,source_and_modules_unchanged=True,natural_population_inference=False))

if __name__=='__main__':main()
