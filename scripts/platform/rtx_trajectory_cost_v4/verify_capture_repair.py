"""Independent fixed 30-run repair coverage, actual endpoints and semantic gates."""
from pathlib import Path
from verify_common import read,require,check_run,sha
def check(root,metadata):
    root=Path(root);metadata=Path(metadata);m=read(root/'work/capture-repair/records.json');order=['E_ORIGINAL_REFERENCE_UB1','R_REFERENCE_UB1','E_ORIGINAL_TARGET_ONLY_UB2','H2_P_R','R_ONLY','E_ORIGINAL_BATCHED_K2','E_ORIGINAL_SERIALIZED_K2','E_TIMER_REFERENCE_UB1','E_TIMER_BATCHED_K2','E_TIMER_SERIALIZED_K2']
    require(m['status']=='PASS' and [(r['task_id'],r['repetition'],r['condition']) for r in m['runs']]==[('HumanEval/59',rep,c) for rep in [1,2,3] for c in order],'repair fixed exposed coverage')
    require(len({r['run_id'] for r in m['runs']})==30,'repair duplicate run')
    require('HumanEval/59' not in read(metadata/'RESERVED_SET.json')['eligible_pool'],'repair task must already be exposed')
    lookup={};simultaneous=[]
    for r in m['runs']:
        d=root/r['path'];tape=d.parent/r['run_id'].replace('R_ONLY','H2_P_R')/'tape.jsonl' if r['condition']=='R_ONLY' else None
        v=check_run(d,tape,metadata);require(v['ids']==r['generated_ids'],'repair raw/manifest IDs');lookup[r['repetition'],r['condition']]=v
        if r.get('native_stop_observations')==['limit','EOS']:
            require(len(v['ids'])==128 and v['termination']=='EOS','repair actual dual endpoint');simultaneous.append(r['run_id'])
    gates={'reference':0,'replay':0,'timer_reference':0,'timer_batched':0,'timer_serialized':0}
    for rep in [1,2,3]:
        def ids(c):return lookup[rep,c]['ids']
        gates['reference']+=ids('E_ORIGINAL_REFERENCE_UB1')==ids('R_REFERENCE_UB1');gates['replay']+=ids('H2_P_R')==ids('R_ONLY')
        for label,c in [('reference','REFERENCE_UB1'),('batched','BATCHED_K2'),('serialized','SERIALIZED_K2')]:gates['timer_'+label]+=ids('E_ORIGINAL_'+c)==ids('E_TIMER_'+c)
    require(all(n==3 for n in gates.values()) and len(simultaneous)>=12,'repair semantic gate or actual simultaneous coverage')
    require(read(metadata/'EOG_VOCAB_CONTRACT.json')['eog_token_ids']==[128247,151643,151645,151662,151663,151664],'actual vocab EOG identity')
    return {'status':'PASS','actual_fresh_model_conditions':30,'task_id':'HumanEval/59','exposed_only':True,'gates':gates,'actual_simultaneous_EOG_cap_run_ids':simultaneous,'actual_dual_endpoints':len(simultaneous),'formal_observations':0,'independent':True}
