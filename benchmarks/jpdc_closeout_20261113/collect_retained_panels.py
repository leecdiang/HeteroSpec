"""Read existing native JSON receipts and replay the frozen legacy analyzer. No model execution."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

from recompute_panels import estimate, compare

LEGACY_SHA = '8b1d0f7b794132bf5a33208d5c85124246bd112685f8bf33283156b70d7b0887'
STUDIES = {'pr205': 'f-run-01', 'pr206': 'd14-run-01', 'pr208': 'd14-attribution-run-01'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--private-root', type=Path, required=True)
    p.add_argument('--legacy-analyzer', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise ValueError('Fresh output required; existing evidence is retained')
    if hashlib.sha256(args.legacy_analyzer.read_bytes()).hexdigest() != LEGACY_SHA:
        raise ValueError('Wrong analyzer; use docs/merge_audits/20261111/legacy_shared/experiment.py')
    spec = importlib.util.spec_from_file_location('frozen_statistics_only', args.legacy_analyzer)
    legacy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(legacy)
    args.out.mkdir(parents=True)
    reports = []
    for study, directory in STUDIES.items():
        panel = args.private_root / directory / 'panel-01'
        plan = json.loads((panel / 'PLAN.json').read_text())
        records = json.loads((panel / 'ANALYZER_RECORDS.private.json').read_text())['records']
        saved_bytes = (panel / 'RESULTS.json').read_bytes()
        original = json.loads(saved_bytes)
        # This exact historical module checks every original receipt SHA itself.
        if legacy.analyze(plan, records) != original:
            raise ValueError('Frozen analysis did not reproduce exactly: ' + study)
        safe = []
        bindings = []
        for row in records:
            source = Path(row['evidence_path'])
            raw = source.read_bytes()
            receipt = json.loads(raw)
            if receipt['service_seconds'] != row['service_s']:
                raise ValueError('Actual receipt metric mismatch')
            safe.append(dict(root=row['root'], session=row['session'], arm=row['arm'],
                             service_s=format(receipt['service_seconds'], '.17g')))
            bindings.append(dict(logical_receipt=str(source.relative_to(args.private_root)),
                                 original_sha256=hashlib.sha256(raw).hexdigest()))
        compare(estimate(plan, safe), original)
        target = args.out / study
        target.mkdir()
        # Publish only mathematical plan fields, not allocation/host metadata.
        public_plan = {k: plan[k] for k in (
            'roots', 'arms', 'sessions', 'contrasts', 'interaction', 'seed',
            'bootstrap_draws', 'inference', 'sample_scope', 'metric')}
        (target / 'PLAN.json').write_text(json.dumps(public_plan, indent=2) + '\n')
        (target / 'ORIGINAL_RESULTS.json').write_bytes(saved_bytes)
        with (target / 'TIMING_ROWS.csv').open('x', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['root', 'session', 'arm', 'service_s'], lineterminator='\n')
            writer.writeheader()
            writer.writerows(safe)
        proof = dict(study=study, status='PASS_FROZEN_EXACT_AND_INDEPENDENT_CI',
                     formal_rows=len(records), roots=len(plan['roots']),
                     original_plan_sha256=hashlib.sha256((panel / 'PLAN.json').read_bytes()).hexdigest(),
                     original_results_sha256=hashlib.sha256(saved_bytes).hexdigest(),
                     legacy_analyzer_sha256=LEGACY_SHA, receipt_bindings=bindings,
                     captured_numeric_payloads_requalified=False, model_calls=0)
        (target / 'REPLAY_CHECK.json').write_text(json.dumps(proof, indent=2) + '\n')
        reports.append({k: proof[k] for k in ('study', 'status', 'formal_rows', 'roots')})
    (args.out / 'REPLAY_SUMMARY.json').write_text(json.dumps(dict(
        status='PASS', studies=reports, model_calls=0, GPU_contexts=0), indent=2) + '\n')
    print(json.dumps(reports))


if __name__ == '__main__':
    main()
