"""Compare explicitly bound Llama layer rows after probe and trace controls pass."""
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read, write, need, sha
from trace_compare import compare


def run(probe, control_report, out):
    probe=Path(probe); certificate=read(control_report)
    need(certificate['status']=='NATIVE_PROBE_CONTROLS_PASS','trace/natural controls required')
    record=probe.parent.with_suffix('.json')
    need(any(r['trace'] and r['probe_record_sha256']==sha(record) for r in certificate['results']), 'trace record not certified')
    state=read(probe/'CONTROL.json');base=state['base'];ids=state['verify_ids']
    indices={}
    for role in ('q1','q4'):
        index={}
        for p in (probe/role/'trace').glob('*.json'):
            m=read(p);need(m['phase']=='VERIFY','unexpected probe phase')
            key=(m['caller_base'],m['name'])
            need(key not in index,'ambiguous node identity')
            index[key]=(p,m)
        indices[role]=index
    rows=[]
    names=[f'l_out-{i}' for i in range(32)]+['result_norm','result_output']
    for name in names:
        bp,b=indices['q4'][base,name]
        width=128256 if name=='result_output' else 4096
        need(b['caller_ids']==ids and b['ne']==[width,len(ids),1,1], 'unqualified batched Llama output axis')
        for row,token in enumerate(ids):
            ap,a=indices['q1'][base+row,name]
            need(a['caller_ids']==[token] and a['ne']==[width,1,1,1], 'unqualified scalar Llama output axis')
            result=compare(ap.with_suffix('.bin'),bp.with_suffix('.bin'),ap,bp,0,row,1)
            rows.append(dict(name=name,row=row,position=base+row,a_meta_sha256=sha(ap),b_meta_sha256=sha(bp),**result))
    result={'status':'CONTROLLED_LAYER_ROWS_COMPARED','control_report_sha256':sha(control_report),
            'probe_control_sha256':sha(probe/'CONTROL.json'),'rows':rows,
            'first_differing_layer_by_row':{str(j):next((r['name'] for r in rows if r['row']==j and not r['bitwise_equal']),None) for j in range(len(ids))},
            'causal_operator':'NOT_YET_LOCALIZED','pipeline_identity':'NOT_CAPTURED_BY_SCHEDULER_LABEL'}
    write(out,result);print(result['first_differing_layer_by_row'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--probe',required=True);p.add_argument('--control-report',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.probe,a.control_report,a.out)
