"""Separate actual dispatch/clean-append observations; never formal timing."""
from qualify_rtx import *
from collections import Counter
from receipts import natural_decision

def histogram(out):
    events=read(out);counts=Counter()
    for e in events:
        if e['kind']=='kernel':key=('kernel',e['name'],tuple(e['grid']),tuple(e['block']))
        else:key=('copy',e['bytes'],e['direction'])
        counts[key]+=1
    assert counts and any(k[0]=='kernel' for k in counts),'No actual GPU kernel activities'
    return dict(sorted((json.dumps(k),v) for k,v in counts.items()))

def main():
    summary=[];scope=[];natural={};profiling=[]
    for family in ('Qwen','Smol'):
        t=tape(family)
        for arm,(recipe,lowering) in ARMS.items():
            probes=[dict(name='q'+str(w),prefix=t[:767],ids=t[767:767+w]) for w in (4,32)]
            out=finished(f'{family}-append-scope-{arm}',recipe,family,dict(lowering=lowering,append_probes=probes),dict(requests=2,token_rows=sum(len(p['prefix'])+len(p['ids']) for p in probes),operators=0))
            for p in probes:
                row=read(out/'native'/p['name']/'receipt.json');assert row['capacity']==1024 and row['copied_requested_rows']==1
                assert all(v==0 for v in row['append_observer_calls'].values())
                assert row['graphs_built']+row['graphs_reused']==sum(row['physical_widths']) and sum(row['physical_widths'])>0
                scope.append(dict(family=family,arm=arm,width=len(p['ids']),actual=row,native_receipt=str(out/'native'/p['name']/'receipt.json'),numerical_qualification=str(ROOT/f'{family}-v2-matrix-{arm}-QUALIFICATION.json')))
            for width in (4,32):
                probe=dict(name='trace',prefix=t[:767],ids=t[767:767+width])
                out=finished(f'{family}-profile-append-q{width}-{arm}',recipe,family,dict(lowering=lowering,profile=True,append_probes=[probe]),dict(requests=1,token_rows=767+width,operators=0))
                assert read(out/'native/trace/CUPTI-RECEIPT.json')['dropped_records']==0
                summary.append(dict(family=family,arm=arm,width=width,histogram=histogram(out/'native/trace/cuda-events.json'),raw_events=str(out/'native/trace/cuda-events.json'),profiled_not_clean_timing=True))
            r=dict(roots(family)[0],cap=16)
            out=finished(f'{family}-profile-natural-{arm}',recipe,family,dict(lowering=lowering,profile=True,inputs=[dict(name='trace',capture=False,input=r)]),dict(requests=1,token_rows=len(r['prompt_ids'])+15,operators=0))
            assert read(out/'native/CUPTI-RECEIPT.json')['dropped_records']==0
            row=read(out/'native/trace/receipt.json');old=read(P190/'runs'/(family+'-old-free')/'native/r0-heavy/receipt.json');assert row['ids']==old['ids'][:16]
            natural[(family,arm)]=dict(histogram=histogram(out/'native/cuda-events.json'),native=row,source_out=str(out))
            profiling.append(dict(family=family,arm=arm,out=str(out),zero_drop=True,original_R_endpoint_prefix_equal=True))
    comparisons=[]
    for family in ('Qwen','Smol'):
        for a,b in [('W_L4','L_L4'),('W_P','L_P')]:
            x,y=natural[(family,a)],natural[(family,b)]
            # This does NOT certify total frontend equivalence. The source's
            # whole planner scans/group-validates; the local caller constructs
            # the same aligned groups with different bookkeeping.
            comparisons.append(dict(family=family,arms=[a,b],actual_kernel_grid_block_copy_histogram_equal=x['histogram']==y['histogram'],physical_executions_equal=x['native']['executions']==y['native']['executions'],source_paths=[x['source_out'],y['source_out']],frontend_cost_path_identical=False))
    assert all(x['actual_kernel_grid_block_copy_histogram_equal'] and x['physical_executions_equal'] for x in comparisons),'Inspect actual non-alias behavior before deciding the optional natural branch'
    facts=dict(four_arms_qualified=True,distinct_mechanism=False,unanswered_natural_question=False,source_review=True,trace_review=True,numerical_failure=False,engineering_open=False,budget_available=True)
    put(ROOT/'APPEND_SCOPE_QUALIFICATION.json',dict(passed=True,observations=scope,same_numerical_Context_decode_as_forced_matrix=True,scope='Numerical vectors/KV qualified in separate forced calls; actual clean append counters/heads/masks observed here. No full-state claim for these clean requests.'))
    put(ROOT/'DISPATCH_REVIEW.json',dict(fixed_append_profiles=summary,natural_profiles=profiling,aligned_natural_pairs=comparisons,source_rule='Dense cache padding256 and outer groups32 from0 do not cross padding boundaries in M; singleton continuation is identical numerically within each recipe. Whole/local host planner bookkeeping differs.',kernel_activities_not_launch_API_counts=True,profiled_times_not_performance_samples=True))
    put(ROOT/'R1_NATURAL_DECISION.json',dict(facts=facts,decision=natural_decision(facts),reason='The genuine structural cut/packing factors remain in the fixed mechanism matrix. Natural M has no new cut mechanism on the admitted aligned profile and would repeat prior packing comparisons; frontend bookkeeping remains a real R2 control, so no mixed target-only arm is omitted.',R2_continues_with_all_four_target_only_controls=True,old_results_unchanged=True))
    print('Actual clean append scope and CUDA dispatch reviewed; optional R1 natural closed, R2 remains independent',flush=True)

if __name__=='__main__':main()
