"""Independently reconstruct full saved attention-stage byte comparisons."""
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def audit(attempt,out):
    attempt=Path(attempt);c=read(attempt/'CONFIG.json');n=read(attempt/'native/result.json');s=read(attempt/'SUPERVISOR.json')
    need(n['status']=='REAL_ATTENTION_REPLAY_PASS' and n['normal_cleanup_returned'],'native replay failed')
    need(s['job_accounting']['active_processes']==0 and s['status']=='complete','cleanup')
    fixture=c['fixtures'][0];need(len(c['fixtures'])==1 and len(n['rows'])==8,'registered inventory')
    for k,h in fixture['hashes'].items():need(sha(fixture[k])==h,'fixture drift')
    rows=[]
    for r in n['rows']:
        for key in ('qk','softmax','av','final'):
            p=attempt/'native'/(r['id']+'-'+key+'.bin');a=p.read_bytes();expected=Path(fixture[key+'_payload']).read_bytes()
            need(len(a)*4==len(expected)*r['q'] and a==expected[:len(a)],'independent full stage mismatch')
            rows.append({'id':r['id'],'q':r['q'],'arm':r['arm'],'keys':r['physical_keys'],'stage':key,'bytes':len(a),'sha256':sha(p)})
    write(out,{'status':'INDEPENDENT_REAL_ATTENTION_REPLAY_PASS','graph_submissions':8,'stage_comparisons':len(rows),'numerical_graph_nodes':sum(r['numerical_graph_nodes'] for r in n['rows']),'fixture_config_sha256':sha(attempt/'CONFIG.json'),'supervisor_sha256':sha(attempt/'SUPERVISOR.json'),'rows':rows,'scope':c['scope']})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',required=True);p.add_argument('--out',required=True);a=p.parse_args();audit(a.attempt,a.out)
