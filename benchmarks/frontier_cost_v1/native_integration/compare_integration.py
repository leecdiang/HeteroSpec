"""Compare saved CPU worker vectors, native sequence bytes, and exact logical receipts."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

SAME_FIELDS=['arm','k','lifecycle','capture','draft_enabled','observed_scope','context_scope_fixed',
             'producer','draft_producer','draft_ubatch','proposal_mode','target_output_reserve',
             'cycles','ids','eog','length','terminal_id','stop_reason','target_final_kv','draft_final_kv',
             'target_caller_trace','target_physical_width_hist','target_physical_by_phase',
             'phase_executions','target_calls','prompt_tokens','prompt_ids','context_teardown_completed']


def read(p):return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('run',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise FileExistsError(a.out)
    plan=read(a.run/'PLAN.json');summary=read(a.run/'RUN_SUMMARY.json')
    if summary['status']!='EXECUTED_PENDING_OFFLINE_COMPARISON':raise ValueError('Incomplete execution')
    report={'schema':'heterospec.cpu-integration-comparison.v1','status':'STARTED','requests':[],
            'full_vector_pairs':0,'native_sequence_pairs':0,'compared_bytes_per_side':0,
            'tail_skips':0,'tail_recoveries':0,'coverage':{},'GPU_qualification':'NOT_RUN','performance_claim':False}
    coverage={k:0 for k in ['initial_CAP','initial_EOG','accepted_terminal_full','accepted_terminal_partial',
                            'bonus_terminal','correction','CAP','EOG','dirty_resident_resets','crossing_extent_256']}
    try:
        for cell in plan['matrix']:
            left=a.run/(cell['name']+'_mode0');right=a.run/(cell['name']+'_mode1')
            lr=read(left/'RESULT.json');rr=read(right/'RESULT.json')
            if lr['status']!='COMPLETE' or rr['status']!='COMPLETE':raise ValueError('Incomplete process')
            if lr['actual_context']!=rr['actual_context']:raise ValueError('Context config differs')
            if lr['actual_context']['target_ubatch']!=32 or lr['actual_context']['draft_ubatch']!=4:
                raise ValueError('Actual M2 ubatch differs')
            if lr['eog_ids']!=[127] or rr['eog_ids']!=[127]:raise ValueError('Native EOG vocabulary differs')
            job=read(a.run/cell['job'])
            for index,entry in enumerate(job['inputs']):
                name=entry['name'];ld=left/name;rd=right/name;l=read(ld/'RECEIPT.json');r=read(rd/'RECEIPT.json')
                for key in SAME_FIELDS:
                    if l[key]!=r[key]:raise ValueError(f'{cell["name"]}/{name}: {key} differs')
                cycles=r['cycles'];skips=sum(c['accepted']<cell['k'] for c in cycles);recovers=len(cycles)-skips
                if r['draft_tail_skipped']!=skips or r['draft_tail_recovered']!=recovers:raise ValueError('Tail accounting differs')
                if l['draft_calls']-r['draft_calls']!=skips:raise ValueError('Saved native calls differ')
                if l['draft_tail_skipped']!=0 or l['draft_tail_recovered']!=0:raise ValueError('Eager arm mislabeled')
                la=read(ld/'AUDIT.json');ra=read(rd/'AUDIT.json')
                if la!=ra:raise ValueError(f'{cell["name"]}/{name}: capture order/geometry differs')
                actual=Counter((e['role'],e['kind']) for e in la)
                expected=Counter({('target','requested-logits'):1+len(cycles)*(cell['k']+1),
                                  ('draft','requested-logits'):len(cycles)*cell['k'],
                                  ('target','reset'):1,('draft','reset'):1,
                                  ('target','trim'):len(cycles),('draft','trim'):2*len(cycles),
                                  ('target','terminal'):1,('draft','terminal'):1})
                if actual!=+expected:raise ValueError('Incomplete frontend-read vector or state coverage')
                vp=sp=0
                for event in la:
                    f=event['file'];x=(ld/'audit'/f).read_bytes();y=(rd/'audit'/f).read_bytes()
                    if x!=y:raise ValueError(f'{cell["name"]}/{name}/{f}: bytes differ')
                    report['compared_bytes_per_side']+=len(x)
                    if event['kind']=='requested-logits':
                        if len(x)!=event['vocab']*4:raise ValueError('Vector length differs')
                        if not all(math.isfinite(v[0]) for v in struct.iter_unpack('<f',x)):raise ValueError('Nonfinite vector')
                        vp+=1
                    else:
                        if len(x)!=event['bytes']:raise ValueError('Native state length differs')
                        if not event['geometry']['dense'] or not event['geometry']['native_append_head_guard_passed']:
                            raise ValueError('Native append geometry not established')
                        if event['kind']=='reset' and event['geometry']['used']!=0:
                            raise ValueError('Reset did not clear active sequence')
                        sp+=1
                report['full_vector_pairs']+=vp;report['native_sequence_pairs']+=sp
                report['tail_skips']+=skips;report['tail_recoveries']+=recovers
                stop=r['stop_reason'];coverage[stop]+=1
                if not cycles:coverage['initial_'+stop]+=1
                if index>0:coverage['dirty_resident_resets']+=1
                for cycle in cycles:
                    if cycle['rejected']:coverage['correction']+=1
                    if cycle['done'] and cycle['commit_kind']=='accepted':
                        coverage['accepted_terminal_full' if cycle['accepted']==cell['k'] else 'accepted_terminal_partial']+=1
                    if cycle['done'] and cycle['commit_kind']=='bonus':coverage['bonus_terminal']+=1
                if any(len(set(e['expected_extents']))>1 and 256 in e['expected_extents'] for e in r['phase_executions']):
                    coverage['crossing_extent_256']+=1
                report['requests'].append({'cell':cell['name'],'name':name,'cycles':len(cycles),'stop_reason':stop,
                    'full_vector_pairs':vp,'native_sequence_pairs':sp,'tail_skips':skips,'tail_recoveries':recovers,
                    'accepted_per_cycle':[c['accepted'] for c in cycles],
                    'receipt_sha256':{'eager':hashlib.sha256((ld/'RECEIPT.json').read_bytes()).hexdigest(),
                                      'deferred':hashlib.sha256((rd/'RECEIPT.json').read_bytes()).hexdigest()}})
        if not all(coverage.values()):raise ValueError('A declared branch was not observed: '+str(coverage))
        report['status']='PASS';report['request_pairs']=len(report['requests']);report['coverage']=coverage
        report['scope']='Unchanged worker provision/request function, actual greedy vectors and native EOS metadata; synthetic F32 CPU fixtures, no text tokenization or production/GPU qualification.'
    except Exception as exc:
        report['status']='FAILED';report['error']=str(exc);report['coverage']=coverage
        a.out.write_text(json.dumps(report,indent=2)+'\n');raise
    a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='requests'},indent=2))


if __name__=='__main__':main()
