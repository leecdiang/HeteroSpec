"""Read immutable inherited evidence; write only new research-plan summaries.

This is an output-equivalence audit, not a model runner or a causal experiment.
"""
import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path

PLAN = 'docs/research/execution_minimization_v1'
EOG = {128247, 151643, 151645, 151662, 151663, 151664}


def load_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON field: ' + key)
            result[key] = value
        return result
    return json.loads(data, object_pairs_hook=pairs)


def endpoint(record):
    ids = record['ids']
    reason = 'limit' if record['endpoint'] == 'CAP128' else record['endpoint']
    if not ids or any(type(i) is not int or not 0 <= i < 151936 for i in ids):
        raise ValueError('Invalid generated IDs')
    if len(ids) > 128 or any(i in EOG for i in ids[:-1]):
        raise ValueError('Outside the frozen inclusive-EOG/cap128 contract')
    if reason not in ('EOS', 'limit') or (reason == 'EOS') != (ids[-1] in EOG):
        raise ValueError('Stop reason disagrees with terminal ID')
    if reason == 'limit' and len(ids) != 128:
        raise ValueError('Incomplete capped output')
    return len(ids), reason, ids[-1]


def equivalent(left, right):
    return left['ids'] == right['ids'] and endpoint(left) == endpoint(right)


def index_context(context):
    tasks, conditions = context['tasks'], context['known_conditions']
    if len(tasks) != len(set(tasks)) or len(conditions) != len(set(conditions)):
        raise ValueError('Duplicate task or condition')
    result = {}
    for record in context['records']:
        endpoint(record)
        key = record['task'], record['condition'], record['rep']
        if key in result:
            raise ValueError('Duplicate task/condition/repetition')
        result[key] = record
    expected = {(t, c, r) for t in tasks for c in conditions for r in (1, 2, 3)}
    if set(result) != expected:
        raise ValueError('Missing or unexpected observation')
    return result


def pair_metrics(context, left, right):
    index = index_context(context)
    n = len(context['tasks'])
    result = dict(context=context['name'], left=left, right=right,
                  task_units=n, expected_paired_observations=3*n,
                  observed_paired_observations=0, all_three_equal_tasks=None,
                  joint_equal_observations=None, array_equal_observations=None,
                  boundary_equal_observations=None, status='UNKNOWN')
    if left not in context['known_conditions'] or right not in context['known_conditions']:
        return result
    array = boundary = joint = task_count = 0
    for task in context['tasks']:
        matches = []
        for rep in (1, 2, 3):
            a, b = index[task, left, rep], index[task, right, rep]
            ae, be = a['ids'] == b['ids'], endpoint(a) == endpoint(b)
            array += ae
            boundary += be
            joint += ae and be
            matches.append(ae and be)
        task_count += all(matches)
    result.update(observed_paired_observations=3*n, all_three_equal_tasks=task_count,
                  joint_equal_observations=joint, array_equal_observations=array,
                  boundary_equal_observations=boundary, status='OBSERVED')
    return result


def task_cases(context):
    index = index_context(context)
    rows = []
    for task in context['tasks']:
        baseline = all(equivalent(index[task, 'N0', r], index[task, 'R', r]) for r in (1, 2, 3))
        changed = all(equivalent(index[task, 'N1', r], index[task, 'R', r]) for r in (1, 2, 3))
        a, b = index[task, 'N0', 1], index[task, 'N1', 1]
        first = next((i for i, (x, y) in enumerate(zip(a['ids'], b['ids'])) if x != y), None)
        if first is None and len(a['ids']) != len(b['ids']):
            first = min(len(a['ids']), len(b['ids']))
        transition = ('retained_match' if baseline and changed else 'repair' if changed
                      else 'regression' if baseline else 'persistent_deviation')
        rows.append(dict(context=context['name'], task=task, transition=transition,
                         N0_N1_all_three_equal=all(equivalent(index[task, 'N0', r], index[task, 'N1', r]) for r in (1, 2, 3)),
                         first_difference_index_0_rep1=first,
                         N0_length_rep1=len(a['ids']), N1_length_rep1=len(b['ids']),
                         U2_N1_all_three_equal=(all(equivalent(index[task, 'U2', r], index[task, 'N1', r]) for r in (1, 2, 3))
                                               if 'U2' in context['known_conditions'] else 'UNKNOWN')))
    return rows


def source_bytes(repo, entry):
    # Content-addressed Git reads do not modify the user's working files.
    data = subprocess.check_output(['git', 'cat-file', 'blob', entry['git_blob_sha']], cwd=repo)
    if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Source binding failed: ' + entry['path'])
    return data


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def write_csv(path, rows):
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--bindings', type=Path)
    args = parser.parse_args()
    out = args.out or args.repo / PLAN
    out.mkdir(parents=True, exist_ok=True)
    bindings = load_json((args.bindings or out / 'SOURCE_BINDINGS.json').read_bytes())
    sources = {entry['path']: source_bytes(args.repo, entry) for entry in bindings['files']}
    snapshot_path = 'benchmarks/diagnostic_selection_feasibility_v1/inputs/OUTCOMES.json'
    snapshot = sources[snapshot_path]
    original_binding = load_json(sources['benchmarks/diagnostic_selection_feasibility_v1/INPUT_SNAPSHOT_BINDING.json'])
    if hashlib.sha256(snapshot).hexdigest() != original_binding['sha256']:
        raise ValueError('Inherited normalized arrays fail their original binding')
    contexts = load_json(snapshot)
    pairs = [('N0', 'N1'), ('U2', 'N1'), ('U2', 'N0'), ('N0', 'R'), ('N1', 'R'), ('U2', 'R')]
    table, cases, context_results = [], [], []
    for context in contexts:
        index = index_context(context)
        rows = task_cases(context)
        cases.extend(rows)
        local_pairs = pairs + ([('T0', 'N0'), ('T1', 'N1')] if 'T1' in context['known_conditions']
                               else [('H1', 'N1')])
        table.extend(pair_metrics(context, a, b) for a, b in local_pairs)
        context_results.append(dict(context=context['name'], task_units=len(context['tasks']),
                                    inherited_records=len(context['records']),
                                    all_records_exposed=True,
                                    transitions={label: sum(r['transition'] == label for r in rows)
                                                 for label in ('retained_match', 'repair', 'regression', 'persistent_deviation')},
                                    stable_tasks={c: sum(all(equivalent(index[t,c,1], index[t,c,r]) for r in (2,3))
                                                         for t in context['tasks']) for c in context['known_conditions']}))
    write_csv(out / 'EVIDENCE_TABLE.csv', table)
    write_csv(out / 'TASK_CASES.csv', cases)
    write_json(out / 'AUDIT_RESULTS.json', dict(
        status='PASS', source_commit=bindings['source_commit'], source_tree=bindings['source_tree'],
        bound_source_files=len(sources), inherited_analysis_records=sum(len(c['records']) for c in contexts),
        contexts=context_results, comparisons=table,
        new_model_runs=0, new_gpu_forwards=0,
        causal_experiment_status='NOT_EXECUTED', transfer_validation_status='NOT_EXECUTED',
        scope='CPU recomputation of inherited normalized arrays; no independent rerun of physical experiments, full raw archives, or new mechanism evidence.'))
    print('PASS: immutable evidence; 1005 inherited records; 67 task-context units; no new inference.')


if __name__ == '__main__':
    main()
