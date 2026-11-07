"""Deterministic B-output-only selection and complete C schedule freeze."""
from close_base import HERE,read,save,sha,now

def main():
    chosen=read(HERE/'generated/C_SELECTION.json');assert chosen['status']=='QUALIFIED'
    assert chosen['B_results_sha256']==sha(HERE/'generated/B_RESULTS.json')
    tasks=[t for i in chosen['tasks'] for t in read(HERE/'B_INPUTS.json') if t['id']==i]
    for t in tasks:t['cohort']='primary_unused_MBPP'
    for t in read(HERE/'C_LEGACY_INPUTS.json'):t['cohort']='exposed_long_supplement';tasks.append(t)
    save(HERE/'C_INPUTS.json',tasks)
    schedule=[]
    for rep in range(2):
        widths=chosen['widths'] if rep==0 else chosen['widths'][::-1]
        for wi,(k,ub) in enumerate(widths):
            modes=[{'name':'scalar_reference','mask':0,'spec':False,'k':0,'ub':1},
                   {'name':'matched_target','mask':3,'spec':False,'k':0,'ub':ub},
                   {**chosen['condition'],'name':'selected_speculation','k':k,'ub':ub}]
            rotation=(rep+wi)%3;modes=modes[rotation:]+modes[:rotation]
            caps=chosen['caps'];cr=(rep+wi)%3;caps=caps[cr:]+caps[:cr]
            taskids=[t['id'] for t in tasks];tr=(rep+wi)%len(taskids);taskids=taskids[tr:]+taskids[:tr]
            for mode in modes:schedule.append({'repetition':rep+1,'width_k':k,'width_ub':ub,'condition':mode,'caps':caps,'tasks':taskids})
    save(HERE/'C_MANIFEST.json',{'utc':now(),'B_selection':chosen,'protocol_sha256':sha(HERE/'PROTOCOL.md'),'inputs_sha256':sha(HERE/'C_INPUTS.json'),
         'build_identity':read(HERE/'generated/C_BUILD_IDENTITY.json'),'patch_identity_sha256':sha(HERE/'generated/C_PATCH_IDENTITY.json'),
         'schedule':schedule,'measured_requests':792,'warmups':24,'bridge_requests':48,'bridge_warmups':2,'topology_requests':16,'topology_warmups':8,
         'diagnostic_selection':'at most two failures ordered k then cap then frozen task order; never retune modes'})
    print('C schedule frozen: primary8 + exposed3, 792 measured requests.',flush=True)

if __name__=='__main__':main()
