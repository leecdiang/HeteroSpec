"""Separate actual reset qualification from capture-disabled resident cost."""
from close_base import HERE,read,save,sha,head,now
from close_server import Server,measure
from run_c import inspect_trace
from analyze_bcd import signature
from gpu import capture as gpu_capture

def main(stage):
    source=head();plan=read(HERE/'D_MANIFEST.json');assert plan['protocol_sha256']==sha(HERE/'PROTOCOL.md') and plan['inputs_sha256']==sha(HERE/'B_INPUTS.json')
    assert stage in ['d_reset','d']
    if stage=='d':assert read(HERE/'generated/D_RESET_QUALIFICATION.json')['status']=='PASS'
    exe=HERE/'generated/c-build/bin/llama-server.exe';assert sha(exe)==plan['server_sha256']
    inputs={t['id']:t for t in read(HERE/'B_INPUTS.json')};refs={r['task']:signature(r) for r in read(HERE/'runs/b/RECORDS.json') if r['condition']=='scalar_reference' and r['repetition']==1}
    root=HERE/'runs'/stage;root.mkdir(parents=True,exist_ok=False);save(root/'MANIFEST.json',{'stage':stage,'source_commit':source,'plan_sha256':sha(HERE/'D_MANIFEST.json'),'utc':now(),'capture':stage=='d_reset'})
    records=[];proofs=[]
    for session in plan['schedule']:
        c=session['condition'];d=root/session['name'];print('START '+d.name,flush=True)
        with Server(d,c,capture=stage=='d_reset',exe=exe) as s:
            gpu_capture(d/'GPU_PRE.json')
            try:
                for i,taskid in enumerate(session['tasks']):
                    r=measure(s,inputs[taskid],c['name'],session['repetition'],source,128);r.update({'order_index':i,'session':session['name'],'B_reference_equal':signature(r)==refs[taskid]})
                    p=d/(taskid.replace('/','-')+'.json');r['record_relative_path']=p.relative_to(HERE).as_posix();save(p,r);records.append(r)
                    print(f'DONE {d.name} {i+1} {taskid} equal={r["B_reference_equal"]}',flush=True)
            finally:gpu_capture(d/'GPU_POST.json')
        if stage=='d_reset':proofs.append({'session':session['name'],'proof':inspect_trace(d/'trace.jsonl',c['mask'],25,4,c['spec'])})
    save(root/'RECORDS.json',records)
    if stage=='d_reset':
        full=all(r['B_reference_equal'] for r in records)
        save(HERE/'generated/D_RESET_QUALIFICATION.json',{'status':'PASS' if full else 'OUTPUT_FAILURE','requests':96,'warmups':4,'proofs':proofs,'records_sha256':sha(root/'RECORDS.json')})
    print(f'COMPLETE {stage} {len(records)}',flush=True)

if __name__=='__main__':
    import sys
    main(sys.argv[1])
