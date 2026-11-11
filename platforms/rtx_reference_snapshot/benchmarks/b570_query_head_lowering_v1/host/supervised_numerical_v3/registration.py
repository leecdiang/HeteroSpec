"""New identities/serializer; reuses unchanged numerical fixtures and rules."""
from legacy import HERE,OLD,ROOT,RUN,RUN_ID,LIMITS,MODES,load,encode,digest,need

def plan():
    inputs=load(OLD/'INPUTS.json');slots=[]
    def add(fields):
        s=dict(run_id=RUN_ID,index=len(slots),**fields);s['id']=digest(s);slots.append(s)
    add(dict(kind='census',graph_compute=False))
    for item in sorted(enumerate(inputs),key=lambda x:(x[1]['cell']['geometry']['q']!=1,x[0])):
        item=item[1]
        for repeat in (0,1):
            for mode in MODES:add(dict(kind='graph',input_id=item['id'],mode=mode,repeat=repeat,q=item['cell']['geometry']['q'],control='q1_common' if item['cell']['geometry']['q']==1 else 'q_gt1'))
    need(len(slots)==161,'complete new161 host plan')
    return dict(run_id=RUN_ID,primary_candidate='QH_C',inputs_manifest='host/aligned_numerical_v2/INPUTS.json',slots=slots,
        limits=LIMITS,numerical_rules='host/aligned_numerical_v2/RULES.md',
        accounting='3600s whole future controller wall, includes control workers and audit;180s per complete slot; native observed lifetime and post-exit audit reported separately',
        extra_control_processes_max=322,experiment_processes_max=161,monitor_threads_per_host=2,monitor_main_threads=1,audit_threads_per_host=1,
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
