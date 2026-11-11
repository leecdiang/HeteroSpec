"""Describe producer-state changes separately from reference preservation.

Consumes analyze.py's independently rehashed audit, binds its source ledger,
and additionally reads the actual initial FP32 vectors. No model is invoked.
"""
import argparse
import array
import csv
from pathlib import Path
import sys
import work_package as wp

def main():
    ap=argparse.ArgumentParser()
    for n in ['plan','records','payload-root','analysis','out']:ap.add_argument('--'+n,type=Path,required=True)
    a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    plan=wp.read(a.plan);slots=wp.validate_plan(plan);records=wp.load_records(a.records)
    audit=wp.read(a.analysis/'CPU_AUDIT.json');summary=wp.read(a.analysis/'SUMMARY.json')
    assert summary['source_records_sha256']==wp.sha_file(a.records)
    assert audit['plan_sha256']==wp.digest(plan) and audit['payloads_rehashed']
    by_id={r['slot_id']:r for r in records};bad={e['slot_id'] for e in audit['errors']}
    result=[]
    for index in range(8):
        group=[s for s in slots if s['stage']=='B1' and s['input_index']==index]
        valid=audit['b0_qualified'] and all(s['slot_id'] in by_id and by_id[s['slot_id']]['status'] in wp.COMPLETE and s['slot_id'] not in bad for s in group)
        r=dict(input_index=index,input_id=group[0]['input_id'],prompt_tokens=group[0]['prompt_tokens'],qualified=valid)
        if not valid:
            r['outcome']='UNQUALIFIED_OR_NOT_RUN';result.append(r);continue
        def get(producer,consumer,route,observer):
            slot=next(s for s in group if (s['producer'],s['consumer'],s['route'],s['observer'])==(producer,consumer,route,observer))
            return by_id[slot['slot_id']]
        natural={p:get(p,'C1','natural','heavy') for p in ['P1','P4T']}
        reference=get('P1','C1','strict_reference','off')
        signatures={p:wp.boundary_signature(natural[p]) for p in natural}
        r['producer_boundary_equal']=signatures['P1']==signatures['P4T']
        for component in ['kv','initial_logits']:
            r[component+'_bytes_equal']=signatures['P1'][component]==signatures['P4T'][component]
        vectors=[]
        for producer in ['P1','P4T']:
            meta=natural[producer]['boundary']['initial_logits'];wp.safe_payload(a.payload_root,meta)
            values=array.array('f');values.frombytes((a.payload_root/meta['path']).read_bytes())
            if sys.byteorder!='little':values.byteswap()
            assert len(values)==plan['runtime']['vocabulary_size'];vectors.append(values)
        r['initial_logits_differing_elements']=sum(x!=y for x,y in zip(*vectors))
        r['initial_logits_max_absolute_difference']=max(abs(x-y) for x,y in zip(*vectors))
        r['natural_endpoints_equal']=natural['P1']['endpoint']==natural['P4T']['endpoint']
        endpoints=[];by_consumer={}
        def first_difference(left,right):
            return next((i for i,(x,y) in enumerate(zip(left,right),1) if x!=y),min(len(left),len(right))+1 if len(left)!=len(right) else None)
        for producer in ['P1','P4T']:
            base=natural[producer]
            r[producer+'_C1_strict_reference_equal']=base['endpoint']==reference['endpoint'];endpoints.append(base['endpoint'])
            r[producer+'_C1_first_R_difference_1based']=first_difference(base['endpoint']['ids'],reference['endpoint']['ids'])
            consumers={c:get(producer,c,'resumed','heavy') for c in ['PQ','QB']}
            by_consumer[producer]=consumers
            for consumer,row in consumers.items():
                r[producer+'_'+consumer+'_producer_conditioned_equal']=row['endpoint']==base['endpoint']
                r[producer+'_'+consumer+'_strict_reference_equal']=row['endpoint']==reference['endpoint'];endpoints.append(row['endpoint'])
                r[producer+'_'+consumer+'_first_R_difference_1based']=first_difference(row['endpoint']['ids'],reference['endpoint']['ids'])
                r[producer+'_'+consumer+'_first_C1_difference_1based']=first_difference(row['endpoint']['ids'],base['endpoint']['ids'])
            comparisons=wp.compare_records(consumers['PQ'],consumers['QB'],True)
            for key,value in comparisons.items():r[producer+'_PQ_QB_'+key+'_equal']=value
        r['all_six_endpoints_match_R']=all(e==reference['endpoint'] for e in endpoints)
        for consumer in ['PQ','QB']:
            r['producer_change_'+consumer+'_endpoints_equal']=by_consumer['P1'][consumer]['endpoint']==by_consumer['P4T'][consumer]['endpoint']
        r['outcome']=('STATE_CHANGED_OUTPUT_UNCHANGED' if not r['producer_boundary_equal'] else 'NO_STATE_CHANGE') if r['all_six_endpoints_match_R'] else 'REFERENCE_OR_CONSUMER_DIFFERENCE'
        if not r['all_six_endpoints_match_R'] and any(r[p+'_PQ_QB_endpoint_equal'] and not r[p+'_PQ_producer_conditioned_equal'] for p in ['P1','P4T']):
            r['outcome']='MATCHING_LOCAL_CONSUMERS_DIFFER_FROM_C1'
        result.append(r)
    wp.write_new(a.out/'STATE_EFFECTS.json',result)
    keys=list(dict.fromkeys(k for r in result for k in r))
    with (a.out/'STATE_EFFECTS.csv').open('x',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(result)
    wp.write_new(a.out/'SUMMARY.json',dict(fixed_input_denominator=8,qualified_inputs=sum(r['qualified'] for r in result),
        state_changed_output_unchanged=sum(r.get('outcome')=='STATE_CHANGED_OUTPUT_UNCHANGED' for r in result),
        initial_vector_different=sum(r.get('initial_logits_bytes_equal') is False for r in result),
        kv_serialization_different=sum(r.get('kv_bytes_equal') is False for r in result),
        all_six_endpoints_match_R=sum(r.get('all_six_endpoints_match_R',False) for r in result),
        matching_local_consumers_differ_from_C1=sum(r.get('outcome')=='MATCHING_LOCAL_CONSUMERS_DIFFER_FROM_C1' for r in result),
        natural_producer_endpoint_changes=sum(r.get('natural_endpoints_equal') is False for r in result),
        source_records_sha256=wp.sha_file(a.records),audited_summary_sha256=wp.sha_file(a.analysis/'SUMMARY.json'),
        scope=plan['claim_scope'],performance_claims=False))
    print(wp.read(a.out/'SUMMARY.json'))

if __name__=='__main__':main()
