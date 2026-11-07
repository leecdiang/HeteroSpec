"""Describe E2 absolute request cost using the registered equal-task/session weights.

No new measurement or inference is performed. The input retains all warmups;
only the registered warmup rows are excluded from the estimates.
"""
import csv
import hashlib
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'anc/rtx104/E2_REQUEST_LATENCIES.csv'
SOURCE_BLOB = '975240c96131f28f538314938e8269a08bd0d7d6'
PRIMARY_BLOB = 'ca81bd9e8c02bdd99fd61e71b57869175e2ac86d'


def generate(root=ROOT):
    raw = (root / 'anc/rtx104/E2_REQUEST_LATENCIES.csv').read_bytes()
    blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
    if blob != SOURCE_BLOB:
        raise ValueError('source request table differs from pinned Git blob')
    rows = list(csv.DictReader(raw.decode().splitlines()))
    if (len(rows) != 1620 or sum(r['warmup'] == 'True' for r in rows) != 324
            or sum(r['arm'] == 'R' and r['warmup'] == 'False' for r in rows) != 432
            or not all(r['contract_valid'] == 'True' for r in rows)):
        raise ValueError('E2 request accounting or qualification mismatch')
    cells = defaultdict(dict)
    for r in rows:
        value = float(r['latency_ms'])
        if not math.isfinite(value) or value <= 0:
            raise ValueError('finite positive request latency required')
        if r['warmup'] == 'True' or r['arm'] == 'R':
            continue
        if r['warmup'] != 'False':
            raise ValueError('unexpected warmup marker')
        key = (r['family'], r['arm'], int(r['session']))
        task = r['slot'].split('|')[-1]
        if task in cells[key]:
            raise ValueError('duplicate measured E2 task')
        cells[key][task] = value
    results = []
    for family in ('Qwen', 'SmolLM2', 'Llama'):
        vals = {}
        for arm in ('M_PQ', 'M_QB', 'C_PQ', 'C_QB'):
            sessions = []
            for session in range(6):
                values = cells[family, arm, session]
                if len(values) != 12:
                    raise ValueError('twelve measured tasks per session required')
                sessions.append(statistics.mean(math.log(x) for x in values.values()))
            vals[arm] = math.exp(statistics.mean(sessions))
        results.append(dict(family=family, **vals,
                            M_ratio=vals['M_PQ']/vals['M_QB'],
                            C_ratio=vals['C_PQ']/vals['C_QB']))
    # Absolute GMs and paired contrasts use the same complete balanced panel.
    # Their ratio must reproduce the original published E2 point estimate.
    primary_raw = (root / 'anc/rtx104/e2_summary.csv').read_bytes()
    primary_blob = hashlib.sha1(b'blob ' + str(len(primary_raw)).encode() + b'\0' + primary_raw).hexdigest()
    if primary_blob != PRIMARY_BLOB:
        raise ValueError('primary E2 summary differs from pinned Git blob')
    primary = {(r['family'], r['path']): float(r['ratio'])
               for r in csv.DictReader(primary_raw.decode().splitlines())}
    for result in results:
        for path in ('M', 'C'):
            if abs(result[path + '_ratio'] - primary[result['family'], path]) > 1e-12:
                raise ValueError('absolute latency ratio differs from published E2 estimate')
    return results


def outputs(root=ROOT):
    results = generate(root)
    summary = json.dumps(dict(
        unit='ms', statistic='geometric mean; equal tasks within session and equal six-session weights',
        source_git_blob=SOURCE_BLOB, primary_summary_git_blob=PRIMARY_BLOB,
        rows=results), indent=2, allow_nan=False) + '\n'
    lines = [r'\begin{tabular}{lrrrr}', r'\toprule',
             r'Family & $M_{\mathrm{PQ}}$ & $M_{\mathrm{QB}}$ & $C_{\mathrm{PQ}}$ & $C_{\mathrm{QB}}$ \\',
             r'\midrule']
    for r in results:
        display = 'Qwen3' if r['family'] == 'Qwen' else r['family']
        lines.append(display + ' & ' + ' & '.join(f"{r[a]:.1f}" for a in ('M_PQ', 'M_QB', 'C_PQ', 'C_QB')) + r' \\')
    lines.extend([r'\bottomrule', r'\end{tabular}'])
    return {'anc/rtx104/e2_absolute_cost.json': summary,
            'tables/e2_absolute_cost.tex': '\n'.join(lines) + '\n'}


def verify(check, root=ROOT):
    from check_closure import derived_json_equal, read_derived_json
    for name, expected in outputs(root).items():
        actual = (root / name).read_text()
        consistent = (derived_json_equal(read_derived_json(actual), read_derived_json(expected))
                      if name.endswith('.json') else actual == expected)
        check('Absolute E2 latency source/derived consistency: ' + name, consistent)
    return {'status': 'PASS', 'source_git_blob': SOURCE_BLOB,
            'published_ratio_crosschecks': 6, 'new_model_executions': 0}


def main():
    for name, text in outputs().items():
        (ROOT / name).write_text(text)
    print('Generated E2 absolute cost; all six ratios reproduce published E2 estimates.')


if __name__ == '__main__':
    main()
