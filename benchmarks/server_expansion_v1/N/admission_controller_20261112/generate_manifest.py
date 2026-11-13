"""Expand frozen CPU plan only; no model/tokenizer/backend/device imports."""
import hashlib
import json
from pathlib import Path
from resource_limits import (GiB, MiB, KV_BYTES, VECTOR_BYTES, RAW_PER_REQUEST,
                             STATE_METADATA, OWNED_METADATA, RECORD_METADATA,
                             REQUEST_METADATA, resource_budget)

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / 'native_chain_successor_20261112'
PROPOSAL = ROOT.parent / 'n1a_lifecycle_20261112/N1A_PROPOSAL_NOT_ADMITTED.json'
ORDER = ['RESIDENT_R', 'REPEAT_RESIDENT_R', 'COLD_CANONICAL_ORACLE', 'STRONG_WHOLE_RECHUNK_LOOP4']
PINNED_INPUTS = {
    'native_chain_successor_20261112/NATIVE_JOB_TEMPLATE.json': '4287bde0bfb1b34b35fbd2a4b0d9ef39106e1fefa864eea760196ecbc3c063ac',
    'n1a_lifecycle_20261112/N1A_PROPOSAL_NOT_ADMITTED.json': 'bf00a976a5f5385bd818bd58bdfcaa575e49f9548fee615320ed9b1d86194892',
    'native_chain_successor_20261112/review/RESOURCE_PROPOSAL_REVIEW.json': 'c82a19394b39be188a90dfa5a7504c566d15bcca04352d01424bc74d97ee1cf4',
    'n1a_lifecycle_20261112/REQUIRED_COVERAGE.json': 'b28a8ba5337707a4e11f7a920ea665e6f4030a4028395158b9857101e201f8b2',
}


def sha(path):
    b = path.read_bytes()
    return dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def static_rpc_bound(template):
    """Source-call upper bound, no measurement or model execution.

    The covariance between first-turn prompt/cap and the next retained head is
    retained. Replacing all252 states by4096 is unnecessarily pessimistic.
    """
    totals = dict(state_phases=0, nonempty_states=0, KV_chunks=0,
                  state_vector_rows=0, state_RPC=0)

    def add(head, rows):
        chunks = 72 * ((head + 511) // 512)
        totals['state_phases'] += 1
        totals['nonempty_states'] += int(head > 0)
        totals['KV_chunks'] += chunks
        totals['state_vector_rows'] += rows
        totals['state_RPC'] += 18 + (72 if head else 0) + 2 * (chunks + rows)

    per_worker = {}
    for job in template['jobs']:
        before = totals['state_RPC']
        for episode in job['episodes']:
            prior = 0
            for turn, op in enumerate(episode['operations']):
                if isinstance(op.get('canonical_ids'), list):
                    q = len(op['canonical_ids'])
                elif turn:
                    # Unresolved real R-produced cold/free continuation IDs
                    # stay unresolved; only the unchanged capacity/cap bounds
                    # constrain this static resource calculation.
                    q = 4096 - (op['cap'] - 1)
                else:
                    q = len(op['expected_canonical_ids'])
                retained = min(prior, q - 1) if turn else 0
                terminal = q + op['cap'] - 1
                add(retained, int(job['role'] == 'COLD_CANONICAL_ORACLE' and retained > 0))
                add(q, 1)
                add(terminal, op['cap'])
                prior = terminal
            add(0, 0)
        per_worker[job['worker_id']] = totals['state_RPC'] - before
    planned = dict(totals)
    for _ in range(4):
        add(4096, 1)
        add(4096, 1)
        add(4096, 128)
        add(0, 0)
    commands = dict(state_RPC=totals['state_RPC'], owned_RPC=80 * 16,
                    records_RPC=(99 + 32 + 4 * 4) * 4,
                    decode_RPC=85738, append_begin_RPC=76 * 130,
                    request_trace_finish_RPC=76 * 3, trim_clear_RPC=76 * 4,
                    producer_RPC=32, startup_frames_and_probe_allowance=1024)
    upper = sum(commands.values())
    if upper != 199196 or upper >= 250000:
        raise ValueError('Source-level native RPC envelope changed')
    return dict(status='STATIC_SOURCE_UPPER_BOUND_NOT_OBSERVED', planned_states=planned,
                including_failure_states=totals, per_worker_state_RPC=per_worker,
                command_components=commands, native_RPC_upper_bound=upper,
                aggregate_command_ceiling=250000, remaining_command_headroom=250000-upper,
                journal_record_bytes_max=2048, journal_records_max=250100,
                journal_bytes_product=250100 * 2048,
                log_requirement='Pre-reserve each bounded log stream once or buffer fixed64KiB; unbounded one-byte-per-read journaling is not covered',
                source_rule='State constant18+72(nonempty)+2*(72ceil(head/512)+vectorrows); owned16; record4. Decode count<=charged rows. No comparison/read/finite check is removed.')


def load_manifest():
    for relative, expected in PINNED_INPUTS.items():
        if sha(ROOT.parent / relative)['sha256'] != expected:
            raise ValueError('Frozen input identity conflict: ' + relative)
    template_path = OLD / 'NATIVE_JOB_TEMPLATE.json'
    template = json.loads(template_path.read_text())
    proposal = json.loads(PROPOSAL.read_text())
    resources = resource_budget()
    requests, workers, deployments = {}, [], []
    for probe in template['preflight_templates']:
        deployments.append(dict(id=probe['id'], worker=None, stage='PREFLIGHT', kind='PREFLIGHT',
                                source_binary=probe['source_binary'],
                                backend_inits=1, models=1, contexts=1, placements=1,
                                requests=0, rows=0, timeout_seconds=120))
    for job in template['jobs']:
        worker, stage = job['worker_id'], job['role']
        ids = []
        for episode in job['episodes']:
            for op in episode['operations']:
                ident = op['id']
                if ident in requests or op['reserved_rows'] != template['request_rows'][ident]:
                    raise ValueError('Duplicate or changed frozen operation')
                ids.append(ident)
                turn = int(ident.rsplit('/', 1)[1])
                cold = stage == 'COLD_CANONICAL_ORACLE'
                natural = not ident.startswith('control/')
                # BEFORE_NEXT_MUTATION is charged to the still-active setup;
                # AFTER_NEXT_MUTATION is charged to the continuation.
                counts = dict(state_snapshots=3 + turn, owned_events=1,
                              reconcile_receipts=turn if not cold else 0,
                              mutation_receipts=turn, binding_receipts=turn,
                              producer_receipts=1 if natural and not cold else 0)
                directories = counts['state_snapshots'] + counts['owned_events']
                meta = (counts['state_snapshots'] * STATE_METADATA + counts['owned_events'] * OWNED_METADATA
                        + (counts['reconcile_receipts'] + counts['mutation_receipts'] + counts['binding_receipts']) * RECORD_METADATA
                        + counts['producer_receipts'] * MiB + directories * 1024)
                requests[ident] = dict(worker=worker, stage=stage, row_limit=op['reserved_rows'],
                                      raw_byte_limit=RAW_PER_REQUEST, metadata_byte_limit=meta,
                                      byte_limit=RAW_PER_REQUEST + meta, capture_counts=counts,
                                      prepaid_marker_bytes=directories * 1024,
                                      cap=op['cap'], episode=episode['episode_id'],
                                      cohort='CONTROL' if ident.startswith('control/') else 'NATURAL',
                                      runnable=True, retry=False,
                                      capture_phase_limits={
                                          'POST_RECONCILE': dict(raw_bytes=KV_BYTES + VECTOR_BYTES, metadata_bytes=STATE_METADATA + 1024, bytes=700000000),
                                          'POST_APPEND': dict(raw_bytes=KV_BYTES + VECTOR_BYTES, metadata_bytes=STATE_METADATA + 1024, bytes=700000000),
                                          'TERMINAL': dict(raw_bytes=KV_BYTES + 128 * VECTOR_BYTES, metadata_bytes=STATE_METADATA + 1024, bytes=700000000),
                                          'RESET': dict(raw_bytes=0, metadata_bytes=STATE_METADATA + 1024, bytes=STATE_METADATA + 1024),
                                          'OWNED_EVENT': dict(raw_bytes=VECTOR_BYTES, metadata_bytes=OWNED_METADATA + 1024, bytes=VECTOR_BYTES + OWNED_METADATA + 1024),
                                          'TRANSITION_RECORD': dict(raw_bytes=0, metadata_bytes=RECORD_METADATA, bytes=RECORD_METADATA),
                                          'PRODUCER_RECEIPT': dict(raw_bytes=0, metadata_bytes=MiB, bytes=MiB),
                                      })
        workers.append(dict(id=worker, stage=stage, request_ids=ids,
                            deployment_id=job['placement_id'], timeout_seconds=600,
                            executable_sha256=None, identity_bindings={},
                            row_limit=sum(requests[i]['row_limit'] for i in ids),
                            raw_byte_limit=sum(requests[i]['raw_byte_limit'] for i in ids),
                            metadata_byte_limit=sum(requests[i]['metadata_byte_limit'] for i in ids)))
        deployments.append(dict(id=job['placement_id'], worker=worker, stage=stage, kind='WORKER',
                                backend_inits=1, models=1, contexts=1, placements=1, timeout_seconds=600))
    if len(requests) != 72 or sum(x['row_limit'] for x in requests.values()) != 69354 or len(workers) != 8 or len(deployments) != 10:
        raise ValueError('Frozen request/row/deployment derivation changed')
    if template['role_order'] != ORDER or proposal['accounting']['planned_requests'] != 72:
        raise ValueError('Frozen reference ordering changed')
    checks_path = ROOT.parent / 'n1a_lifecycle_20261112/REQUIRED_COVERAGE.json'
    stage_check_ids = {stage: [] for stage in ORDER}
    checks = json.loads(checks_path.read_text())['checks']
    for check in checks:
        binding = check['bindings']
        if check['scope'] == 'ALIGNED_STATE':
            op = binding['right']['operation_id']
        elif check['scope'] == 'PREFIX_RETENTION':
            op = binding['previous']['operation_id']
        elif check['scope'] == 'OWNED_VECTOR_STABILITY':
            op = binding['source']['operation_id']
        else:
            op = binding['capture']['operation_id']
        stage_check_ids[op.split('/')[1]].append(check['id'])
    if sum(map(len, stage_check_ids.values())) != 261:
        raise ValueError('Required check graph changed')
    limits = {**resources, 'requests': 76, 'rows': 85738, 'placements': 10,
              'backend_inits': 10, 'models': 10, 'contexts': 10,
              'planned_requests': 72, 'planned_rows': 69354,
              'failure_requests': 4, 'failure_rows': 16384, 'max_commands': 250000,
              'deadline_seconds': 18000}
    result = dict(schema='hs.N1a.admission-controller.manifest.v1', mode='CPU_MOCK_ONLY',
                  run_id=None, approval=None, gpu_uuid_sha256=None,
                  native_execution_authorized=False, limits=limits, role_order=ORDER,
                  requests=requests, workers=workers, deployments=deployments,
                  RPC_budget=static_rpc_bound(template),
                  stage_check_ids=stage_check_ids,
                  identity_bindings=dict(model_sha256=proposal['freezes']['model_sha256'],
                                         template_sha256=proposal['freezes']['template_sha256'],
                                         source_sha256=None, producer_sha256=None, writer_sha256=None,
                                         loaded_identity_certificate=None, allocation_lease=None),
                  worker_bindings={w['id']: dict(source_sha256=None, executable_sha256=None, writer_sha256=None,
                                                identity={key: None for key in ('contract_sha256', 'model_sha256', 'tokenizer_sha256', 'template_sha256', 'producer_sha256')},
                                                pid=None, start_time=None, boot_id_sha256=None)
                                   for w in workers},
                  failure_reserve=dict(requests=4, rows=16384, runnable=False, automatic_retry=False,
                                       raw_bytes=4 * RAW_PER_REQUEST, metadata_bytes=4 * REQUEST_METADATA),
                  window=dict(start_wall=None, start_mono=None, deadline_wall=None, deadline_mono=None,
                              last_launch_wall=None, last_launch_mono=None, max_seconds=18000),
                  source_bindings={'native_job_template': sha(template_path), 'frozen_N1a_proposal': sha(PROPOSAL),
                                   'resource_review': sha(OLD / 'review/RESOURCE_PROPOSAL_REVIEW.json'),
                                   'required_261_checks': sha(checks_path)},
                  accounting_rule='One global ledger; per-phase/per-request/per-worker caps intersect aggregate caps; reserved failure quota never supplies a runnable retry',
                  journal_rule='Broker and controller share the same512MiB journal ceiling; no second allowance',
                  N1b=False, N2=False, performance=False)
    return finalize_manifest_cpu(result)


def finalize_manifest_cpu(manifest):
    """Refresh only a CPU manifest digest; no authority/grant is inferred."""
    import copy
    result = copy.deepcopy(manifest)
    result.pop('manifest_sha256', None)
    if result.get('mode') != 'CPU_MOCK_ONLY' or result.get('native_execution_authorized') is not False or result.get('approval') is not None:
        raise ValueError('Digest helper only supports nonauthorizing CPU manifests')
    normalized = json.dumps(result, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    result['manifest_sha256'] = hashlib.sha256(normalized).hexdigest()
    return result


def instantiate_cpu_manifest(run_id, wall_start, mono_start, duration_seconds=18000):
    """Bind a CPU rehearsal clock/run identity, never native approval."""
    if not isinstance(run_id, str) or not run_id or type(duration_seconds) is not int or not (0 < duration_seconds <= 18000):
        raise ValueError('Finite CPU run identity/window required')
    manifest = load_manifest()
    template_sha = manifest.pop('manifest_sha256')
    manifest['frozen_template_sha256'] = template_sha
    manifest['run_id'] = run_id
    end = duration_seconds
    last = max(0, min(6600, end - 600))
    manifest['window'] = dict(start_wall=wall_start, start_mono=mono_start,
                              deadline_wall=wall_start + end, deadline_mono=mono_start + end,
                              last_launch_wall=wall_start + last, last_launch_mono=mono_start + last,
                              max_seconds=18000)
    return finalize_manifest_cpu(manifest)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    with Path(args.out).open('x') as f:
        json.dump(load_manifest(), f, indent=2, sort_keys=True)
        f.write('\n')
