"""Optional CPU readers. Availability of these functions grants no execution."""
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
from analyze import geometric
from support import need,positive,digest_value,normalize


def b2(rows):
    """Descriptive process clusters, never 64 independent timing samples."""
    spec=spec_from_file_location('sb217_design',Path(__file__).parent.parent/'design_checks.py')
    module=module_from_spec(spec);spec.loader.exec_module(module)
    expected=module.plan()['b2'];need(len(rows)==128,'Incomplete B2 panel')
    by_id={r['operation_id']:r for r in rows};need(len(by_id)==128,'Duplicate B2 operation')
    need(set(by_id)=={op['id']for w in expected for op in w['operations']},'B2 registered identities')
    cells={c:[]for c in range(4)};previous_end=0
    for worker in expected:
        group=[]
        for op in worker['operations']:
            r=by_id[op['id']];group.append(r)
            need(r['worker_id']==worker['id'] and r['role']==op['role'] and r['path']==op['path'],
                 'B2 process/warm/order mismatch')
            need(r['unit']=='s','B2 units');positive(r['elapsed_s'])
            need(r['start_ns']>=previous_end and r['end_ns']>r['start_ns'] and
                 r['start_ns']<=r['fence_ns']<=r['end_ns'] and
                 abs((r['end_ns']-r['start_ns'])/1e9-r['elapsed_s'])<1e-8,'B2 host clock/order')
            previous_end=r['end_ns']
            need(r['physical_widths']==([4,4] if op['path']=='A' else [8]) and
                 r['output_rows']==8 and r['all_outputs_owned'] is True,'B2 physical/full-output contract')
            digest_value(r['input_state_sha256']);digest_value(r['output_sha256'])
            need(len(r['tokens'])==8,'B2 eight-token input')
        for k in ('input_state_sha256','tokens','output_sha256'):
            need(all(r[k]==group[0][k]for r in group),'B2 different initial state/input/output')
        measured=[r for r in group if r['role']=='measured']
        ratio=sum(r['elapsed_s']for r in measured if r['path']=='B')/sum(r['elapsed_s']for r in measured if r['path']=='A')
        cells[worker['cell']].append(dict(worker_id=worker['id'],ratio_B_over_A=ratio,rows=group))
    return dict(phase='B2',scope='exposed_root_descriptive_by_process_not_32B_or_live',
                independent_clusters_per_cell=4,not_independent_operation_samples=True,
                cells={c:dict(processes=values,geometric_B_over_A=geometric(v['ratio_B_over_A']for v in values),
                              minimum=min(v['ratio_B_over_A']for v in values),maximum=max(v['ratio_B_over_A']for v in values))
                       for c,values in cells.items()})


def replica(primary_rows,replica_rows):
    primary=normalize(primary_rows,'S3');second=normalize(replica_rows,'REPLICA')
    mapping=(0,1,2,6,7,8);result=[]
    for slot,root in enumerate(mapping):
        p=[r for r in primary if r['slot']==root and r['role']=='measured']
        s=[r for r in second if r['slot']==slot and r['role']=='measured']
        need(len({r['input_sha256']for r in p+s})==1,'Replica root identity differs')
        contrasts=[]
        for candidate,base in (('C','B'),('B','G'),('C','G')):
            def ratio(rows,rounds):
                lookup={(r['block'],r['arm']):r['elapsed_s']for r in rows}
                return geometric(lookup[b,candidate]/lookup[b,base]for b in range(rounds))
            a,b=ratio(p,4),ratio(s,3)
            contrasts.append(dict(candidate=candidate,baseline=base,primary_all_four_rounds=a,
                                  replica_all_three_rounds=b,replica_over_primary=b/a))
        result.append(dict(replica_slot=slot,primary_root_slot=root,contrasts=contrasts))
    return dict(phase='REPLICA',roots=6,pooled=False,scope='two_devices_descriptive_no_new_independent_roots',
                paired_root_tables=result)
