"""Offline original-entry evidence checks; never admit performance from PASS."""
from array import array
from collections import Counter
import argparse
import json
import math
from pathlib import Path, PurePosixPath
import sys
from protocol import CAP, DRAFT_SHA, K, TARGET_SHA, VOCAB, actual_work, canonical, digest, identity, make_plan, validate_inputs, write_new

EOG = [128247, 151643, 151645, 151662, 151663, 151664]


def read(path):
    return json.loads(Path(path).read_text())


def need(condition, message):
    if not condition:
        raise ValueError(message)


def safe(name):
    path = PurePosixPath(name)
    need(not path.is_absolute() and '..' not in path.parts and str(path) == name, 'unsafe record path')
    return Path(*path.parts)


def vector(path):
    data = Path(path).read_bytes()
    need(len(data) == VOCAB * 4, 'incomplete full vocabulary vector')
    values = array('f'); values.frombytes(data)
    if sys.byteorder != 'little':
        values.byteswap()
    need(all(math.isfinite(x) for x in values), 'nonfinite full vector')
    return data, max(range(VOCAB), key=values.__getitem__)


def logical_walk(receipt, directory, case):
    """Rebuild acceptance and terminal frontiers from actual saved full vectors."""
    need(all(type(value) is int for value in receipt['ids']) and all(type(value) is bool for value in receipt['eog']), 'endpoint JSON token/EOG types differ')
    _, pending = vector(directory/'target/initial.f32')
    ids = [pending]
    done = pending in EOG or len(ids) == CAP
    base = len(case['prompt_ids'])
    expected_vectors = {directory/'target/initial.f32'}
    for index, cycle in enumerate(receipt['cycles']):
        need(not done, 'cycle after terminal output')
        proposals = []
        decisions = []
        for role, count, output in [('draft', K, proposals), ('target', K + 1, decisions)]:
            stem = 'proposal' if role == 'draft' else 'verify'
            for row in range(count):
                path = directory/role/f'{stem}-{index}-{row}.f32'
                _, token = vector(path); output.append(token); expected_vectors.add(path)
        seed = pending
        accepted = 0; rejected = False; last = ''
        for proposal, decision in zip(proposals, decisions):
            if done:
                break
            if proposal == decision:
                accepted += 1; ids.append(proposal); last = 'accepted'
            else:
                rejected = True; pending = decision; ids.append(pending); last = 'correction'
            done = ids[-1] in EOG or len(ids) == CAP
            if rejected:
                break
        if accepted == K and not done:
            pending = decisions[K]; ids.append(pending); last = 'bonus'
            done = pending in EOG or len(ids) == CAP
        keep = base + 1 + accepted
        before = {'min': 0, 'max': base - 1}; after = {'min': 0, 'max': keep - 1}
        expected = {'cycle': index, 'base': base, 'seed': seed, 'proposals': proposals, 'decisions': decisions,
                    'accepted': accepted, 'rejected': rejected, 'commit_kind': last, 'output_length': len(ids),
                    'pending_after': None if done else pending, 'done': done, 'keep': keep,
                    'target_before': before, 'draft_before': before, 'target_after': after, 'draft_after': after,
                    'caller_rows': K + 1}
        need(canonical(cycle) == canonical(expected), 'literal acceptance/frontier mismatch')
        base = keep
    need(done, 'incomplete terminal request')
    need(receipt['ids'] == ids and receipt['eog'] == [token in EOG for token in ids], 'endpoint does not follow captured vectors')
    need(receipt['length'] == len(ids) and receipt['terminal_id'] == ids[-1], 'endpoint length/terminal differs')
    need(receipt['stop_reason'] == ('EOG' if ids[-1] in EOG else 'CAP'), 'wrong stop reason')
    actual_vectors = set((directory/'target').glob('*.f32')) | set((directory/'draft').glob('*.f32'))
    need(actual_vectors == expected_vectors, 'missing or extra consumer vectors')
    states = ['initial'] + ['commit-'+str(i) for i in range(len(receipt['cycles']))] + ['terminal']
    need({p.name for p in (directory/'target/state').iterdir()} == set(states), 'target checkpoint set differs')
    for name in states:
        checkpoint = directory/'target/state'/name
        expected_members = {'frontier.f32', 'sequence.bin'}
        if name != 'terminal':
            expected_members.add('capture.txt')
        need({p.name for p in checkpoint.iterdir()} == expected_members, 'checkpoint members differ')
        vector(checkpoint/'frontier.f32')
        if name == 'initial' or not receipt['cycles']:
            consumer = directory/'target/initial.f32'
        else:
            index = len(receipt['cycles']) - 1 if name == 'terminal' else int(name.removeprefix('commit-'))
            consumer = directory/'target'/f'verify-{index}-{receipt["cycles"][index]["accepted"]}.f32'
        need((checkpoint/'frontier.f32').read_bytes() == consumer.read_bytes(), 'checkpoint frontier not the requested consumer')
        if name != 'terminal':
            metadata = dict(line.split('=', 1) for line in (checkpoint/'capture.txt').read_text().splitlines())
            maximum = len(case['prompt_ids']) - 1 if name == 'initial' else receipt['cycles'][int(name.removeprefix('commit-'))]['keep'] - 1
            need(int(metadata['vocab']) == VOCAB and int(metadata['sequence_bytes']) == (checkpoint/'sequence.bin').stat().st_size,
                 'checkpoint raw-state metadata differs')
            need(int(metadata['position_min']) == 0 and int(metadata['position_max']) == maximum, 'checkpoint positions differ')
    return len(expected_vectors)


def verify_job(run_root, record, planned, inputs):
    root = Path(run_root)
    job_path = root/safe(record['job_file']); job = read(job_path)
    need(identity(job_path) == record['job_identity'], 'job identity differs')
    need(record['process']['returncode'] == 0 and record['process'].get('child_reaped') is True and not record['process'].get('timed_out'), 'partial/error native process')
    native = root/safe(record['output_dir'])
    for suffix in ('stdout', 'stderr'):
        log = native.parent/('process.'+suffix)
        need(identity(log) == {key:record['process'][suffix][key] for key in ('bytes','sha256')}, 'owned-process log binding differs')
    actual = {str(p.relative_to(native)): identity(p) for p in native.rglob('*') if p.is_file()}
    need(actual == record['native_files'], 'missing, extra, or changed native raw files')
    result = read(native/'result.json')
    need(result['status'] == 'COMPLETE', 'original entry did not complete')
    need(result['vocab'] == VOCAB and result['eog_ids'] == EOG, 'native tokenizer/EOG binding differs')
    names = [f'{case["name"]}-{record["run_id"]}-{planned["name"]}' for case in inputs]
    ready = [line.split() for line in (native.parent/'process.stdout').read_text().splitlines() if line.startswith('PHASE1_RESULT_READY ')]
    need(len(ready) == 2 and all(len(line) == 3 for line in ready) and [line[1] for line in ready] == names, 'partial or cross-run result-ready log')
    need([entry['name'] for entry in job['inputs']] == names, 'cross-run input-name binding differs')
    need(job['experiment_run_id'] == record['run_id'] and job['process_name'] == planned['name'], 'job run/process binding differs')
    need(job['target_sha256'] == TARGET_SHA and job['draft_sha256'] == DRAFT_SHA, 'job real-model binding differs')
    need(result['requests'] == [{'name': name, 'record': name+'/receipt.json'} for name in names], 'native result request set/order differs')
    need(result['total_observed_API_calls']['context_creates'] == 2, 'actual original-entry context creation count differs')
    need(result['total_observed_API_calls']['state_imports'] == 0, 'unexpected state import')
    need(result['trajectories'] == 2, 'native trajectory count differs')
    need(record['loaded_numerical_modules_before'] == record['loaded_numerical_modules_after'], 'actual numerical module identities changed')
    receipts = []; work = Counter(); vectors = 0
    for name, case, submitted in zip(names, inputs, job['inputs']):
        need(submitted['input']['prompt_ids'] == case['prompt_ids'] and submitted['input']['cap'] == CAP, 'native input differs from plan')
        receipt = read(native/name/'receipt.json')
        need(receipt['prompt_ids'] == case['prompt_ids'] and receipt['k'] == K and receipt['capture'] == planned['capture'], 'request identity differs')
        need(receipt['proposal_mode'] == 'live' and receipt['lifecycle'] == 'resident' and receipt['draft_ubatch'] == 4 and receipt['target_output_reserve'] == 8, 'request contract differs')
        need(receipt['draft_tail_policy'] == ('deferred-last-q1' if planned['deferred'] else 'eager-control'), 'wrong macro arm')
        for key in ('request_seconds', 'service_seconds'):
            need(type(receipt[key]) in (int, float) and math.isfinite(receipt[key]) and receipt[key] > 0, 'invalid service clock')
        need(receipt['request_seconds'] <= receipt['service_seconds'], 'service clock excludes request interval')
        observed = receipt['observed_API_calls_within_service']
        need(observed['state_imports'] == 0 and observed['context_creates'] == 0, 'unexpected online API work')
        if not planned['capture']:
            need(observed['state_exports'] == 0 and observed['heavy_captures'] == 0, 'clean interval contained capture work')
            need(not list((native/name).rglob('*.f32')) and not list((native/name).rglob('*.bin')), 'clean binary exported hidden vectors/states')
        else:
            need(observed['state_exports'] == 1 + len(receipt['cycles']) and observed['heavy_captures'] == 2 + 16 * len(receipt['cycles']), 'original heavy observer accounting differs')
            vectors += logical_walk(receipt, native/name, case)
        work.update(actual_work(receipt, case, planned['deferred']))
        receipts.append(receipt)
    need(result['token_rows'] == work['target_rows'] + work['draft_rows'], 'native total token rows differs')
    for key, value in work.items():
        need(value <= planned['work_ceiling'][key], 'native work ceiling exceeded')
    if planned['capture']:
        audit = read(native/'request_audit/AUDIT.json')
        need(audit['status'] == 'OBSERVATIONS_CLOSED_NOT_ENTRY_QUALIFIED' and audit['job_sha256'] == record['job_identity']['sha256'], 'audit footer/job binding differs')
        need(audit['requests_seen'] == 2 and audit['model_loads'] == 2 and audit['contexts'] == [
            {'role': 'target', 'n_ctx': 1024, 'n_ubatch': 32}, {'role': 'draft', 'n_ctx': 1024, 'n_ubatch': 4}], 'observed models/contexts differ')
        expected_events = []
        for index, (name, receipt) in enumerate(zip(names, receipts)):
            expected_events += [(name, 'target', 'reset', {'clear_data': False}, 0), (name, 'draft', 'reset', {'clear_data': False}, 0)]
            for cycle in receipt['cycles']:
                for role, keep in [('draft', cycle['base']), ('target', cycle['keep']), ('draft', cycle['keep'])]:
                    expected_events.append((name, role, 'trim', {'sequence': 0, 'p0': keep, 'p1': -1}, keep))
            for role in ('target', 'draft'):
                boundary = 'before_next_target_clear' if index == 0 else 'before_first_context_free'
                expected_events.append((name, role, 'terminal', {'boundary': boundary}, receipt[role+'_final_kv']['max'] + 1))
        need(len(audit['events']) == len(expected_events), 'missing or extra sidecar state captures')
        journal = [json.loads(line) for line in (native/'request_audit/events.jsonl').read_text().splitlines()]
        need(canonical(journal) == canonical(audit['events']), 'partial or changed sidecar event journal')
        sidecar_bytes = 0
        sidecar_files = set()
        for ordinal, (event, expected) in enumerate(zip(audit['events'], expected_events)):
            need((event['request'], event['role'], event['kind'], event['details'], event['geometry']['used']) == expected, 'ambiguous frontier/event ordering')
            need(event['geometry']['native_head_guard'] and event['geometry']['next'] == event['geometry']['used'], 'native head/extent guard absent')
            need(event['file'] == f'{event["request"]}/{ordinal}-{event["role"]}-{event["kind"]}.bin', 'duplicate or foreign sidecar frontier file')
            path = native/'request_audit'/safe(event['file'])
            need(path.stat().st_size == event['bytes'], 'sidecar state length differs')
            sidecar_files.add(path)
            sidecar_bytes += event['bytes']
        need(set((native/'request_audit').rglob('*.bin')) == sidecar_files, 'extra or missing raw sidecar state')
        need(audit['state_bytes'] == sidecar_bytes, 'sidecar accounting differs')
    else:
        need(not (native/'request_audit').exists(), 'clean entry loaded audit wrapper')
    return {'receipts': receipts, 'work': dict(work), 'vectors': vectors, 'names': names, 'native': native}


def compare_capture(left, right):
    pairs = byte_count = 0
    for left_name, right_name in zip(left['names'], right['names']):
        ldir, rdir = left['native']/left_name, right['native']/right_name
        lfiles = {str(p.relative_to(ldir)) for p in ldir.rglob('*') if p.suffix in {'.f32', '.bin'}}
        rfiles = {str(p.relative_to(rdir)) for p in rdir.rglob('*') if p.suffix in {'.f32', '.bin'}}
        need(lfiles == rfiles, 'capture file sets differ')
        for relative in sorted(lfiles):
            data = (ldir/relative).read_bytes()
            need(data == (rdir/relative).read_bytes(), 'full vector/target sequence bytes differ')
            pairs += 1; byte_count += len(data)
    la = read(left['native']/'request_audit/AUDIT.json')['events']
    ra = read(right['native']/'request_audit/AUDIT.json')['events']
    need(len(la) == len(ra), 'sidecar count differs')
    for l, r in zip(la, ra):
        need({k:v for k,v in l.items() if k not in {'request','file'}} == {k:v for k,v in r.items() if k not in {'request','file'}}, 'sidecar frontier/geometry differs')
        data = (left['native']/'request_audit'/safe(l['file'])).read_bytes()
        need(data == (right['native']/'request_audit'/safe(r['file'])).read_bytes(), 'active target/draft sequence bytes differ')
        pairs += 1; byte_count += len(data)
    return {'status': 'INSTRUMENTED_FULL_CAPTURE_EQUAL', 'raw_pairs': pairs, 'bytes_per_side': byte_count,
            'performance_admitted': False, 'historical_R_bridge': 'OPEN', 'clean_full_vector_state_bridge': 'OPEN'}


def verify_directory(directory):
    directory = Path(directory)
    run, inputs, plan = read(directory/'RUN.json'), read(directory/'INPUTS.json'), read(directory/'PLAN.json')
    need(plan == make_plan(inputs), 'plan was changed or substituted')
    need(run['plan_identity'] == identity(directory/'PLAN.json') and run['inputs_identity'] == identity(directory/'INPUTS.json'), 'run plan/input binding differs')
    required = {'CAPTURE_COMPLETE_PENDING_COMPARISON': 2, 'COMPLETE_PREPARATION_NOT_PERFORMANCE_ADMITTED': 6}.get(run['status'])
    need(required is not None, 'run incomplete or failed')
    need(len(run['completed']) == required and run.get('attempted_processes') == required,
         'status/process count is partial, excessive, or inconsistent')
    checked = []
    for record, job in zip(run['completed'], plan['jobs']):
        need(record['name'] == job['name'] and record['run_id'] == run['run_id'], 'cross-run or skipped job')
        need(record['binary'] == job['binary'] and record['binary_identity'] == run['build']['outputs'][job['binary']], 'binary/macro identity differs')
        need(record['loaded_numerical_modules_before'] == run['build']['numerical_libraries'], 'runtime numerical library binding differs')
        checked.append(verify_job(directory, record, job, validate_inputs(inputs)))
    qualification = compare_capture(checked[0], checked[1])
    fields = ['ids','eog','length','terminal_id','stop_reason','cycles','target_final_kv','draft_final_kv','phase_executions']
    for index, job in enumerate(checked[2:], start=2):
        baseline = checked[plan['jobs'][index]['deferred']]
        for observed, expected in zip(job['receipts'], baseline['receipts']):
            need(canonical({key:observed[key] for key in fields}) == canonical({key:expected[key] for key in fields}), 'clean logical endpoint differs from capture')
    return {'schema': 'heterospec.production-preparation-replay.v1', 'status': 'PREPARATION_EVIDENCE_CHECKED',
            'checked_processes': len(checked), 'checked_requests': 2 * len(checked),
            'capture_qualification': qualification,
            'work': [job['work'] for job in checked],
            'clean_service_seconds': [[r['service_seconds'] for r in job['receipts']] for job in checked[2:]],
            'performance_admitted': False, 'historical_R_bridge': 'OPEN', 'clean_full_vector_state_bridge': 'OPEN'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    write_new(args.out, verify_directory(args.directory))
