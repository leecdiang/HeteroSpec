"""CPU-only prospective task plan. No CUDA imports or execution dispatcher."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random

PARENT = 'd82ec4097adfa032886040e075e71e41cfeb5855'
ARMS = ('PQ', 'QB_A', 'QH_C', 'QB_B')
LAYOUT = dict(PQ='PQ', QB_A='QB', QH_C='QH_C', QB_B='QB')
ORDERS = ((0, 1, 3, 2), (1, 2, 0, 3), (2, 3, 1, 0), (3, 0, 2, 1))
PRODUCER = ('QB_permuted', 'QH_permuted', 'QB_compact', 'QH_compact')


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def make_plan(graph='dual'):
    if graph not in ('dual', 'off-only'):
        raise ValueError('graph plan must be dual or off-only')
    modes = ['OFF', 'ON'] if graph == 'dual' else ['OFF']
    cases = []
    for gid, q, keys, storage in [('q2-k1023', 2, 1023, 'permuted'),
                                ('q2-k1024', 2, 1024, 'permuted'),
                                ('q2-k1025', 2, 1025, 'permuted'),
                                ('q2-k256', 2, 256, 'permuted'),
                                ('q2-compact', 2, 256, 'compact'),
                                ('q1-short', 1, 128, 'permuted')]:
        for value in (0, 1):
            cases.append(dict(case_id=f'{gid}-v{value}', geometry_id=gid, q=q,
                              keys=keys, storage=storage, value=value, d=128,
                              Hq=32, Hkv=8, mask='causal', seed=20261018+value,
                              parent_case_id=f'{gid}-v{value}'))
    tasks = []

    def add(stage, cid, mode, arm, block=0, position=0, optional=False, **extra):
        qualification = stage in ('qualification', 'producer_qualification')
        reference = stage == 'reference'
        tasks.append(dict(task_id=f'{stage}-{len(tasks):04d}', stage=stage,
                          case_id=cid, graph_mode=mode, arm=arm,
                          block=block, position=position, optional=optional,
                          warmups=0 if reference else 2 if qualification else 8,
                          measured_calls=1 if reference else 32 if qualification else 30,
                          session=f'{stage}-s{block//4}' if stage in ('confirm', 'producer') else 'preparation',
                          requires=['input_source_freeze', 'independent_reference'] if qualification else
                                   ['input_source_freeze'] if reference else
                                   ['numerical_qualification', 'execution_freeze', 'mode_evidence'] +
                                   (['producer_decision'] if stage == 'producer' else []), **extra))
        if optional and 'producer_decision' not in tasks[-1]['requires']:
            tasks[-1]['requires'].append('producer_decision')

    for c in cases:
        for query in range(c['q']):
            for repeat in range(2):
                add('reference', c['case_id'], 'OFF', 'PQ', repeat,
                    layout='PQ', query_index=query)
        for mode in modes:
            for layout in ('PQ', 'QB', 'QH_C'):
                for repeat in range(2):
                    add('qualification', c['case_id'], mode, layout, repeat, layout=layout)
    for block in range(8):
        ordered = cases.copy()
        random.Random(20261018+block).shuffle(ordered)
        for c in ordered:
            index = cases.index(c)
            mode_order = modes if (block+index) % 2 == 0 else modes[::-1]
            for mode_position, mode in enumerate(mode_order):
                for position, ai in enumerate(ORDERS[(block+index) % 4]):
                    arm = ARMS[ai]
                    add('confirm', c['case_id'], mode, arm, block, position,
                        layout=LAYOUT[arm], mode_position=mode_position,
                        cost_view='resident_graph')

    # Optional integrated Q materialization/update transaction; K/V/mask resident.
    # q2 references already exist above; q4 gets new independent serial captures.
    producer_cases = [dict(case_id=f'producer-q{q}-v{v}', q=q, value=v,
                           source_case_id=f'q{q}-k256-v{v}') for q in (2, 4) for v in (0, 1)]
    producer_mode = modes[-1]  # ON only if admitted, otherwise off-only plan.
    for c in producer_cases:
        if c['q'] == 4:
            for query in range(4):
                for repeat in range(2):
                    add('reference', c['case_id'], 'OFF', 'PQ', repeat, optional=True,
                        layout='PQ', query_index=query)
        for arm in PRODUCER:
            layout = 'QB' if arm.startswith('QB_') else 'QH_C'
            for repeat in range(2):
                add('producer_qualification', c['case_id'], producer_mode, arm, repeat,
                    optional=True, layout=layout, storage=arm.split('_')[1])
    for block in range(8):
        ordered = producer_cases.copy()
        random.Random(20261118+block).shuffle(ordered)
        for c in ordered:
            index = producer_cases.index(c)
            for position, ai in enumerate(ORDERS[(block+index) % 4]):
                arm = PRODUCER[ai]
                add('producer', c['case_id'], producer_mode, arm, block, position, True,
                    layout='QB' if arm.startswith('QB_') else 'QH_C',
                    storage=arm.split('_')[1], cost_view='integrated_q_update')
    counts = {}
    for t in tasks:
        k=t['stage']+('/optional' if t['optional'] else '/core')
        r=counts.setdefault(k, dict(hosts=0, calls=0))
        r['hosts']+=1; r['calls']+=t['warmups']+t['measured_calls']
    p=dict(schema=1, parent_commit=PARENT, scientific_state='NOT_RUN', graph_plan=graph,
           modes=modes, cases=cases, producer_cases=producer_cases, tasks=tasks, counts=counts,
           factor_edges=[['q2-k1023','q2-k1024','length'],['q2-k1024','q2-k1025','length'],
                         ['q2-k256','q2-compact','storage']],
           extra_caps=dict(capability_hosts=12, trace_hosts=24, calls_per_extra_host=64,
                           elapsed_hours=6, delivery_reserve_minutes=45),
           unresolved=['native adapter', 'capability and actual graph evidence', 'input/reference hashes',
                       'source/runtime freeze', 'actual session IDs', 'trace availability'],
           scope='fixed-input synthetic characterization, no natural decoder or hardware benefit claim')
    p['plan_sha256']=digest(p)
    validate(p)
    return p


def validate(p):
    bare=dict(p); saved=bare.pop('plan_sha256')
    if digest(bare)!=saved: raise ValueError('plan hash mismatch')
    tasks=p['tasks']; ids=[t['task_id'] for t in tasks]
    if len(ids)!=len(set(ids)): raise ValueError('duplicate task')
    if any(t['warmups']+t['measured_calls']>64 for t in tasks): raise ValueError('call bound')
    for stage in ('confirm','producer'):
        groups={}
        for t in tasks:
            if t['stage']==stage:
                groups.setdefault((t['case_id'],t['graph_mode'],t['block']//4),[]).append(t)
        for rows in groups.values():
            pos=Counter((t['arm'],t['position']) for t in rows); transitions=Counter()
            for b in {t['block'] for t in rows}:
                order=sorted((t for t in rows if t['block']==b),key=lambda t:t['position'])
                transitions.update((x['arm'],y['arm']) for x,y in zip(order,order[1:]))
            if len(pos)!=16 or set(pos.values())!={1} or len(transitions)!=12 or set(transitions.values())!={1}:
                raise ValueError('unbalanced cycle')
    return True


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--graph',choices=('dual','off-only'),default='dual')
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(); p=make_plan(args.graph)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as f: json.dump(p,f,indent=2);f.write('\n')
    print(json.dumps(dict(plan_sha256=p['plan_sha256'],counts=p['counts']),indent=2))
