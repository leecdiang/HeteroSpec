"""New identities/serializer; reuses unchanged numerical fixtures and rules."""
from legacy import HERE,OLD,ROOT,RUN,RUN_ID,LIMITS,MODES,load,encode,digest,need

def plan():
    inputs=load(OLD/'INPUTS.json');slots=[]
    def add(fields):
        s=dict(run_id=RUN_ID,index=len(slots),**fields);s['id']=digest(s);slots.append(s)
    add(dict(kind='census',graph_compute=False))
    selected=[]
    for item in inputs:
        g=item['cell']['geometry'];q,n,hk=g['q'],g['n'],g['hk']
        group='A' if q==1 and (n,hk) in ((63,8),(257,2)) else 'B' if (q,n,hk)==(2,63,8) else 'C' if (q,n,hk)==(3,257,2) else 'D' if q==4 else None
        if group:selected.append((group,item))
    for group,item in sorted(selected,key=lambda x:(x[0],x[1]['cell']['geometry']['n'], -x[1]['cell']['geometry']['hk'])):
        for repeat in (0,1):
            for mode in (['MQ','QH_C'] if group=='A' else MODES):add(dict(kind='graph',input_id=item['id'],mode=mode,repeat=repeat,q=item['cell']['geometry']['q'],group=group,control='q1_common' if group=='A' else 'q_gt1'))
    need(len(slots)==69,'targeted69 host plan')
    return dict(run_id=RUN_ID,primary_candidate='QH_C',inputs_manifest='host/aligned_numerical_v2/INPUTS.json',slots=slots,
        limits=LIMITS,numerical_rules='host/aligned_numerical_v2/RULES.md',
        accounting='900s whole future controller wall including per-slot full storage snapshot, watches, controls, audits and closeout;180s per complete slot; native lifetime and post-exit audit separate',
        extra_control_processes_max=138,experiment_processes_max=69,monitor_threads_per_host=2,monitor_main_threads=1,audit_threads_per_host=1,controller_storage_watch_threads=2,
        warmups=0,retries=0,extra_probes=0,model_requests=0,previous_samples_imported=0)

def serialize(slot,binding):
    inputs=load(OLD/'INPUTS.json')
    r=dict(study='b570-aligned-numerical-v2',run_id=RUN_ID,slot_id=slot['id'],execution_binding_sha256=binding,
        kind=slot['kind'],required_alignment_bytes=64)
    if slot['kind']=='census':r['cells']=[x['cell'] for x in inputs]
    else:
        item=next(x for x in inputs if x['id']==slot['input_id'])
        r.update(cell=item['cell'],input=item['path'],input_sha256=item['sha256'],mode=slot['mode'],repeat=slot['repeat'],output_dir=str(RUN/slot['id']/'vectors'))
    return encode(r)
