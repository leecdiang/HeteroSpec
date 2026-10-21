"""Standalone panel identities and exact JSON serializer. No backend imports."""
import hashlib
import json
import pathlib
import sys

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'host'))
from common import load,save,sha,modules

RUN_ID='b570-aligned-numerical-v2-20261015-01'
STUDY='b570-aligned-numerical-v2'
MODES=('MQ','PQ','QH_C','QH_D','REPEAT4')
STAGES=('QK','softmax','AV','final')
RUN=ROOT/'host_outputs/aligned_numerical_v2'/RUN_ID
LIMITS=dict(host_attempts=161,graph_calls=160,owned_seconds=3600,per_host_seconds=180,
    output_bytes=2*1024**3,worker_RSS_bytes=8*1024**3,host_available_bytes=8*1024**3,
    disk_free_bytes=4*1024**3,nominal_sample_ms=100,maximum_actual_gap_ms=1000,
    GPU_checkpoint_free_bytes=512*1024**2,model_requests=0,extra_probes=0,warmups=0,retries=0)

def need(ok,why):
    if not ok:raise ValueError(why)

def encode(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')

def digest(value):return hashlib.sha256(encode(value)).hexdigest()

def parse(data):
    def unique(pairs):
        result={}
        for key,value in pairs:
            need(key not in result,'duplicate JSON key');result[key]=value
        return result
    def invalid(x):raise ValueError('nonfinite JSON '+x)
    return json.loads(data,object_pairs_hook=unique,parse_constant=invalid)

def serialize(slot,inputs,binding):
    request=dict(study=STUDY,run_id=RUN_ID,slot_id=slot['id'],execution_binding_sha256=binding,
                 kind=slot['kind'],required_alignment_bytes=64)
    if slot['kind']=='census':request['cells']=[x['cell'] for x in inputs]
    else:
        item=next(x for x in inputs if x['id']==slot['input_id'])
        request.update(cell=item['cell'],input=item['path'],input_sha256=item['sha256'],mode=slot['mode'],
                       repeat=slot['repeat'],output_dir=str(RUN/slot['id']/'vectors'))
    return encode(request)

def build_plan(inputs):
    need(len(inputs)==16 and len({x['id'] for x in inputs})==16,'original16 input identities')
    expected={(q,n,hk) for q in (1,2,3,4) for n in (63,257) for hk in (8,2)}
    need({tuple(x['cell']['geometry'][k] for k in ('q','n','hk')) for x in inputs}==expected,'complete geometry grid')
    ordered=sorted(enumerate(inputs),key=lambda p:(p[1]['cell']['geometry']['q']!=1,p[0]))
    slots=[]
    def append(row):
        row=dict(run_id=RUN_ID,index=len(slots),**row);row['id']=digest(row);slots.append(row)
    append(dict(kind='census',graph_compute=False))
    for _,item in ordered:
        for repeat in (0,1):
            for mode in MODES:
                append(dict(kind='graph',input_id=item['id'],mode=mode,repeat=repeat,
                            q=item['cell']['geometry']['q'],control='q1_common' if item['cell']['geometry']['q']==1 else 'q_gt1'))
    need(len(slots)==161 and all(s['q']==1 for s in slots[1:41]) and all(s['q']>1 for s in slots[41:]),'q1-first complete plan')
    return dict(study=STUDY,run_id=RUN_ID,primary_candidate='QH_C',slots=slots,limits=LIMITS,
                input_exposure='All16 fixed synthetic operands were exposed; no unseen/natural-input claim')
