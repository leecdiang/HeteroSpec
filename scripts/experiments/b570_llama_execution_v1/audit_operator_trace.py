"""Bind layer-zero producer outputs by op, occurrence, caller IDs and tensor axes."""
from collections import Counter
from pathlib import Path
import argparse
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read, write, need, sha
from trace_compare import compare


def index(directory, base):
    result={}; counts=Counter()
    for p in sorted(Path(directory).glob('*.json'),key=lambda p:int(p.stem)):
        m=read(p)
        if m['caller_base']!=base:continue
        tag=(m['name'],m['op']);key=(*tag,counts[tag]);counts[tag]+=1
        need(m['phase']=='VERIFY','probe phase');result[key]=(p,m)
    return result


def run(probe, certificate, out):
    probe=Path(probe);proof=read(certificate)
    need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS','invalid trace/natural controls')
    need(any(r['trace'] and r['probe_record_sha256']==sha(probe.parent.with_suffix('.json')) for r in proof['results']),'trace is not certified')
    state=read(probe/'CONTROL.json');ids=state['verify_ids'];base=state['base']
    batched=index(probe/'q4/trace',base);result=[]
    for row,token in enumerate(ids):
        single=index(probe/'q1/trace',base+row)
        need(set(single)==set(batched),'operator inventory differs')
        for ordinal,(key,(bp,b)) in enumerate(batched.items()):
            ap,a=single[key]
            need(a['caller_ids']==[token] and b['caller_ids']==ids,'actual query IDs')
            axis=2 if a['op'] in ('ROPE','RESHAPE') else 1
            need(a['ne'][axis]==1 and b['ne'][axis]==len(ids),'explicit query extent')
            if axis==2:need(a['ne'][0]==128 and a['ne'][1] in (8,32) and a['ne'][3]==1,'Llama head axes')
            else:need(a['ne'][0] in (1024,4096,14336) and a['ne'][2:]==[1,1],'Llama row axes')
            metrics=compare(ap.with_suffix('.bin'),bp.with_suffix('.bin'),ap,bp,0,row,axis)
            result.append(dict(row=row,ordinal=ordinal,name=key[0],op=key[1],occurrence=key[2],query_axis=axis,
                               scalar_meta=str(ap),batched_meta=str(bp),scalar_meta_sha256=sha(ap),batched_meta_sha256=sha(bp),**metrics))
    first={str(j):next(({k:r[k] for k in ('ordinal','name','op','occurrence','max_abs')} for r in result if r['row']==j and not r['bitwise_equal']),None) for j in range(len(ids))}
    write(out,{'status':'CONTROLLED_OPERATOR_OUTPUTS_COMPARED','certificate_sha256':sha(certificate),'rows':result,'first_output_difference_by_row':first,
               'not_a_fixed_operand_replay':True,'scope':'Producer completion captures; no assertion that source descriptors are saved pre-consumer operands.'})
    print(first)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--probe',required=True);p.add_argument('--certificate',required=True);p.add_argument('--out',required=True)
    a=p.parse_args();run(a.probe,a.certificate,a.out)
