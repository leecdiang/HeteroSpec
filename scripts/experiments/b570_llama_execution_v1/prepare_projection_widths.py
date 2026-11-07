"""Add q2/q3 real activation-prefix cases to the already certified Q8 controls."""
from pathlib import Path
import copy,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

root=Path(sys.argv[1]);out=root/'projection-widths-plan-00';need(not out.exists(),'fresh plan');out.mkdir()
c=read(root/'Q8_STRUCTURAL_CONFIG-01.json');original=copy.deepcopy(c['fixtures'])
for f in original:
    if f['q']!=4:continue
    for q in (2,3):
        x=copy.deepcopy(f);x['q']=q;x['id']=f['id'].replace('q4-',f'q{q}-');x['expected_row_sources']=f['expected_row_sources'][:q]
        for key in ('input','output'):
            old=read(f[key+'_meta']);m=copy.deepcopy(old);m['ne'][1]=q;m['nb'][2]=m['nb'][3]=m['nb'][1]*q
            m['derived_capture']={'original_meta_sha256':sha(f[key+'_meta']),'original_payload_sha256':sha(f[key+'_payload']),'first_rows':q,'scope':'Real producer input prefix; not labeled a separately captured natural q2/q3 call'}
            data=Path(f[key+'_payload']).read_bytes();need(len(data)%4==0,'four original rows');data=data[:len(data)//4*q]
            if 'bytes' in m:m['bytes']=len(data)
            p=out/(x['id']+'-'+key+'.json');write(p,m);p.with_suffix('.bin').write_bytes(data);x[key+'_meta']=str(p);x[key+'_payload']=str(p.with_suffix('.bin'))
        x['hashes']={k:sha(x[k]) for k in ('input_meta','output_meta','input_payload','output_payload')};c['fixtures'].append(x)
c['expected_rows']=c['operator_calls']=21;c['expected_status']='FINAL_Q8_ALL_WIDTHS_PASS';c['scope']='Final candidate binary: original q1 controls and F32-policy q4 controls, plus q2/q3 prefixes of the same real captured producer operands, compared with original scalar concatenations; no environment override.';write(out/'CONFIG.json',c)
p=Path(__file__).with_name('q8_replay.cpp');s=p.read_text(encoding='utf-8');need(s.count('q==1||q==4')==1,'width guard');source=out/'q8_replay_all_widths.cpp';source.write_text(s.replace('q==1||q==4','q>=1&&q<=4'),encoding='utf-8',newline='\n');write(out/'SOURCE.json',{'parent_source_sha256':sha(p),'source_sha256':sha(source),'change':'Only the diagnostic admission guard expands to q1..4; graph/weights/precision/validation code unchanged'})
