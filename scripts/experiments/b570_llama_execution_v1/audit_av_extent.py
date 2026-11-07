"""Recompute all AV own-path/intervention bytes and bind actual Vulkan dispatches."""
from pathlib import Path
import argparse,re,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def audit(attempt,out):
    attempt=Path(attempt);c=read(attempt/'CONFIG.json');n=read(attempt/'native/result.json');s=read(attempt/'SUPERVISOR.json')
    need(n['status']=='AV_EXTENT_INTERVENTION_PASS' and n['normal_cleanup_returned'] and s['status']=='complete' and s['job_accounting']['active_processes']==0,'native control')
    dispatches=[line for line in (attempt/'SUPERVISOR.stderr.log').read_text().splitlines() if line.startswith('HS_DISPATCH ')]
    need(len(dispatches)==len(c['fixtures'])==len(n['rows']),'one observed dispatch per AV submission')
    rows=[]
    for f,native,d in zip(c['fixtures'],n['rows'],dispatches):
        need(f['id']==native['id'],'request ordering')
        for k,h in f['hashes'].items():need(sha(f[k])==h,'fixture identity')
        p=attempt/'native'/(f['id']+'.bin');need(p.read_bytes()==Path(f['output_payload']).read_bytes(),'full independent output mismatch')
        rows.append({'id':f['id'],'sha256':sha(p),'physical_keys':native['physical_keys'],'dispatch':d})
    write(out,{'status':'INDEPENDENT_AV_EXTENT_INTERVENTION_PASS','operator_calls':len(rows),'rows':rows,'config_sha256':sha(attempt/'CONFIG.json'),'supervisor_sha256':sha(attempt/'SUPERVISOR.json'),'interpretation':'Changing only the physical reduction extent while keeping causal operands fixed exchanges the observed native results. On this Vulkan backend it also changes physical contiguity and actual dispatch between nc and contiguous F16 matvec; this is not asserted to be an unchanged-pipeline loop-length effect.'})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.attempt,a.out)
