"""Old-reference bridge, then locked prospective paid-reference experiment."""
from close_base import HERE,PHASE2,read,save,sha,now,head
from close_server import Server,measure
from gpu import capture as gpu_capture

def main(stage):
    source=head();plan=read(HERE/'B_MANIFEST.json')
    assert plan['inputs_sha256']==sha(HERE/'B_INPUTS.json') and plan['protocol_sha256']==sha(HERE/'PROTOCOL.md')
    if stage=='bridge_b':
        inputs=read(PHASE2/'INPUTS.json');tasks=[next(t for t in inputs if t['id']==f'HumanEval/{i}') for i in plan['bridge']['original_tasks']]
        repetitions=1
    else:
        assert stage=='b' and read(HERE/'generated/BRIDGE_B.json')['status']=='PASS'
        tasks=read(HERE/'B_INPUTS.json');repetitions=plan['repetitions']
    conditions=plan['conditions'];root=HERE/'runs'/stage;root.mkdir(parents=True,exist_ok=False)
    save(root/'MANIFEST.json',{'stage':stage,'utc':now(),'source_commit':source,'plan_sha256':sha(HERE/'B_MANIFEST.json'),
          'conditions':conditions,'tasks':[t['id'] for t in tasks],'repetitions':repetitions,'request_cap':len(tasks)*len(conditions)*repetitions,
          'warmups':len(conditions)*repetitions,'runner_sha256':sha(HERE/'run_b.py'),'server_wrapper_sha256':sha(HERE/'close_server.py')})
    records=[]
    for rep in range(repetitions):
        order=conditions[rep%4:]+conditions[:rep%4]
        for c in order:
            d=root/f'r{rep+1}-{c["name"]}';print('START '+d.name,flush=True)
            with Server(d,c) as s:
                gpu_capture(d/'GPU_PRE.json')
                try:
                    for t in tasks[rep%len(tasks):]+tasks[:rep%len(tasks)]:
                        r=measure(s,t,c['name'],rep+1,source)
                        assert r['response']['timings']['prompt_n']==t.get('prompt_token_count',r['response']['timings']['prompt_n'])
                        if stage=='bridge_b':
                            r['original_reference_equal']=r['response']['tokens']==t['original_reference_ids'] and r['endpoint']==t['original_endpoint']
                        p=d/(t['id'].replace('/','-')+'.json');r['record_relative_path']=p.relative_to(HERE).as_posix()
                        save(p,r);records.append(r)
                        print(f'DONE {d.name} {t["id"]}'+(f' equal={r["original_reference_equal"]}' if stage=='bridge_b' else ''),flush=True)
                        if stage=='bridge_b' and not r['original_reference_equal']:
                            save(root/'BRIDGE_FAILURE.json',r);raise RuntimeError('Original scalar/reference bridge failed; no new-task inference permitted')
                finally:gpu_capture(d/'GPU_POST.json')
    save(root/'RECORDS.json',records)
    if stage=='bridge_b':save(HERE/'generated/BRIDGE_B.json',{'status':'PASS','requests':16,'warmups':4,'source_commit':source,'records_sha256':sha(root/'RECORDS.json')})
    print(f'COMPLETE {stage} {len(records)}',flush=True)

if __name__=='__main__':
    import sys
    main(sys.argv[1])
