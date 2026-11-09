"""Current-epoch physical geometry bridge, including1+k splits at256/768."""
from pathlib import Path
import collections,copy,json,sys
from admission import ROOT,put,sha
from execute import BASE,WORK,execute
from lifecycle_gate import read,spec
from geometry_gate import check

MANIFEST='JOB_MANIFEST_GEOMETRY_V2.json'

def freeze():
    old=read(ROOT/'JOB_MANIFEST_GEOMETRY.json');base=read(ROOT/'JOB_MANIFEST_LIFECYCLE.json')
    rr=Path('D:/rtx188/runs/Qwen-old-free/native/r3-heavy/receipt.json');r=read(rr);tape=r['prompt_ids']+r['ids'];cc=[]
    for width in (4,8):
        for head in (255,767):
            assert len(tape)>=head+width
            cc.append(dict(name=f'edge{head}-q{width}',forced=[dict(ids=tape[:head],phase='PREFILL',all=False),dict(ids=tape[head:head+width],phase='VERIFY',all=True)],
                observe_positions=list(range(head,head+width+1)),state_positions=[head,head+width]))
    models={k:v for k,v in old['jobs'][0]['job'].items() if k.endswith(('_model','_sha256'))}
    jobs=[spec('geometry-v2-extra-independent-R','R',dict(models,lowering='SIMPLE',cases=cc),len(cc),sum(len(c['forced'][0]['ids'])+len(c['forced'][1]['ids']) for c in cc))]
    for prior in old['jobs'][1:]:
        core='packed' if '-packed-' in prior['id'] else 'loop4';k=prior['job']['k'];cases=copy.deepcopy(prior['job']['cases'])+[c for c in cc if c['name'].endswith('-q'+str(k+1))]
        payload=dict(prior['job'],cases=cases)
        jobs.append(spec(prior['id'].replace('geometry-v1','geometry-v2'),core,payload,len(cases),sum(sum(len(v['ids']) for v in c['forced']) for c in cases)))
    put(ROOT/MANIFEST,dict(base,status='FROZEN_CURRENT_EPOCH_PHYSICAL_COUNTER_GEOMETRY',jobs=jobs,requests=sum(j['requests'] for j in jobs),rows=sum(j['rows'] for j in jobs),
        original_scalar_geometry_reused=str(WORK/'runs/geometry-v1-independent-R/native'),scalar_long_operand_receipt=str(rr),scalar_long_operand_sha256=sha(rr),
        criteria='All requested full rows and active KV against unchanged Windows R; actual core histograms equal frontend executions; LOCAL k7 retains8, W1+k crosses extent; q4 is packing negative control.'))
    print('Frozen V2 geometry',sum(j['requests'] for j in jobs),'requests',flush=True)

def physical(native,job):
    meta=read(native/'result.json');reports=[]
    for record,case in zip(meta['cases'],job['job']['cases']):
        executions=record['executions'];assert dict(collections.Counter(str(e['width']) for e in executions))==record['target_physical_width_hist']
        assert not record['draft_physical_width_hist']
        verify=[e for e in executions if e['phase']=='VERIFY'];width=job['job']['k']+1
        assert sum(e['width'] for e in verify)==width
        assert sorted(i for e in verify for i in e['requested_rows'])==list(range(width))
        if job['job']['lowering']=='LOCAL':assert len(verify)==1 and verify[0]['width']==width
        if case['name'].startswith('edge') and job['job']['lowering']=='SIMPLE':assert [e['width'] for e in verify]==[1,width-1]
        graph=[g for g in record['geometry'] if g['phase']=='VERIFY' and g['op']=='MUL_MAT'];assert graph
        packed=[g for g in graph if g['name'].startswith('frontier_packed_')]
        if width==4:assert not packed
        if width==8 and '-packed-' in job['id'] and any(e['width']==8 for e in verify):
            assert packed and all(g['ne'][1:3]==[4,2] for g in packed)
        loop=[g for g in graph if g['name'].startswith('hs_backend_loop4_')]
        if width==8 and '-loop4-' in job['id'] and any(e['width']==8 for e in verify):assert loop
        reports.append(dict(case=case['name'],verify=verify,physical_hist=record['target_physical_width_hist'],packed_verify_nodes=len(packed),marked_loop4_nodes=len(loop),
            packed_samples=packed[:2],graph_descriptor_count=len(graph),q8_group_eligible=any(e['width']==8 for e in verify)))
    put(ROOT/'geometry_v2_checks'/(job['id']+'-PHYSICAL.json'),dict(passed=True,cases=reports,not_kernel_profiling=True))

def main():
    if sys.argv[1]=='freeze':freeze();return
    manifest=read(ROOT/MANIFEST);old=WORK/'runs/geometry-v1-independent-R/native';new=None
    for job in manifest['jobs']:
        native=execute(job,MANIFEST)
        if job['id']=='geometry-v2-extra-independent-R':new=native;continue
        for kind,ref in [('old',old),('edge',new)]:
            cc=[c for c in job['job']['cases'] if c['name'].startswith('edge')==(kind=='edge')]
            one=dict(job,id=job['id']+'-'+kind,job=dict(job['job'],cases=cc));check(ref,native,one)
        physical(native,job)
    put(ROOT/'GEOMETRY_V2_COMPLETE.json',dict(passed=True,requests=36,actual_core_q8=True,all_requested_rows=True,extents=[256,768],within_balanced_cross_and1plusk_cross=True))

if __name__=='__main__':main()
