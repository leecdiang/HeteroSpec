"""Reconstruct final layer0 attention/group rows under certified trace controls."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
from trace_compare import compare

def audit(probe,certificate,out):
    probe=Path(probe);proof=read(certificate);need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS' and any(x['trace'] and x['probe_record_sha256']==sha(probe.parent.with_suffix('.json')) for x in proof['results']),'certified traced natural trajectory')
    control=read(probe/'CONTROL.json');base=control['base'];ids=control['verify_ids'];indices={};groups=[]
    for side in ('q1','q4'):
        nodes={}
        for p in sorted((probe/side/'trace').glob('*.json'),key=lambda x:int(x.stem)):
            m=read(p);need(m['phase']=='VERIFY','actual probe phase')
            if side=='q4' and m['name']=='hs_prefix_attention-0':groups.append((p,m))
            if m['name'] not in ('kqv_out-0','l_out-0'):continue
            key=m['caller_base'],m['name'];need(key not in nodes,'unique selected layer output');nodes[key]=(p,m)
        indices[side]=nodes
    rows=[]
    for name in ('kqv_out-0','l_out-0'):
        p,m=indices['q4'][base,name];need(m['ne']==[4096,4,1,1] and m['caller_ids']==ids,'complete batched trace geometry')
        for row,token in enumerate(ids):
            a,meta=indices['q1'][base+row,name];need(meta['ne']==[4096,1,1,1] and meta['caller_ids']==[token],'actual scalar trace geometry');result=compare(a.with_suffix('.bin'),p.with_suffix('.bin'),a,p,0,row,1);need(result['bitwise_equal'],'repaired trace row differs')
            rows.append(dict(name=name,row=row,scalar_meta_sha256=sha(a),batched_meta_sha256=sha(p),**result))
    need([m['ne'][1] for p,m in groups]==[3,1] and all(m['scheduler_backend']=='Vulkan0' for p,m in groups),'observed maximal3+1 Vulkan grouping')
    full=indices['q4'][base,'kqv_out-0'][0].with_suffix('.bin').read_bytes();need(b''.join(p.with_suffix('.bin').read_bytes() for p,m in groups)==full,'complete group concatenation')
    write(out,{'status':'FINAL_CONTROLLED_TRACE_PASS','actual_base':base,'verify_ids':ids,'trace_rows':rows,'group_widths':[3,1],'group_outputs_concatenate_bitwise_to_attention_output':True,'group_metadata_sha256':[sha(p) for p,m in groups],'observer_control_sha256':sha(certificate),'probe_state_control_sha256':sha(probe/'CONTROL.json'),'scope':'Actual layer0 attention and post-FFN output rows; all final full-vocabulary probe rows are independently checked by the probe auditor. Scheduler labels are not pipeline IDs.'})

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for k in ('probe','certificate','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();audit(a.probe,a.certificate,a.out)
