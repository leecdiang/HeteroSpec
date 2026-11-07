"""Resolve real projection operands from certified producer-completion captures."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha
from audit_operator_trace import index

def prepare(probe,certificate,model,out):
    probe=Path(probe);proof=read(certificate)
    need(proof['status']=='NATIVE_PROBE_CONTROLS_PASS','observer control')
    need(any(r['probe_record_sha256']==sha(probe.parent.with_suffix('.json')) for r in proof['results']),'record binding')
    control=read(probe/'CONTROL.json');base=control['base'];ids=control['verify_ids'];fixtures=[]
    batched=index(probe/'q4/trace',base);bp,bm=batched[('attn_norm-0','MUL',0)];batch=bp.with_suffix('.bin').read_bytes()
    for row in range(5):
        q=1 if row<4 else 4;nodes=index(probe/('q1/trace' if q==1 else 'q4/trace'),base+row if q==1 else base)
        ip,im=nodes[('attn_norm-0','MUL',0)]
        need(im['caller_ids']==([ids[row]] if q==1 else ids),'query identity')
        if q==1:need(ip.with_suffix('.bin').read_bytes()==batch[row*16384:(row+1)*16384],'common exact input')
        for name in ('Qcur-0','Kcur-0','Vcur-0'):
            op,om=nodes[(name,'MUL_MAT',0)]
            need(om['sources'][1]=={k:im[k] for k in ('name','ne','nb','op','type')},'input producer descriptor ownership')
            paths={'input_meta':ip,'output_meta':op,'input_payload':ip.with_suffix('.bin'),'output_payload':op.with_suffix('.bin')}
            fixtures.append({'id':f'q{q}-row{row if q==1 else 0}-{name}', 'q':q,'weight':om['sources'][0]['name'],**{k:str(v.resolve()) for k,v in paths.items()},'hashes':{k:sha(v) for k,v in paths.items()}})
    write(out,{'target_model':str(Path(model).resolve()),'target_sha256':sha(model),'certificate_sha256':sha(certificate),'certificate_path':str(Path(certificate).resolve()),'fixtures':fixtures,'scope':'Exact immutable GGUF weight and actual attn_norm producer output; own-path equality must pass before causal interpretation.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--probe',required=True);p.add_argument('--certificate',required=True);p.add_argument('--model',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.probe,a.certificate,a.model,a.out)
