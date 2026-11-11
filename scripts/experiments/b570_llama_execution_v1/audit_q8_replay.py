"""Independently compare saved full replay bytes and bind all real operands."""
from pathlib import Path
import argparse,sys,struct
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def audit(attempt,out):
    root=Path(attempt);c=read(root/'CONFIG.json');n=read(root/'native/result.json');sup=read(root/'SUPERVISOR.json')
    need(sup['status']=='complete' and sup['job_accounting']['active_processes']==0,'cleanup')
    expected_status=c.get('expected_status','OWN_PATH_REPLAY_PASS')
    need(n['normal_cleanup_returned'] and n['status']==expected_status,'native failure')
    need(len(c['fixtures'])==len(n['rows'])==15,'full fifteen real-operand calls')
    rows=[]
    for f,r in zip(c['fixtures'],n['rows']):
        need(f['id']==r['id'],'order');actual=root/'native'/(f['id']+'.bin');expected=Path(f['output_payload'])
        need(actual.read_bytes()==expected.read_bytes(),'independent own-path bytes mismatch')
        for k,h in f['hashes'].items():need(sha(f[k])==h,'fixture drift')
        if f.get('expected_row_sources'):
            payload=[]
            for x in f['expected_row_sources']:
                need(sha(x['path'])==x['sha256'],'original scalar reference changed');payload.append(Path(x['path']).read_bytes())
            need(expected.read_bytes()==b''.join(payload),'intervention target must be exact original scalar concatenation')
        w=root/'native/weights'/(r['weight']+'.bin')
        with Path(c['target_model']).open('rb') as model:
            model.seek(r['weight_offset']);need(model.read(r['weight_bytes'])==w.read_bytes(),'immutable GGUF operand mismatch')
        rows.append({'id':f['id'],'actual_sha256':sha(actual),'expected_sha256':sha(expected),'weight_sha256':sha(w),'complete_bytes':actual.stat().st_size})
    paired=[]
    for name in ('Qcur-0','Kcur-0','Vcur-0'):
        batch=(root/'native'/f'q4-row0-{name}.bin').read_bytes();width=len(batch)//4
        for row in range(4):
            a=(root/'native'/f'q1-row{row}-{name}.bin').read_bytes();b=batch[row*width:(row+1)*width]
            need(len(a)==len(b),'logical row extent')
            af=struct.unpack('<'+'f'*(len(a)//4),a);bf=struct.unpack('<'+'f'*(len(b)//4),b)
            paired.append({'name':name,'row':row,'bitwise_equal':a==b,'max_abs':max(abs(x-y) for x,y in zip(af,bf))})
    log=root/'SUPERVISOR.stderr.log';dispatch=[line for line in log.read_text(encoding='utf-8',errors='strict').splitlines() if line.startswith('HS_DISPATCH ')]
    if c.get('force_no_mmvq'):
        need(n['declared_disable_mmvq_intervention'] and all(x['bitwise_equal'] for x in paired),'intervention not executed or failed')
        need(len(dispatch)==15 and all('pipeline=mul_mat_vec_q8_0_f32_f32 ' in line for line in dispatch),'actual intervention dispatch')
    write(out,{'status':'INDEPENDENT_'+expected_status,'operator_calls':15,'model_requests':0,'config_sha256':sha(root/'CONFIG.json'),'native_result_sha256':sha(root/'native/result.json'),'supervisor_sha256':sha(root/'SUPERVISOR.json'),'rows':rows,'same_input_q1_q4_projection_outputs':paired,'actual_dispatch_lines':dispatch,'dispatch_log_sha256':sha(log),'scope':'Same-host saved-byte reconstruction, not third-party scientific replication.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.attempt,a.out)
