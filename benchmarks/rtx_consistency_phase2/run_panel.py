"""Gated scope factorial and later frozen cohort/cost panels."""
from base import HERE,read,save,sha,now,head
from server import Server,measure
from gpu import capture as gpu_capture

def run(stage):
    source=head();config=read(HERE/'CONFIG.json');inputs=read(HERE/'INPUTS.json')
    if stage=='a1':
        assert read(HERE/'generated/ENGINEERING_QUALIFICATION.json')['status']=='PASS'
        conditions=[{'name':f'mask{m}','mask':m,'spec':True} for m in config['scope_masks']]
        tasks=[next(t for t in inputs if t['id']==f'HumanEval/{i}') for i in config['sentinels']];reps=2
    else:
        selection=read(HERE/f'{stage.upper()}_SELECTION.json');assert selection['gate']=='PASS'
        conditions=selection['conditions'];tasks=inputs;reps=selection['repetitions']
    root=HERE/'runs'/stage;root.mkdir(parents=True,exist_ok=False)
    save(root/'MANIFEST.json',{'stage':stage,'source_commit':source,'protocol_sha256':sha(HERE/'MASTER_PROTOCOL.md'),
         'conditions':conditions,'repetitions':reps,'tasks':[t['id'] for t in tasks],
         'request_cap':len(conditions)*len(tasks)*reps,'warmups':len(conditions)*reps,'utc':now(),
         'build_identity':read(HERE/'generated/BUILD_IDENTITY.json'),'inputs_sha256':sha(HERE/'INPUTS.json')})
    records=[]
    for rep in range(reps):
        order=conditions if stage=='a1' and rep==0 else (list(reversed(conditions)) if stage=='a1' else conditions[rep%len(conditions):]+conditions[:rep%len(conditions)])
        for c in order:
            d=root/f'r{rep+1}-{c["name"]}';print('START '+d.name,flush=True)
            with Server(d,c['mask'],c['spec']) as s:
                if stage=='a3':gpu_capture(d/'GPU_PRE.json')
                try:
                    for task in tasks[rep%len(tasks):]+tasks[:rep%len(tasks)]:
                        r=measure(s,task,c['name'],rep+1,source);save(d/(task['id'].replace('/','-')+'.json'),r);records.append(r)
                        print(f"DONE {d.name} {task['id']} equal={r['original_reference_equal']}",flush=True)
                        if ((not c['spec'] and c['mask']==3) or (c['spec'] and c['mask']==15)) and not r['original_reference_equal']:
                            save(root/'REFERENCE_GATE_FAILURE.json',r);raise RuntimeError('Required reference/all-on gate failed; raw attempt retained')
                finally:
                    if stage=='a3':gpu_capture(d/'GPU_POST.json')
    save(root/'RECORDS.json',records);print(f'COMPLETE {stage} {len(records)}',flush=True)

if __name__=='__main__':
    import sys
    run(sys.argv[1])
