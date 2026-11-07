"""Predeclare one-factor activation-quantization intervention on real operands."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def prepare(config,out):
    c=read(config);out=Path(out);need(not out.exists(),'fresh intervention');out.mkdir(parents=True)
    c['force_no_mmvq']=True;c['expected_status']='FIXED_OPERAND_ACTIVATION_INTERVENTION_PASS'
    c['intervention']={'parent_config_sha256':sha(config),'factor':'Disable dynamic activation Q8_1 quantization using declared native backend MMVQ control','expected_before_execution':'Batched projection outputs equal concatenation of original q1 producer captures','not_model_qualification_or_timing':True}
    for f in c['fixtures']:
        if f['q']==1:continue
        scalar=[x for x in c['fixtures'] if x['q']==1 and x['weight']==f['weight']]
        need(len(scalar)==4,'four original scalar rows')
        data=b''.join(Path(x['output_payload']).read_bytes() for x in scalar);p=out/(f['id']+'.expected.bin');p.write_bytes(data)
        f['original_q4_payload']=f['output_payload'];f['original_q4_sha256']=f['hashes']['output_payload']
        f['expected_row_sources']=[{'path':x['output_payload'],'sha256':x['hashes']['output_payload']} for x in scalar]
        f['output_payload']=str(p.resolve());f['hashes']['output_payload']=sha(p)
    write(out/'CONFIG.json',c)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args();prepare(a.config,a.out)
