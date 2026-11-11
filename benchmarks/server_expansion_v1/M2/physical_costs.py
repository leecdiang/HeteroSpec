"""Data-only completed-worker physical/caller work and cost reconciliation."""
from pathlib import Path
from collections import Counter
import argparse, hashlib, json


def read(p):
    return json.loads(p.read_text())


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def analyze(root):
    assert read(root / 'm2-audit-03/STATUS.json')['status'] == 'COMPLETE'
    rows = []
    for epoch in (1, 2, 3):
        work = root / f'm2-run-{epoch:02d}'
        for e in map(json.loads, (work / 'ledger.jsonl').read_text().splitlines()):
            if e['event'] != 'RESERVE':
                continue
            dest = Path(e['out'])
            host = read(dest / 'HOST.json')
            p = dest / 'native/result.json'
            target = draft = None
            source = 'No completed physical-row receipt: unknown, not observed zero'
            if host['status'] == 'COMPLETE':
                meta = read(p)
                assert meta['status'] == 'COMPLETE'
                if meta.get('schema') == 'linux-transfer.reference.v1':
                    assert meta['n_ubatch'] == meta['output_reserve'] == 1
                    target = sum(read(dest / 'native' / x['record'])['materialized_tokens'] for x in meta['requests'])
                    target += sum(x['materialized_tokens'] for x in meta['cases'])
                    draft = 0
                    source = 'Derived from unchanged scalar-R UB1/dense-append contract and native materialized_tokens; no added physical histogram'
                else:
                    target = draft = 0
                    for x in meta.get('requests', []):
                        r = read(dest / 'native' / x['record'])
                        target += sum(int(k) * v for k, v in r['target_physical_width_hist'].items())
                        draft += sum(int(k) * v for k, v in r['draft_physical_width_hist'].items())
                    target += sum(sum(x['width'] for x in c['executions']) for c in meta.get('cases', []))
                    for tape in meta.get('proposal_tapes', []):
                        assert tape['target_calls'] == tape['target_rows'] == 0
                        assert tape['draft_rows'] == sum(int(k) * v for k, v in tape['draft_physical_width_hist'].items())
                        draft += tape['draft_rows']
                    assert target + draft == meta['token_rows']
                    source = 'Actual M2 target/draft physical histograms, forced execution widths or native producer histograms'
            rows.append(dict(epoch=epoch, out=str(dest.relative_to(root)), phase=e['phase'],
                reserved_requests=e['requests'], reserved_rows=e['rows'], native_status=host['status'],
                worker_wall_s=host['worker_wall_s'], target_rows=target, draft_rows=draft, row_evidence=source,
                native_result_sha256=sha(p) if p.exists() else None, expected_negative='negative-' in dest.name))
    requests = sum(x['reserved_requests'] for x in rows)
    bound = sum(x['reserved_rows'] for x in rows)
    return dict(schema='heterospec.m2.complete-cost-addendum.v2', workers=rows,
        total_reserved_workers=len(rows), reserved_requests=requests, reserved_row_bound=bound,
        native_status_counts=dict(Counter(x['native_status'] for x in rows)),
        native_worker_wall_known_s=sum(x['worker_wall_s'] for x in rows if x['worker_wall_s'] is not None),
        M2_direct_target_rows=sum(x['target_rows'] for x in rows if x['row_evidence'].startswith('Actual')),
        M2_direct_draft_rows=sum(x['draft_rows'] for x in rows if x['row_evidence'].startswith('Actual')),
        scalar_R_derived_rows=sum(x['target_rows'] for x in rows if x['row_evidence'].startswith('Derived')),
        failed_workers_without_complete_physical_row_receipt=[x['out'] for x in rows if x['target_rows'] is None],
        cumulative_PR197=dict(requests=857 + 382 + requests, ceiling_requests=2048,
            reserved_rows=1552339 + 889908 + bound, ceiling_rows=8000000),
        clock_scope='Worker walls include hash/load/request string/observers; not GPU kernel time. Stage/worker/service/adapter clocks overlap; do not add.',
        row_scope='Direct M2 and derived scalar-R rows reported separately. Failed incomplete row receipts are unknown; reserved bounds remain charged.',
        new_native_jobs=0, model_forwards=0)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.root.resolve())
    with a.out.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'workers'}), flush=True)
