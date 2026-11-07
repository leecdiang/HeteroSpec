"""Account for an invalidated O panel without deleting slow or failed slots."""
from operator_service_host import *
import numpy as np

def main():
    f=json.loads((ROOT/'O-FREEZE.json').read_bytes());profile=f['profile'];references={}
    for p in (ROOT/'O-main-reference').glob('*.json'):
        r=json.loads(p.read_bytes());references[tuple(r['ids'])]=r
    refs={}
    for ix,input in enumerate(f['inputs']):refs[input['id']]=json.loads((ROOT/'O-main-reference'/(str(ix)+'.json')).read_bytes())
    completed={};failures=[]
    for out in sorted(RUNS.glob('O-main-s*-pair*')):
        if not (out/'job.json').exists():continue
        spec=json.loads((out/'job.json').read_bytes());block=spec['operator_service']['blocks'][0]
        for slot in block['slots']:
            p=out/'native'/slot['id'];receipt=p/'receipt.json'
            if not receipt.exists():continue
            r=json.loads(receipt.read_bytes());ref=refs[slot['input']['id']];raw=p/'target/state/final-clean'
            row=dict(slot=slot['id'],arm=block['study_arm'],kind=slot.get('kind'),input_id=slot['input']['id'],native=str(receipt),endpoint_equal=r['endpoint']==ref['endpoint'] and r['ids']==ref['ids'])
            text=(raw/'capture.txt').read_text();count=int(text.split('position_max=')[1].splitlines()[0])+1;expected=ref['states'].get(str(count));row['materialized_count']=count
            if expected:
                a,_=parse((raw/'sequence.bin').read_bytes(),list(range(count)),profile);reference=Path(expected['native']);b,_=parse((reference/'sequence.bin').read_bytes(),list(range(count)),profile)
                row.update(active_kv_equal=a==b,frontier_equal=sha(raw/'frontier.f32')==expected['frontier'],active_sha256=hashlib.sha256(a).hexdigest(),reference_sha256=hashlib.sha256(b).hexdigest())
                if a!=b:
                    aa=np.frombuffer(a,dtype='<u2').reshape(count,36,2,1024);bb=np.frombuffer(b,dtype='<u2').reshape(aa.shape);coords=np.argwhere(aa!=bb)
                    row.update(differing_kv_half_elements=len(coords),first_kv_differences=[dict(coordinate=x.tolist(),actual_bits=int(aa[tuple(x)]),expected_bits=int(bb[tuple(x)])) for x in coords[:12]],differing_positions=np.unique(coords[:,0]).tolist())
                    if len(coords):row['intersecting_cycle']=[c for c in r['cycles'] if c['base']<=int(coords[0,0])<c['base']+c['caller_rows']]
            else:row.update(active_kv_equal=False,frontier_equal=False,reason='unmatched materialized prefix')
            row['status']='VALIDATED_BEFORE_PANEL_INVALIDATION' if row['endpoint_equal'] and row['active_kv_equal'] and row['frontier_equal'] else 'FAILED_TARGET_CONTRACT'
            completed[slot['id']]=row
            if row['status']=='FAILED_TARGET_CONTRACT':failures.append(row)
    assert failures,'No numerical failure found: inspect host interruption separately; do not manufacture a negative'
    outcomes=[dict(s,**{k:v for k,v in completed[s['slot']].items() if k not in s}) if s['slot'] in completed else dict(s,status='NOT_RUN_PANEL_INVALIDATED') for s in f['schedule']['slots']]
    put(ROOT/'O-LANE-CLOSURE.json',dict(status='CLOSED_NEGATIVE_FROZEN_PANEL_INVALIDATED',freeze_sha256=sha(ROOT/'O-FREEZE.json'),failures=failures,completed_main_requests=len(completed),validated_main_requests=len(completed)-len(failures),state_failed_main_requests=len(failures),unstarted_main_requests=len(outcomes)-len(completed),outcomes=outcomes,performance_aggregate=None,selective_retry=False,no_policy_retuning=True,prior_AUTO_null_preserved=True))

if __name__=='__main__':main()
