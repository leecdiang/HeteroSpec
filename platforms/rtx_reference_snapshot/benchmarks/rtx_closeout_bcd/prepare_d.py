"""Freeze persistent cycles only at the qualified original anchor."""
import hashlib
from close_base import HERE,read,save,sha,now

def main():
    result=read(HERE/'generated/C_RESULTS.json');assert result['D_anchor_qualified']
    selection=read(HERE/'generated/C_SELECTION.json');spec={**selection['condition'],'name':'selected_speculation'}
    target={'name':'matched_target','mask':3,'spec':False,'ub':4,'k':0};tasks=read(HERE/'B_INPUTS.json');schedule=[]
    for cycle in [1,2]:
        ids=sorted([t['id'] for t in tasks],key=lambda t:(hashlib.sha256((t+f'HeteroSpec-RTX-Phase2-D-v1-cycle{cycle}').encode()).hexdigest(),t))
        for mode in ([target,spec] if cycle==1 else [spec,target]):schedule.append({'name':f'cycle{cycle}-{mode["name"]}','repetition':cycle,'condition':mode,'tasks':ids})
    save(HERE/'D_MANIFEST.json',{'utc':now(),'protocol_sha256':sha(HERE/'PROTOCOL.md'),'inputs_sha256':sha(HERE/'B_INPUTS.json'),
         'C_results_sha256':sha(HERE/'generated/C_RESULTS.json'),'B_records_sha256':sha(HERE/'runs/b/RECORDS.json'),'server_sha256':read(HERE/'generated/C_BUILD_IDENTITY.json')['server_sha256'],
         'schedule':schedule,'capture_reset_requests':96,'capture_reset_warmups':4,'measured_requests':96,'measured_warmups':4,'fixed_cap':128})
    print('D fixed resident cycles frozen.',flush=True)

if __name__=='__main__':main()
