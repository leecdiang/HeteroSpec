"""Independently reconstruct every final-binary projection width result."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

attempt=Path(sys.argv[1]);c=read(attempt/'CONFIG.json');n=read(attempt/'native/result.json');s=read(attempt/'SUPERVISOR.json');need(n['status']=='FINAL_Q8_ALL_WIDTHS_PASS' and n['normal_cleanup_returned'] and s['status']=='complete' and s['job_accounting']['active_processes']==0,'native controls');need(len(c['fixtures'])==len(n['rows'])==21,'registered width coverage');rows=[]
for f,r in zip(c['fixtures'],n['rows']):
    need(f['id']==r['id'],'order');p=attempt/'native'/(f['id']+'.bin');expected=Path(f['output_payload']).read_bytes();need(p.read_bytes()==expected,'full output bytes')
    for k,h in f['hashes'].items():need(sha(f[k])==h,'operand metadata drift')
    if f.get('expected_row_sources'):
        parts=[]
        for original in f['expected_row_sources']:need(sha(original['path'])==original['sha256'],'original scalar changed');parts.append(Path(original['path']).read_bytes())
        need(expected==b''.join(parts),'exact scalar row concatenation')
    w=attempt/'native/weights'/(r['weight']+'.bin')
    with Path(c['target_model']).open('rb') as model:model.seek(r['weight_offset']);need(model.read(r['weight_bytes'])==w.read_bytes(),'immutable weight slice')
    rows.append({'id':f['id'],'q':f['q'],'weight':r['weight'],'bytes':p.stat().st_size,'sha256':sha(p)})
need({x['q'] for x in rows}=={1,2,3,4},'all admitted widths');write(sys.argv[2],{'status':'INDEPENDENT_FINAL_Q8_ALL_WIDTHS_PASS','operator_calls':21,'rows':rows,'config_sha256':sha(attempt/'CONFIG.json'),'supervisor_sha256':sha(attempt/'SUPERVISOR.json'),'scope':c['scope']})
