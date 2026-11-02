"""Bind certified real QB attention captures to expanded-domain replay cases."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha,TARGET

def prepare(probe,certificate,model,out):
    probe=Path(probe);proof=read(certificate);control=read(probe/'CONTROL.json')
    need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS','observer certificate')
    need(any(x['probe_record_sha256']==sha(probe.parent.with_suffix('.json')) for x in proof['results']),'certified actual request')
    nodes={}
    for p in (probe/'q4/trace').glob('*.json'):
        m=read(p)
        if m['caller_base']==control['base'] and m['phase']=='VERIFY':
            need(m['caller_ids']==control['verify_ids'],'real query identity');need(m['name'] not in nodes,'ambiguous stage label');nodes[m['name']]=(p,m)
    stages={'qk':'hs_qb_qk-0','softmax':'hs_qb_prob-0','av':'hs_qb_av-0','final':'kqv_out-0'};fixture={'id':'attention-base'+str(control['base'])};hashes={}
    for key,name in stages.items():
        p,m=nodes[name]
        for label,path in [(key+'_meta',p),(key+'_payload',p.with_suffix('.bin'))]:fixture[label]=str(path.resolve());hashes[label]=sha(path)
    for key,stage,source in [('Q','qk','src1'),('K','qk','src0'),('V','av','src0'),('mask','softmax','src1')]:
        m=nodes[stages[stage]][1];item=m['raw_operands'][source];meta=read(item['meta'])
        need(meta['source_output_disjoint'] and meta['caller_base']==control['base'] and meta['caller_ids']==control['verify_ids'],'real disjoint operand certificate')
        for suffix in ('meta','payload'):
            label=key+'_'+suffix;fixture[label]=item[suffix];hashes[label]=sha(item[suffix])
    fixture['hashes']=hashes
    write(out,{'target_model':str(Path(model).resolve()),'target_sha256':TARGET,'certificate_path':str(Path(certificate).resolve()),'certificate_sha256':sha(certificate),'expected_status':'REAL_ATTENTION_REPLAY_PASS','expected_rows':8,'operator_calls':8,'operator_accounting_unit':'one native attention-chain graph submission; numerical node count also recorded per submission','fixtures':[fixture],'scope':'q4 QB own-path replay plus PQ correspondence and first-q real input slices q1/2/3 at identical physical KV extent. Cropped q1 inputs are not claimed to have the natural scalar cache extent at a boundary.'})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('probe','certificate','model','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();prepare(a.probe,a.certificate,a.model,a.out)
