"""Report qualified same-history q8 action differences; never fit a call constant."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from verify_run import verify


def summarize(directory):
    directory=Path(directory)
    audit=verify(directory)
    result=json.loads((directory/'native/RESULT.json').read_text())
    summary={'schema':'heterospec.matched-cost-differences.v1','raw_replay_status':audit['status'],
             'native_status':result['status'],'backend':result['backend'],
             'scope':'Capture-conditioned M2 LOCAL target operation, two repetitions; no full-service or universal call-constant claim.',
             'historical_GPU_reference_qualification':'NOT_ESTABLISHED',
             'CPU_times_are_GPU_evidence':False,'full_service_performance_claim':False,
             'pairs':[]}
    if result['status']!='PASS':
        summary['status']='NO_COST_ADMITTED_QUALIFICATION_OR_EXECUTION_FAILED'
        return summary
    groups={}
    for record in result['measurements']:
        if not record['qualified'] or not all(record['comparison'].values()):raise ValueError('unqualified timing record')
        if record['q']!=8:continue
        key=(record['case'],record['mode'],record['repeat'])
        schedule=tuple(record['schedule']);group=groups.setdefault(key,{})
        if schedule in group:raise ValueError('duplicate matched action')
        group[schedule]=record
    for (case,mode,repeat),group in sorted(groups.items()):
        required={(8,),(4,4),(1,)*8}
        if set(group)!=required:raise ValueError('incomplete matched q8 group')
        if len({json.dumps(r['initial_geometry'],sort_keys=True) for r in group.values()})!=1:raise ValueError('initial geometry differs')
        if len({r['captures']['initial_state']['sha256'] for r in group.values()})!=1:raise ValueError('initial state differs')
        wide=group[(8,)]['operation_seconds'];four=group[(4,4)]['operation_seconds'];scalar=group[(1,)*8]['operation_seconds']
        summary['pairs'].append({'case':case,'mode':mode,'repeat':repeat,
                                'wide_q8_seconds':wide,'q4_plus_q4_seconds':four,'eight_q1_seconds':scalar,
                                'q4_plus_q4_minus_q8_seconds':four-wide,
                                'eight_q1_minus_q8_seconds':scalar-wide,
                                'fraction_of_q4_plus_q4_operation_saved':(four-wide)/four,
                                'physical_widths':{'+'.join(map(str,k)):v['work']['physical_widths'] for k,v in group.items()}})
    only_q1=bool(result['measurements']) and all(r['q']==1 for r in result['measurements'])
    summary['status']='MATCHED_Q8_LOCAL_DIAGNOSTIC_DIFFERENCES' if summary['pairs'] else ('NO_Q8_PAIRS_Q1_PROTOCOL_SMOKE_ONLY' if only_q1 else 'NO_MATCHED_Q8_PAIRS')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(summarize(a.directory),indent=2))
