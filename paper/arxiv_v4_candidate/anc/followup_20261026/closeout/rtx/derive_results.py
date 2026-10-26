"""Post-execution CPU summaries; never launches a native/model process."""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import shutil

WORK=Path(__file__).parent
REPO=WORK/'HeteroSpec'
HERE=REPO/'benchmarks/rtx_jsa_closeout_v1/revision_a'
FAMILIES=['Qwen','SmolLM2','Llama']

def read(path):return json.loads(path.read_bytes())
def save(path,value):
    with path.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def first_difference(left,right):
    return next((i for i,(a,b) in enumerate(zip(left,right)) if a!=b),None if len(left)==len(right) else min(len(left),len(right)))

def main(verification,out=None):
    config=read(HERE/'F0B_EXECUTION.json');root=Path(config['run_root'])
    assert not (root/'EXECUTION.lock').exists() and (root/'TIMING_RECORDS.json').is_file()
    result=out or HERE/'results';result.mkdir(exist_ok=False)
    for path in sorted(verification.iterdir()):
        if path.is_file():shutil.copyfile(path,result/path.name)
    for name in ['E1_SUMMARY.json','E1_CAPTURE_COMPLETENESS.json','MODEL_CONTRACT.json','COUNTER_SEMANTICS.md']:
        shutil.copyfile(root/name,result/name)
    summary=read(verification/'VERIFICATION.json')
    slots=read(verification/'ALL_1776_SLOTS.json')
    assert len(slots)==1776
    events=[read(p) for p in sorted((root/'ledger').glob('*.json'))]
    save(result/'ACTUAL_EXECUTION_ORDER.json',{'source':'Immutable ledger sequence, including load/warmup/measurement charges; no sorting by outcome.', 'events':events})
    life=read(verification/'PROCESS_LIFETIMES.json')
    cleanup=[{'worker':str(p.parent.relative_to(root/'runs')),**read(p)} for p in (root/'runs').glob('*/*/*/CLEANUP.json')]
    resources={'study_uuid':config['study_uuid'],'budget':config['budget'],'actual_by_stage':{},
        'historical_E2_charges_unchanged':read(HERE/'F0A_CALIBRATION.json')['old_E2_charges'],
        'historical_S0_charges_unchanged':read(HERE/'F0A_CALIBRATION.json')['previous_S0'],
        'all_workers_exit_verified':len(cleanup)==summary['charged_workers'] and all(r.get('exit_verified') is True for r in cleanup),
        'all_watchdog_failures':[r for r in cleanup if r.get('watchdog_failure') is not None],
        'worker_problems':summary['worker_problems'],'raw_capture_failures':summary['raw_capture_failures'],
        'owned_worker_seconds':sum(r['seconds'] for r in life),'maximum_worker_seconds':max(r['seconds'] for r in life),
        'request_slot_counts':dict(collections.Counter(r['status'] for r in slots)),
        'completed_E2_categories':dict(collections.Counter(r.get('category') for r in slots if r['stage']=='E2' and r['status']=='COMPLETED')),
        'request_ceiling':1776,'worker_ceiling':888,'no_scientific_retry':True,
        'resource_scope':'Native scientific lifetimes; CPU preparation, audit, transport and packaging are separate and preserved in their receipts.'}
    for stage in ['calibration','E1','E2']:
        selected=[e for e in events if e['stage']==stage]
        lifetimes=[r['seconds'] for r in life if r['worker'].startswith(stage+'/')]
        resources['actual_by_stage'][stage]={'workers':sum(e['kind']=='load' for e in selected),
            'requests':sum(e['kind']!='load' for e in selected),'owned_seconds':sum(lifetimes),
            'maximum_worker_seconds':max(lifetimes,default=None)}
    raw_manifest=[json.loads(line) for line in (verification/'RAW_FILE_MANIFEST.jsonl').read_bytes().splitlines()]
    resources['raw_files']=len(raw_manifest);resources['raw_bytes']=sum(r['bytes'] for r in raw_manifest)
    resources['raw_manifest_sha256']=sha(verification/'RAW_FILE_MANIFEST.jsonl')
    save(result/'RESOURCE_LEDGER.json',resources)
    coverage=[];counterexamples=[];attempted=set();complete=set()
    for family in FAMILIES:
        for index,task in enumerate(config['panel'][family]):
            row={'family':family,'input_index':index,'task_id':task['id'],'stratum':task['stratum'],
                'prompt_tokens':task['prompt_token_count'],'arms':{}}
            records={}
            for arm in ['R','PQ','QB','NATIVE_FAST']:
                worker=root/'runs/E1'/family/f'{index:02d}_{arm}'
                paths=sorted(worker.glob('requests/*/RECORD.json'))
                pair=[read(p) for p in paths];heavy=[r for r in pair if r['mode']=='heavy']
                if not heavy:
                    row['arms'][arm]={'status':'NOT_RUN'};continue
                assert len(heavy)==1
                record=heavy[0];records[arm]=record;attempted.add(task['id'])
                groups={};q=collections.Counter();visible=[];extents=[];decode_events=collections.Counter()
                with (worker/'capture/observer.jsonl').open('rb') as stream:
                    for line in stream:
                        event=json.loads(line)
                        if event.get('event')!='geometry':continue
                        key=(event['layer'],event['phase'])
                        group=groups.setdefault(key,{'records':0,'q':set(),'visible_min':None,'visible_max':0,'physical':set(),'caller_rows':set(),'example':event})
                        group['records']+=1;group['q'].add(event['q_occupied']);group['physical'].add(event['physical_key_extent']);group['caller_rows'].add(event['caller_rows'])
                        low=min(event['visible_keys']);high=max(event['visible_keys'])
                        group['visible_min']=low if group['visible_min'] is None else min(group['visible_min'],low)
                        group['visible_max']=max(group['visible_max'],high)
                        if event['phase']=='continuation':
                            q[event['q_occupied']]+=1;visible.extend(event['visible_keys']);extents.append(event['physical_key_extent'])
                layer_rows=[]
                for (layer,phase),group in sorted(groups.items()):
                    layer_rows.append({'layer':layer,'phase':phase,'records':group['records'],
                        'observed_q_occupied':sorted(group['q']),'visible_keys_range':[group['visible_min'],group['visible_max']],
                        'physical_key_extents':sorted(group['physical']),'caller_rows':sorted(group['caller_rows']),
                        'example_geometry':group['example']})
                with (worker/'trace.jsonl').open('rb') as stream:
                    for line in stream:
                        event=json.loads(line);decode_events[event.get('event')]+=1
                row['arms'][arm]={'status':'OBSERVED','output_length':record['output']['length'],
                    'stop_reason':record['output']['stop_reason'],'terminal_id':record['output']['terminal_id'],
                    'heavy_count_endpoint_equal':len(pair)==2 and pair[0]['output']==pair[1]['output'],
                    'continuation_q_geometry_counts':dict(q),'q_gt_one_verification_observed':any(v>1 for v in q),
                    'continuation_visible_keys_range':[min(visible),max(visible)] if visible else None,
                    'continuation_physical_key_extents':sorted(set(extents)),
                    'layer_phase_geometry':layer_rows,'native_event_counts':dict(decode_events)}
            if all(a in records for a in ['R','PQ','QB']):
                row['PQ_QB_endpoint_equal']=records['PQ']['output']==records['QB']['output']
                row['primary_reference_equal']=all(records[a]['output']==records['R']['output'] for a in ['PQ','QB'])
                if row['primary_reference_equal']:complete.add(task['id'])
                for arm in ['PQ','QB','NATIVE_FAST']:
                    if arm in records and records[arm]['output']!=records['R']['output']:
                        counterexamples.append({'stage':'E1','family':family,'task_id':task['id'],'input_index':index,
                            'prompt_tokens':task['prompt_token_count'],'arm':arm,
                            'first_different_output_index_zero_based':first_difference(records['R']['output']['ids'],records[arm]['output']['ids']),
                            'reference_output':records['R']['output'],'observed_output':records[arm]['output'],
                            'worker':str(root/'runs/E1'/family/f'{index:02d}_{arm}')})
            coverage.append(row)
    for item in read(root/'CALIBRATION_SUMMARY.json')['results']:
        if item['arm']!='NATIVE_FAST' or not item['records']:continue
        record=item['records'][0];reference=config['calibration'][item['family']][item['input_index']]['reference_output']
        if record['output']!=reference:
            counterexamples.append({'stage':'calibration','family':item['family'],'task_id':record['task_id'],
                'arm':'NATIVE_FAST','first_different_output_index_zero_based':first_difference(reference['ids'],record['output']['ids']),
                'reference_output':reference,'observed_output':record['output'],'worker':item['worker']})
    save(result/'E1_GEOMETRY_COVERAGE.json',{'scope':'Observed heavy capture only; no inference about missing widths or unstarted inputs.',
        'planned_distinct_tasks':len({t['id'] for ts in config['panel'].values() for t in ts}),
        'attempted_distinct_tasks':len(attempted),'primary_reference_passing_distinct_tasks':len(complete),'inputs':coverage})
    save(result/'COUNTEREXAMPLES.json',counterexamples)
    print(json.dumps({'resources':resources,'counterexamples':[{k:v for k,v in row.items() if k not in ['reference_output','observed_output','worker']} for row in counterexamples],
        'planned_distinct_tasks':len({t['id'] for ts in config['panel'].values() for t in ts}),
        'attempted_distinct_tasks':len(attempted),'primary_reference_passing_distinct_tasks':len(complete)},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--verification',type=Path,required=True)
    p.add_argument('--repo',type=Path,default=REPO);p.add_argument('--out',type=Path)
    a=p.parse_args();REPO=a.repo.resolve();HERE=REPO/'benchmarks/rtx_jsa_closeout_v1/revision_a';main(a.verification,a.out)
