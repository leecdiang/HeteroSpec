"""Recompute the stopped-at-admission result from preserved evidence; no GPU use."""
import argparse
import csv
import io
import json
from pathlib import Path
import experiment

def csv_bytes(fields, rows):
    f=io.StringIO(newline=''); w=csv.DictWriter(f, fieldnames=fields)
    w.writeheader(); w.writerows(rows)
    return f.getvalue().encode('utf-8')

def derive(root):
    freeze=experiment.read(root/'FREEZE.json')
    assert freeze['status']=='STOPPED_INCONSISTENCY' and not freeze['execution_admitted']
    assert freeze['scientific_requests_started']==0 and freeze['scientific_slots_started']==[]
    plan=experiment.read(root/'UNREGISTERED_PLAN.json')
    assert plan['blocks']==experiment.schedule(plan['panel'],plan['seed'])
    assert plan['registered'] is False and plan['executed'] is False
    for name, expected in experiment.SOURCE_BLOBS.items():
        assert experiment.blob((root/'raw'/name).read_bytes())==expected
    for name, expected in experiment.RESULT_BLOBS.items():
        assert experiment.blob((root/'raw'/name).read_bytes())==expected
    # Every pinned archive-contained raw input must match the phase-0 freeze.
    for item in freeze['files']:
        old=Path(item['path'])
        if old.parent.name=='raw': target=root/'raw'/old.name
        elif old.name=='UNREGISTERED_PLAN.json': target=root/old.name
        else: continue
        assert target.stat().st_size==item['bytes'] and experiment.sha(target)==item['sha256']
    result=experiment.analyze_blocks(plan,[])
    result.update(status='STOPPED_PHASE0',requests_started=0,processes_started=0,
                  scientific_failures=0,admission_inconsistencies=freeze['mismatches'],
                  missing_started_slots=0,planned_unstarted_slots=1620,
                  sessions=[dict(session=s,status='NOT_STARTED',requests_started=0,
                                 log_latency_contrast=None) for s in range(6)],
                  claim_supported_by_new_evidence=False,
                  interpretation='NO_NEW_EVIDENCE; not a null or negative cost result')
    slots=[]
    for b in plan['blocks']:
        for task, kind, slot in [(None,'warmup',b['id']+'/WARM')]+[
            (t,'reference' if b['arm']=='R' else 'comparison',b['id']+'|'+t) for t in b['tasks']]:
            slots.append(dict(session=b['session'],family=b['family'],block=b['id'],
                              arm=b['arm'],task=task or '',kind=kind,slot=slot,status='NOT_STARTED',
                              latency_ms='',pid='',output_ids='',eog_cap=''))
    assert len(slots)==1620
    contract=experiment.read(root/'raw/MODEL_CONTRACT.json')
    contexts=[]
    for family in experiment.FAMILIES:
        metadata=contract['families'][family]['architecture_shapes']['target']
        layers=[v for k,v in metadata.items() if k.endswith('.block_count')]
        assert len(layers)==1
        count=layers[0]
        task=sorted(plan['panel'][family],key=lambda t:(-len(t['prompt_ids']),t['id']))[0]
        for layer in (0,count//2,count-1):
            for phase in ('prefill','continuation'):
                for q in (1,2,3,4):
                    for op in ('QK','softmax','AV'):
                        contexts.append(dict(family=family,layer=layer,phase=phase,q=q,
                            min_key=0 if q in (1,3) else 128,task=task['id'],operator=op,
                            status='NOT_STARTED_E2_GATE',MQ_PQ_bitwise='',MQ_QB_bitwise='',
                            PQ_QB_bitwise='',max_error='',ULP='',first_divergence=''))
    return {'ANALYSIS.json':experiment.encoded(result),
            'UNSTARTED_SLOTS.csv':csv_bytes(list(slots[0]),slots),
            'E1_NUMERICAL.csv':csv_bytes(list(contexts[0]),contexts)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True); p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=False)
    for name,body in derive(a.input).items():
        with (a.out/name).open('xb') as f:f.write(body)
    print('Recomputed stopped-at-admission analysis: 0 starts; all estimates withheld.')

if __name__=='__main__':main()
