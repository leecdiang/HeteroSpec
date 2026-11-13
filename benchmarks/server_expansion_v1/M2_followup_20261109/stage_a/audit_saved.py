"""Zero-GPU accounting of bound M2 receipts; never executes a native binary."""
from pathlib import Path
from decimal import Decimal
import argparse, hashlib, importlib.util, json, sys

PR210_ZERO_GPU_AUDIT = True


def read(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def save(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def main():
    a = argparse.ArgumentParser()
    a.add_argument('--root', type=Path, required=True)
    a.add_argument('--out', type=Path, required=True)
    args = a.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = root / 'm2-run-03'
    panel = work / 'panel-01'
    driver = root / 'm2-driver-source-03'
    freeze = read(work / 'SOURCE_FREEZE.json')
    for path, digest in freeze['driver_sources'].items():
        assert sha(Path(path)) == digest, path
    spec = importlib.util.spec_from_file_location('bound_exporter', driver / 'postprocess_v2.py')
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    exporter.replay(root, work, out, driver)
    exporter.costs(root, work, out)
    prior = root / 'm2-public-export-02/analysis'
    for name in ('RESULTS_REPRODUCED.json', 'COSTS.json'):
        assert read(out / name) == read(prior / name), name
    checked, plan = read(panel / 'CHECKED.json'), read(panel / 'PLAN.json')
    vocab = read(panel / 'runs' / checked[0]['id'] / 'native/result.json')['vocab']
    modes = {}
    for mode in ('live', 'replay'):
        arms = {}
        for arm in plan['arms']:
            totals = {k: Decimal(0) for k in ('service', 'request', 'setup', 'teardown', 'target_prefill', 'target_verify', 'draft', 'planning', 'output_copy')}
            counts = dict(requests=0, cycles=0, proposed=0, accepted=0, first_rejected_mismatch=0,
                          unexamined_after_rejection=0, terminal_cap_unconsumed=0, terminal_eog_unconsumed=0,
                          output_tokens=0, target_rows=0, draft_rows=0, verify_rows=0, owned_target_vectors=0,
                          target_decode_calls=0, draft_decode_calls=0)
            for w in checked:
                if w['proposal_mode'] != mode or w['arm'] != arm:
                    continue
                for i, c in enumerate(w['calls']):
                    if c['kind'] != 'measurement':
                        continue
                    path = panel / 'runs' / w['id'] / 'native' / ('request-' + str(i)) / 'receipt.json'
                    assert sha(path) == c['receipt_sha256']
                    r = json.loads(path.read_text(), parse_float=Decimal)
                    assert not r['capture'] and all(v == 0 for v in r['observed_API_calls_within_service'].values())
                    for key, field in [('service', 'service_seconds'), ('request', 'request_seconds'), ('setup', 'setup_seconds'), ('teardown', 'teardown_seconds'), ('planning', 'planning_s'), ('output_copy', 'output_copy_s')]:
                        totals[key] += r[field]
                    totals['target_prefill'] += r['target_phases'].get('PREFILL', 0)
                    totals['target_verify'] += r['target_phases'].get('VERIFY', 0)
                    totals['draft'] += sum(r['draft_phases'].values())
                    counts['requests'] += 1
                    counts['output_tokens'] += len(r['ids'])
                    counts['target_rows'] += c['physical']['target_rows']
                    counts['draft_rows'] += c['physical']['draft_rows']
                    counts['verify_rows'] += sum(e['width'] for e in r['executions'] if e['phase'] == 'VERIFY')
                    counts['owned_target_vectors'] += 1 + (r['k'] + 1) * len(r['cycles'])
                    counts['target_decode_calls'] += r['target_calls']
                    counts['draft_decode_calls'] += r['draft_calls']
                    for cycle in r['cycles']:
                        k, accepted = r['k'], cycle['accepted']
                        counts['cycles'] += 1
                        counts['proposed'] += k
                        counts['accepted'] += accepted
                        if cycle['rejected']:
                            assert cycle['decisions'][accepted] != cycle['proposals'][accepted]
                            counts['first_rejected_mismatch'] += 1
                            counts['unexamined_after_rejection'] += k - accepted - 1
                        elif accepted < k:
                            assert cycle['done'] and cycle['commit_kind'] == 'accepted'
                            key = 'terminal_cap_unconsumed' if r['stop_reason'] == 'CAP' else 'terminal_eog_unconsumed'
                            counts[key] += k - accepted
            assert counts['proposed'] == sum(counts[k] for k in ('accepted', 'first_rejected_mismatch', 'unexamined_after_rejection', 'terminal_cap_unconsumed', 'terminal_eog_unconsumed'))
            totals['residual'] = totals['service'] - totals['target_prefill'] - totals['target_verify'] - totals['draft']
            # These fields overlap the residual; this subtraction is bookkeeping,
            # not a newly measured component or a kernel-time attribution.
            totals['residual_less_copy_planning_setup_teardown'] = totals['residual'] - totals['output_copy'] - totals['planning'] - totals['setup'] - totals['teardown']
            sync_sites = counts['target_decode_calls'] + counts['draft_decode_calls'] + counts['owned_target_vectors'] + 2 * counts['requests']
            if mode == 'live':
                sync_sites += counts['proposed']
            arms[arm] = dict(seconds={k: str(v) for k, v in totals.items()}, counts=counts,
                verify_seconds_per_row=str(totals['target_verify'] / counts['verify_rows']),
                target_owned_vector_bytes=counts['owned_target_vectors'] * vocab * 4,
                source_derived_synchronize_API_sites=sync_sites,
                synchronize_scope='Static call sites implied by bound code and recorded calls; not measured waits, kernel launches or a timing attribution')
        modes[mode] = arms
    deltas = {}
    for mode, arms in modes.items():
        left, right = arms['L_P_K3'], arms['L_P_K7']
        d = {k: str(Decimal(right['seconds'][k]) - Decimal(left['seconds'][k])) for k in left['seconds']}
        assert Decimal(d['service']) == sum(Decimal(d[k]) for k in ('target_prefill', 'target_verify', 'draft', 'residual'))
        deltas[mode] = d
    selection = read(work / 'ROOT_SELECTION.json')
    origins = []
    for key in selection['roots']:
        prompt = selection['inputs'][key]['prompt_ids']
        receipt = selection['expected'][key]['receipt']
        available = len(prompt) + len(receipt['ids'])
        origins.append(dict(root=key,initial_prompt_tokens=len(prompt),frozen_R_continuation_tokens=len(receipt['ids']),
            frozen_token_stream_length=available,terminal_kind=receipt.get('terminal_kind', receipt.get('stop_reason')),
            within248_eight_tokens_available=available >= 256,cross252_eight_tokens_available=available >= 260,
            missing_tokens_for_cross252=max(0,260-available),oracle_receipt_sha256=selection['expected'][key]['sha256']))
    save(out / 'STAGE_A_ACCOUNTING.json', dict(schema='heterospec.pr210.stage-a.v1',modes=modes,LOCAL_packed_k7_minus_k3=deltas,
        convention='Exact decimal sums of archived clean measurement receipt scalars. Planning/copy/setup/teardown are nested in service and must not be added again. Residual is unassigned, not logging or kernel time.',
        mismatch_scope='Only the first compared mismatch per rejecting cycle is labelled observed rejected. Later unexamined suffixes are separate from cap/EOG unconsumed proposals.',new_native_requests=0,new_GPU_forwards=0))
    save(out / 'STAGE_B_ORIGIN_INVENTORY.json',dict(origins=origins,all_four_bound_origins_ready=all(x['cross252_eight_tokens_available']for x in origins),
        first_prespecified_timing_origin_ready=origins[0]['cross252_eight_tokens_available'],
        decision='No silent padding, substitution or continuation extension. Stage B requires an explicit remedy/admission for short frozen continuations before its full matrix.',new_native_requests=0))
    save(out / 'CHECKED.json',dict(passed=True,saved_request_receipts_replayed=144,
        reported_results_sha256=sha(prior/'RESULTS_REPRODUCED.json'),reproduced_results_sha256=sha(out/'RESULTS_REPRODUCED.json'),
        saved_complete_costs_reproduced=True,new_native_requests=0,new_GPU_forwards=0,
        source_bindings_preserved=True,scope='Saved-record accounting only, not a new numerical qualification or performance measurement'))
    print(json.dumps(dict(passed=True,new_native_requests=0,new_GPU_forwards=0,live_delta=deltas['live'],origins=origins)),flush=True)


if __name__ == '__main__':
    main()
