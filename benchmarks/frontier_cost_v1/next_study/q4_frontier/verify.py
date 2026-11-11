"""Offline verification of exact diagnostic blobs and fail-stop receipts; no model calls."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import struct
from protocol import (ARMS, BUDGET, LIBRARIES, MODEL_BYTES, MODEL_SHA, RAW_BYTE_LIMIT,
                      atomic_json, cases, digest, identity)

CHECKS = ['initial_state', 'initial_geometry', 'shared_operation_vectors', 'final_state',
          'final_geometry', 'continuation_vector', 'continuation_state', 'continuation_geometry']
GEOMETRIES = ['initial_geometry', 'untrimmed_geometry', 'final_geometry', 'continuation_geometry']


def require(condition, message):
    if not condition:
        raise ValueError(message)


def blob(native, descriptor):
    sha = descriptor['sha256']
    require(len(sha) == 64 and all(c in '0123456789abcdef' for c in sha), 'Invalid blob hash')
    require(descriptor['path'] == 'blobs/'+sha+'.bin', 'Noncanonical blob path')
    path = native/descriptor['path']
    require(not path.is_symlink() and identity(path) == {'bytes': descriptor['bytes'], 'sha256': sha}, 'Blob identity differs')
    return path.read_bytes()


def vector(data, rows):
    require(len(data) == rows*128*4, 'Full vocabulary vector byte count differs')
    require(all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', data)), 'Nonfinite primary vector')


def validate_work(records, panel, work):
    """Require every completed stage in both views; allow one interrupted final stage."""
    order = ['prefill', 'operation', 'continuation']
    expected_stages = {};required_stages = set();possible_incomplete = set()
    for index, record in enumerate(records):
        case, arm = panel[index];prefix = case['name']+'/'+arm['name']+'/'
        shape = {'prefill': ((len(case['history'])+31)//32, len(case['history'])),
                 'operation': (len(arm['schedule']), sum(arm['schedule'])), 'continuation': (1, 1)}
        counts = record['counts'];present = [name for name in order if name in counts]
        require(set(counts) == set(present) and present == order[:len(present)], 'Completed stages are not an ordered prefix')
        complete = record['status'] in ('PASS', 'REFERENCE_CAPTURED')
        if complete:
            require(present == order, 'Completed path lacks all three work stages')
        elif len(present) < len(order):
            require(index == len(records)-1, 'Earlier path is incomplete')
            possible_incomplete.add(prefix+order[len(present)])
        for stage, (calls, rows) in shape.items():
            expected_stages[prefix+stage] = (record, stage, calls, rows)
        for stage in present:
            required_stages.add(prefix+stage)
    actual = set(work['by_stage'])
    require(required_stages <= actual <= required_stages | possible_incomplete, 'Missing completed stage or unplanned extra native work')
    totals = {'reserved_calls': 0, 'reserved_rows': 0, 'attempted_calls': 0, 'attempted_rows': 0}
    for name, value in work['by_stage'].items():
        record, stage, calls, rows = expected_stages[name]
        require(value['reserved_calls'] == calls and value['reserved_rows'] == rows, 'Stage reservation differs')
        require(0 <= value['attempted_calls'] <= calls and 0 <= value['attempted_rows'] <= rows, 'Attempted native work exceeds reservation')
        if stage in record['counts']:
            count = record['counts'][stage]
            require(count['total_native_calls'] == value['attempted_calls'] == calls and count['total_target_rows'] == value['attempted_rows'] == rows, 'Completed counter receipt differs')
            require(count['outer_calls'] + count['prefill_calls'] == calls and count['target_rows'] + count['prefill_rows'] == rows, 'Prefill/nonprefill accounting differs')
            require((count['prefill_calls'], count['prefill_rows']) == ((calls, rows) if stage == 'prefill' else (0, 0)), 'Native stage role differs')
            histogram = count['physical_widths']
            require(all(str(int(k)) == k and 1 <= int(k) <= 32 and type(v) is int and v > 0 for k, v in histogram.items()), 'Physical width histogram malformed')
            require(sum(histogram.values()) == count['physical_calls'] == calls, 'Physical call count differs')
            require(sum(int(width)*number for width, number in histogram.items()) == rows, 'Physical row count differs')
        for field in totals:
            totals[field] += value[field]
    for field, key in [('reserved_calls', 'reserved_native_calls'), ('reserved_rows', 'reserved_target_rows'),
                       ('attempted_calls', 'attempted_native_calls'), ('attempted_rows', 'attempted_target_rows')]:
        require(work[key] == totals[field], 'Global/stage accounting differs')


def validate_trim(record, arm):
    trims = record['trim_calls'];require(type(trims) is int and trims in (0, 1), 'Invalid trim count')
    needed = int(sum(arm['schedule']) > arm['frontier'])
    if not needed:
        require(trims == 0, 'Reference or full macro unexpectedly trimmed')
    if trims:
        require(record['checks'].get('shared_operation_vectors') is True, 'Trim happened before shared-vector qualification')
    if record['status'] in ('PASS', 'REFERENCE_CAPTURED') or 'final_geometry' in record:
        require(trims == needed, 'Completed frontier trim count differs')
    if needed and record['checks'].get('shared_operation_vectors') is False:
        require(trims == 0, 'Trim followed a failed shared-vector check')


def verify(directory):
    directory = Path(directory)
    run = json.loads((directory/'RUN.json').read_text())
    job_path = directory/'JOB.json';job = json.loads(job_path.read_text())
    native = directory/'native';result_path = native/'RESULT.json';result = json.loads(result_path.read_text())
    require(run['status'] == 'COMPLETE_PENDING_INDEPENDENT_VERIFICATION', 'Runner incomplete or failed; partial evidence only')
    require(run['native_child_launches'] == 1 and run['child_reaped'] is True and run['timed_out'] is False, 'Owned child receipt differs')
    require(run['performance_admitted'] is False and run['automatic_retry'] is False, 'Performance or retry forbidden')
    require(run['job'] == identity(job_path) and run['native_result'] == identity(result_path), 'Job/result binding differs')
    require(run['model'] == {'bytes': MODEL_BYTES, 'sha256': MODEL_SHA}, 'Runner model differs')
    require(run['publication']['remote_source_verified'] is True, 'Remote publication missing')
    require(job['source_binding'] == run['publication']['sources'] == result['source_binding'], 'Source binding differs')
    require(job['published_source_commit'] == run['publication']['commit'] == result['published_source_commit'], 'Source commit differs')
    require(result['job_sha256'] == digest(job_path), 'Native job hash differs')
    require(job['cases'] == cases() and job['budget'] == BUDGET and job['raw_byte_limit'] == RAW_BYTE_LIMIT, 'Input panel differs')
    require(job['expected_native_libraries'] == LIBRARIES, 'Library profile differs')
    for name, desc in run['logs'].items():
        require(name in ('stdout.log', 'stderr.log') and identity(directory/name) == desc, 'Log binding differs')
    for key in ('dependencies_unchanged', 'sources_unchanged', 'model_unchanged'):
        require(run[key] is True, 'Post-run binding changed')
    for key in ('performance_admitted', 'timing_phase', 'natural_acceptance_tested', 'production_q8_full_mask_qualified'):
        require(result[key] is False, 'Unadmitted claim in native receipt')
    require(result['historical_R_qualification'] == 'NOT_ESTABLISHED', 'Historical R claim forbidden')
    require(result['model'] == {'bytes': MODEL_BYTES, 'sha256': MODEL_SHA, 'trained': False}, 'Native model differs')
    require(result['model_loads'] == 1 and result['backend'] == 'cpu' and result['threads'] == 1, 'Native profile differs')
    require({name: item['sha256'] for name, item in result['native_modules_before'].items()} == LIBRARIES, 'Loaded module profile differs')
    status = result['status']
    require(status in ('DIAGNOSTIC_PASS', 'QUALIFICATION_FAILED', 'GUARD_OR_RUNTIME_FAILED'), 'Unexpected native status')
    require(run['returncode'] == {'DIAGNOSTIC_PASS': 0, 'QUALIFICATION_FAILED': 3, 'GUARD_OR_RUNTIME_FAILED': 2}[status], 'Exit status differs')
    panel = [(case, arm) for case in cases() for arm in ARMS]
    records = result['runs'];require(len(records) <= 14, 'Context panel expanded')
    loaded = {};seen_blobs = {};observed = [];first_failure = None
    for index, record in enumerate(records):
        case, arm = panel[index];key = (case['name'], arm['name'])
        require(record['case'] == key[0] and record['arm'] == key[1], 'Out-of-order or repeated context')
        for field in ('schedule', 'shared_rows', 'frontier'):
            require(record[field] == arm[field], 'Arm changed: '+field)
        require(record['base'] == len(case['history']) and record['reference'] == (arm['reference'] or ''), 'Context geometry/reference differs')
        data = {name: blob(native, desc) for name, desc in record['captures'].items()}
        loaded[key] = data
        for desc in record['captures'].values():
            seen_blobs[desc['sha256']] = desc['bytes']
        if 'all_operation_vectors' in data:
            require(len(data['all_operation_vectors']) == sum(arm['schedule'])*128*4, 'All requested vector count differs')
            require(data['shared_operation_vectors'] == data['all_operation_vectors'][:arm['shared_rows']*128*4], 'Shared row projection differs')
            vector(data['shared_operation_vectors'], arm['shared_rows'])
            all_finite = all(math.isfinite(x[0]) for x in struct.iter_unpack('<f', data['all_operation_vectors']))
            require(record['all_operation_vectors_finite_diagnostic'] is all_finite, 'Extra-vector finite diagnostic differs')
        if 'continuation_vector' in data:
            vector(data['continuation_vector'], 1)
        for field in GEOMETRIES:
            if field not in record:
                continue
            delta = {'initial_geometry': 0, 'untrimmed_geometry': sum(arm['schedule']),
                     'final_geometry': arm['frontier'], 'continuation_geometry': arm['frontier']+1}[field]
            end = len(case['history'])+delta;geometry = record[field]
            require(geometry['used'] == end and geometry['occupied_end'] == end, 'Active state frontier differs')
            require(geometry['dense_seq0'] is True and geometry['head_equals_next_by_native_guard'] is True, 'Native append geometry rejected')
            require(geometry['n_ubatch'] == 32 and geometry['n_ctx'] == 1024, 'Context dimensions changed')
            require(geometry['extent'] == ((end+255)//256)*256 and geometry['next_q1_extents'] == [((end+1+255)//256)*256], 'Native attention extent differs')
        if arm['frontier'] == 5 and 'all_operation_vectors' in data:
            require(record['fifth_vector_is_primary_contract'] is False, 'Fifth vector incorrectly gates contract')
            require(data['fifth_vector_diagnostic'] == data['all_operation_vectors'][4*128*4:5*128*4], 'Fifth diagnostic projection differs')
        if arm['reference']:
            reference_key = (case['name'], arm['reference'])
            ref_data = loaded[reference_key]
            ref_record = records[next(i for i, pair in enumerate(panel[:index]) if (pair[0]['name'], pair[1]['name']) == reference_key)]
            checks = record['checks'];present = [name for name in CHECKS if name in checks]
            available = {name: (record[name] == ref_record[name] if name in GEOMETRIES else data[name] == ref_data[name])
                         for name in CHECKS if (name in record and name in ref_record) or (name in data and name in ref_data)}
            require(set(checks) == set(present) and present == CHECKS[:len(present)], 'Required comparison sequence differs')
            for name in present:
                computed = record[name] == ref_record[name] if name in GEOMETRIES else data[name] == ref_data[name]
                require(checks[name] is computed, 'Recorded comparison disagrees with raw bytes: '+name)
                if not computed:
                    require(first_failure is None and name == present[-1] and index == len(records)-1, 'Work continued after mismatch')
                    first_failure = {'case': key[0], 'arm': key[1], 'check': name}
            if 'fifth_vector_diagnostic_equal' in record:
                require(record['fifth_vector_diagnostic_equal'] is (data['fifth_vector_diagnostic'] == ref_data['fifth_vector_diagnostic']), 'Extra diagnostic equality differs')
            if record['status'] == 'PASS':
                require(present == CHECKS and all(checks.values()), 'Candidate PASS lacks full comparison')
        else:
            require(record['checks'] == {}, 'Reference must not self-qualify')
            available = {}
        if index < len(records)-1 or status == 'DIAGNOSTIC_PASS':
            require(record['status'] == ('PASS' if arm['reference'] else 'REFERENCE_CAPTURED'), 'Incomplete earlier path')
            require(record['checkpoint'] == 'CONTINUATION_CAPTURED', 'Earlier path lacks continuation')
        validate_trim(record, arm)
        observed.append({'case': key[0], 'arm': key[1], 'status': record['status'], 'checkpoint': record.get('checkpoint'),
                         'available_comparisons_recomputed': available})
    work = result['work'];require(work['contexts'] == len(records), 'Context count differs from started records')
    validate_work(records, panel, work)
    require(work['reserved_native_calls'] <= BUDGET['native_calls'] and work['reserved_target_rows'] <= BUDGET['target_rows'], 'Native budget exceeded')
    require(result['trim_calls'] == sum(r['trim_calls'] for r in records) <= 4, 'Trim accounting differs')
    require(result['raw_bytes'] == sum(seen_blobs.values()) <= RAW_BYTE_LIMIT, 'Raw byte accounting differs')
    require({p.name for p in (native/'blobs').iterdir()} == {sha+'.bin' for sha in seen_blobs}, 'Unreported raw blob')
    if status == 'DIAGNOSTIC_PASS':
        require(len(records) == 14 and work['attempted_native_calls'] == 146 and work['attempted_target_rows'] == 3612 and result['trim_calls'] == 4, 'Incomplete successful panel')
        require({name: item['sha256'] for name, item in result['native_modules_after'].items()} == LIBRARIES, 'Final modules differ')
    elif status == 'QUALIFICATION_FAILED':
        require(first_failure is not None and records[-1]['status'] == 'FAIL', 'Missing preserved mismatch')
    for case, arm in panel[len(records):]:
        observed.append({'case': case['name'], 'arm': arm['name'], 'status': 'NOT_RUN'})
    failure_detail = None
    if status == 'GUARD_OR_RUNTIME_FAILED':
        failure_detail = {'kind': 'native_geometry_guard' if records and 'rejected_native_geometry' in records[-1] else 'guard_or_runtime',
                          'message': result.get('error'), 'geometry_observation': records[-1].get('rejected_native_geometry') if records else None,
                          'does_not_establish_numerical_mismatch': True}
    elif first_failure:
        field = first_failure['check']
        failure_detail = {'kind': 'geometry_equality' if 'geometry' in field else ('active_state_bytes' if 'state' in field else 'full_vector_bytes'),
                          'message': result.get('error')}
    return {'schema': 'heterospec.q4-frontier-verification.v1', 'verified': True, 'native_status': status,
            'failure_detail': failure_detail,
            'first_failure': first_failure, 'contracts': observed, 'work': work, 'trim_calls': result['trim_calls'],
            'raw_bytes': result['raw_bytes'], 'performance_admitted': False,
            'scope': 'Fixed synthetic CPU forced-history diagnostic; absent branches are NOT_RUN and inherit no failure or pass.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    require(not args.out.exists(), 'Fresh verification output required')
    try:
        result = verify(args.run_directory)
    except Exception as error:
        atomic_json(args.out, {'verified': False, 'error': str(error), 'performance_admitted': False});raise
    atomic_json(args.out, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
