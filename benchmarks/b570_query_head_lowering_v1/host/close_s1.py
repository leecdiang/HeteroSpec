"""Read-only S1 raw reconstruction and immutable archive; launches no worker."""
import collections
import datetime
import hashlib
import json
import pathlib
import struct
import sys
import zipfile

from common import ROOT, load, modules, save, sha

sys.path.insert(0, str(ROOT))
import core

F0_SHA = '8935c7cb5369ec052d074f060d9519ac51311620830819b74be5e3c49d3a0fb7'


def events(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]


def main():
    before = modules()
    root = ROOT / 'host_outputs/S1_RUN'
    f0 = load(ROOT / 'host/S1_F0.json')
    assert sha(ROOT / 'host/S1_F0.json') == F0_SHA
    for name, digest in f0['sources'].items():
        assert sha(ROOT / name) == digest, name
    for item in [f0['executable']] + f0['dependencies'] + f0['driver_files']:
        assert sha(item['path']) == item['sha256'], item['path']
    assert sha(ROOT / 'host/S1_PLAN.json') == f0['plan_sha256']
    assert sha(ROOT / 'host/S1_INPUTS.json') == f0['input_manifest_sha256']
    inputs = load(ROOT / 'host/S1_INPUTS.json')
    for item in inputs:
        assert sha(item['path']) == item['sha256']
    planned = load(ROOT / 'host/S1_PLAN.json')['slots']
    close = load(root / 'CLOSEOUT.json')
    ledger = events(root / 'LEDGER.jsonl')
    attempts = [x for x in ledger if x['event'] == 'PROCESS_ATTEMPT']
    complete = [x for x in ledger if x['event'] == 'PROCESS_COMPLETE']
    assert len(planned) == 161
    assert len(attempts) == close['attempts'] == 2
    assert len(complete) == len(close['completed']) == 1
    assert [a['slot'] for a in attempts] == [s['id'] for s in planned[:2]]
    assert close['failed'] == [planned[1]['id']]
    assert close['unstarted'] == [s['id'] for s in planned[2:]]
    assert not close['skipped_unsupported']
    assert len({a['slot'] for a in attempts}) == 2
    assert not any(x['event'] == 'FULL_VECTOR_COMPARISON' for x in ledger)
    choice_index = next(i for i, x in enumerate(ledger) if x['event'] == 'CHOICE_FROZEN_BEFORE_OUTPUTS')
    graph_index = next(i for i, x in enumerate(ledger) if x['event'] == 'PROCESS_ATTEMPT' and x['request']['kind'] == 'graph')
    assert choice_index < graph_index
    processes = []
    raw_by_kind = {}
    for attempt in attempts:
        folder = root / attempt['slot']
        request = load(folder / 'REQUEST.wire')
        lifecycle = load(folder / 'LIFECYCLE.json')
        raw = events(folder / 'raw.jsonl')
        assert request == attempt['request']
        assert request['F0_sha256'] == F0_SHA
        assert lifecycle['request_sha256'] == sha(folder / 'REQUEST.wire')
        assert lifecycle['raw_sha256'] == sha(folder / 'raw.jsonl')
        assert raw[0]['event'] == 'HOST_START'
        assert raw[0]['pid'] == lifecycle['pid']
        assert raw[0]['request'] == request
        device = next(x for x in raw if x['event'] == 'DEVICE')
        assert 'B570' in device['description'] and device['backend_name'] == 'Vulkan0'
        gates = [x for x in raw if x['event'] == 'AWAIT_RUNTIME_GATE']
        assert len(gates) == 1
        dependencies = {pathlib.Path(x['path']).name.lower(): x['sha256'] for x in f0['dependencies']}
        numerical = {pathlib.Path(x['path']).name.lower(): x['sha256'] for x in lifecycle['actual_runtime_modules']
                     if pathlib.Path(x['path']).name.lower().startswith(('ggml', 'llama'))}
        assert numerical == dependencies
        for item in lifecycle['actual_runtime_modules']:
            assert sha(item['path']) == item['sha256']
        assert len(gates[0]['modules']) == len(lifecycle['actual_runtime_modules'])
        assert {p.lower() for p in gates[0]['modules']} == {
            x['path'].lower() for x in lifecycle['actual_runtime_modules']}
        samples = lifecycle['watchdog_samples']
        assert samples and lifecycle['stop'] is None
        checkpoints = [x for x in raw if x['event'] == 'MEMORY_CHECKPOINT']
        assert all(x['backend_reported_free_bytes'] >= 512 * 1024**2 for x in checkpoints)
        assert all(x['continuous_residency'] is False for x in checkpoints)
        counts = collections.Counter(x['event'] for x in raw)
        assert counts['GRAPH_START'] == lifecycle['graph_start_events']
        assert counts['GRAPH_RETURN'] == lifecycle['graph_return_events']
        processes.append(dict(slot=attempt['slot'], kind=request['kind'], pid=lifecycle['pid'],
            returncode=lifecycle['returncode'], returncode_hex=hex(lifecycle['returncode']),
            owned_wall_s=lifecycle['owned_wall_s'], event_counts=dict(counts),
            last_event=raw[-1]['event'], numerical_modules=numerical,
            sample_count=len(samples), peak_sampled_RSS=max(x['RSS'] or 0 for x in samples),
            max_actual_gap_ms=max(x['gap_ms'] for x in samples),
            min_host_available_bytes=min(x['host_available'] for x in samples),
            min_disk_free_bytes=min(x['disk_free'] for x in samples), memory_checkpoints=checkpoints))
        raw_by_kind[request['kind']] = raw
    census_raw = raw_by_kind['capability_only']
    assert processes[0]['returncode'] == 0 and census_raw[-1]['event'] == 'CLOSE'
    assert not any(x['event'].startswith('GRAPH_') for x in census_raw)
    census = [x for x in census_raw if x['event'] == 'CAPABILITY']
    expected = {(core.sha(s['cell']), s['mode']) for s in planned[1:]}
    actual = {}
    matrix = []
    per_mode = collections.defaultdict(lambda: dict(cells=0, supported_cells=0, executable_nodes=0, unsupported_nodes=0))
    metadata_ops = {'NONE', 'VIEW', 'RESHAPE', 'PERMUTE', 'TRANSPOSE'}
    reconstructed = []
    census_hash = sha(root / planned[0]['id'] / 'raw.jsonl')
    for row in census:
        key = core.sha(row['cell']), row['mode']
        assert key in expected and key not in actual and row['graph_compute'] is False
        nodes = row['nodes']
        assert nodes and len({n['id'] for n in nodes}) == len(nodes)
        for node in nodes:
            assert type(node['supports_op']) is bool
            assert node['executable'] == (node['op'] not in metadata_ops)
        compute = [n for n in nodes if n['executable']]
        assert compute
        ok = all(n['supports_op'] for n in compute)
        actual[key] = ok
        p = per_mode[row['mode']]
        p['cells'] += 1
        p['supported_cells'] += ok
        p['executable_nodes'] += len(compute)
        p['unsupported_nodes'] += sum(not n['supports_op'] for n in compute)
        matrix.append(dict(cell=row['cell'], cell_sha256=key[0], mode=row['mode'],
                           full_supports_op=ok, executable_nodes=len(compute), graph_compute=False))
        reconstructed.append(dict(cell_sha256=key[0], mode=row['mode'],
            compute_nodes=[dict(id=str(n['id']), op=n['op'], supports_op=n['supports_op']) for n in compute],
            raw_sha256=census_hash))
    assert set(actual) == expected and len(census) == 80
    stored_census = load(root / 'CAPABILITY_CENSUS.json')
    assert stored_census == dict(binding_sha256=F0_SHA, observations=reconstructed)
    reference_ok = all(ok for (c, m), ok in actual.items() if m in ('MQ', 'PQ'))
    selected = 'STOP_REFERENCE_BACKEND_NOT_ADMITTED'
    if reference_ok:
        selected = next((m for m in ('QH_C', 'QH_D') if all(ok for (c, mode), ok in actual.items() if mode == m)),
                        'STOP_NO_SUPPORTED_CANDIDATE')
    selection = load(root / 'CANDIDATE_SELECTION.json')
    assert selection == dict(choice=selected, census_sha256=sha(root / 'CAPABILITY_CENSUS.json'), before_numerical_graph=True)
    assert selected == close['selected_candidate'] == 'QH_C'
    graph_raw = raw_by_kind['graph']
    assert processes[1]['returncode'] == 3221226505
    assert processes[1]['event_counts']['GRAPH_START'] == 1
    assert not any(x['event'] in ('GRAPH_RETURN', 'GRAPH_OUTPUT', 'CLOSE') for x in graph_raw)
    assert graph_raw[-1]['event'] == 'GRAPH_START'
    graph_request = attempts[1]['request']
    assert graph_request['mode'] == 'MQ' and graph_request['cell']['geometry']['q'] == 1
    before_caps = next(x for x in graph_raw if x['event'] == 'PRECOMPUTE_CAPABILITY')['nodes']
    assignments = next(x for x in graph_raw if x['event'] == 'ASSIGNMENT_BEFORE_COMPUTE')['nodes']
    assert {x['id'] for x in assignments} == {x['id'] for x in before_caps if x['executable']}
    assert all(x['device_matches'] and x['direct_execution_backend'] == 'Vulkan0' and x['buffer_name'] == 'Vulkan0' for x in assignments)
    assert all(x['supports_op'] for x in before_caps if x['executable'])
    folder = root / planned[1]['id']
    stderr = (folder / 'stderr.log').read_text(encoding='utf-8')
    assertion = 'GGML_ASSERT(allow_misalign || misalign_bytes == 0) failed'
    assert assertion in stderr
    assert not list(root.rglob('*.f32'))
    source = pathlib.Path(graph_request['input']).read_bytes()
    q, n, h, hk, storage, mask, pattern = struct.unpack('<7i', source[:28])
    assert (q, n, h, hk, storage, mask, pattern) == (1, 63, 8, 8, 1, 0, 0)
    cursor = 28
    identities = []
    for i, size in enumerate((128*q*h*4, 128*n*hk*2, 128*n*hk*2, 32*n*4)):
        expected_bytes = source[cursor:cursor+size]
        cursor += size
        if i == 0:
            expected_bytes = bytes(32) + expected_bytes
        stored = folder / f'vectors/input-{i}.before.bin'
        assert stored.read_bytes() == expected_bytes
        assert not (folder / f'vectors/input-{i}.after.bin').exists()
        identities.append(dict(input=i, before_sha256=sha(stored), matches_frozen_source=True,
                               after_sha256=None, after_reason='graph did not return'))
    assert cursor == len(source)
    owned = sum(p['owned_wall_s'] for p in processes)
    assert owned == close['owned_wall_s'] and owned < 3600
    states = []
    for i, slot in enumerate(planned):
        states.append(dict(slot=slot, state='COMPLETED_CAPABILITY_ONLY' if i == 0 else
                           'FAILED_RUNTIME_ASSERTION' if i == 1 else 'UNSTARTED_AFTER_STOP'))
    files = []
    for file in sorted(root.rglob('*')):
        if file.is_file():
            files.append(dict(path=file.relative_to(root).as_posix(), bytes=file.stat().st_size, sha256=sha(file)))
    archive = ROOT / 'host/S1_RAW.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for item in files:
            z.write(root / item['path'], item['path'])
    with zipfile.ZipFile(archive) as z:
        assert set(z.namelist()) == {f['path'] for f in files}
        for item in files:
            digest = hashlib.sha256()
            size = 0
            with z.open(item['path']) as f:
                while chunk := f.read(1024 * 1024):
                    digest.update(chunk)
                    size += len(chunk)
            assert digest.hexdigest() == item['sha256'] and size == item['bytes']
    save(ROOT / 'host/S1_RAW_MANIFEST.json', dict(archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
         raw_root=str(root), files=files))
    save(ROOT / 'host/S1_RESTORE_RECEIPT.json', dict(all_archived_bytes_independently_streamed_and_rehashed=True,
         files=len(files), bytes=sum(x['bytes'] for x in files), archive_sha256=sha(archive), GPU_launches=0))
    save(ROOT / 'host/S1_SUPPORT_MATRIX.json', dict(F0_sha256=F0_SHA, raw_sha256=census_hash,
         per_mode=dict(per_mode), cells=matrix, support_only_selected=selected,
         meaning='Actual complete per-executable-node supports_op, not successful execution or numerical qualification'))
    save(ROOT / 'host/S1_SLOT_ACCOUNTING.json', dict(F0_sha256=F0_SHA, slots=states))
    save(ROOT / 'host/S1_RESULT.json', dict(status='STOP_S1_REFERENCE_RUNTIME_ASSERTION', F0_sha256=F0_SHA,
         audit_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), attempts=2,
         completed_capability_hosts=1, failed_graph_hosts=1, completed_graph_hosts=0, unstarted_slots=159,
         skipped_unsupported=0, selected_candidate=selected, owned_wall_s=owned,
         max_actual_gap_ms=max(p['max_actual_gap_ms'] for p in processes),
         peak_sampled_RSS=max(p['peak_sampled_RSS'] for p in processes),
         raw_bytes=sum(f['bytes'] for f in files), processes=processes,
         failed_cell=graph_request['cell'], failed_mode='MQ', assertion=assertion,
         source_assertion_location='ggml/src/ggml-vulkan/ggml-vulkan.cpp:8301',
         placement_scope='Precompute actual Vulkan buffer/device ownership only; graph did not return',
         input_before_identity=identities, numerical_outputs_available=False,
         candidate_graphs_executed=0, candidate_numerical_qualification=None,
         exact_faulting_tensor=None, minStorageBufferOffsetAlignment=None,
         model_requests=0, warmups=0, retries=0, extra_probes=0,
         S2='NOT_ADMITTED_UNSTARTED', S3='NOT_ADMITTED_UNSTARTED',
         source_runtime_input_hashes_still_match_F0=True, modules_before=before, modules_after=modules(),
         DRAM=None, cache=None, XMX=None, shader_timestamps=None, arithmetic_DAG=None,
         continuous_residency=None, PPA=None, end_to_end_speedup=None))
    print(json.dumps(dict(status='STOP_S1_REFERENCE_RUNTIME_ASSERTION', attempts=2,
        unstarted=159, owned_wall_s=owned, per_mode=dict(per_mode), archive_bytes=archive.stat().st_size)))


if __name__ == '__main__':
    main()
