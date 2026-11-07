"""Map the local Vulkan disagreement to actual saved decision rows; no output_index//k."""
import argparse
from pathlib import Path
import audit
from common import need, sha, write


def compare(reference, candidate):
    a,b=audit.record(reference),audit.record(candidate);r,c=a['record'],b['record']
    need(r['prompt_ids']==c['prompt_ids'] and r['input_id']==c['input_id'],'different requests')
    need(r['slot']['observer']==c['slot']['observer']=='heavy','complete vectors required')
    rm,cm=audit.transactions(r),audit.transactions(c)
    first=next((i for i,(x,y) in enumerate(zip(r['ids'],c['ids'])) if x!=y),None)
    if first is None and len(r['ids'])!=len(c['ids']):first=min(len(r['ids']),len(c['ids']))
    common=min(len(r['ids']),len(c['ids']));limit=min(common,first+1) if first is not None else common
    rr,cr=Path(reference).with_suffix(''),Path(candidate).with_suffix('')
    earlier=next((i for i in range(limit) if sha(rr/'target'/(rm[i]+'.f32'))!=sha(cr/'target'/(cm[i]+'.f32'))),None)
    chosen=cm.get(first) if first is not None else None
    cycle=int(chosen.split('-')[1]) if chosen and chosen.startswith('verify-') else None
    return {'endpoint_equal':a['endpoint']==b['endpoint'],'first_output_difference':first,
            'earliest_saved_decision_difference':earlier,'candidate_decision_file':chosen,'suggested_cycle':cycle,
            'cause':'UNLOCATED','same_prefix_is_not_same_state':True,'new_model_requests':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('reference','candidate','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args();write(a.out,compare(a.reference,a.candidate))
