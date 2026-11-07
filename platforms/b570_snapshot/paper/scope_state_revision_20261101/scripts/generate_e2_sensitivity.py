#!/usr/bin/env python3
"""Reanalyse the six saved E2 session contrasts; no new model measurements.

The registered bootstrap remains primary. The t interval and leave-one-session
estimates are secondary, post-review checks on the same fixed-input panel.
Uses only the Python standard library.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PINS = {
    'E2_SESSION_CONTRASTS.csv': 'a723987e174f16e33d13e9f257360b66115176ff',
    'e2_summary.csv': 'ca81bd9e8c02bdd99fd61e71b57869175e2ac86d',
}
# Two-sided 95% Student t critical value with 6 - 1 degrees of freedom.
T_CRITICAL_DF5 = 2.570581835636314
FAMILIES = ('Qwen', 'SmolLM2', 'Llama')
PATHS = ('M', 'C')


def git_blob(body: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(body)).encode() + b'\0' + body).hexdigest()


def estimate(logs: list[float]) -> dict:
    if len(logs) != 6 or not all(math.isfinite(x) for x in logs):
        raise ValueError('exactly six finite session log contrasts required')
    mean = math.fsum(logs) / 6
    variance = math.fsum((x - mean) ** 2 for x in logs) / 5
    se = math.sqrt(variance / 6)
    omitted = [math.exp(math.fsum(logs[:i] + logs[i + 1:]) / 5) for i in range(6)]
    return {
        'ratio': math.exp(mean),
        'session_log_mean': mean,
        'session_log_standard_error': se,
        'secondary_t95_lower': math.exp(mean - T_CRITICAL_DF5 * se),
        'secondary_t95_upper': math.exp(mean + T_CRITICAL_DF5 * se),
        'leave_one_session_out': omitted,
        'leave_one_session_min': min(omitted),
        'leave_one_session_max': max(omitted),
        'observed_sessions_above_one': sum(x > 0 for x in logs),
    }


def analyse(root: Path = ROOT) -> dict:
    data = root / 'anc/rtx104'
    for name, expected in SOURCE_PINS.items():
        if git_blob((data / name).read_bytes()) != expected:
            raise ValueError('source Git blob mismatch: ' + name)
    with (data / 'E2_SESSION_CONTRASTS.csv').open(newline='', encoding='utf-8') as stream:
        raw = list(csv.DictReader(stream))
    with (data / 'e2_summary.csv').open(newline='', encoding='utf-8') as stream:
        primary_rows = list(csv.DictReader(stream))
    primary = {(r['family'], r['path']): r for r in primary_rows}
    expected_groups = {(f, p) for f in FAMILIES for p in PATHS}
    if len(raw) != 36 or len(primary_rows) != 6 or set(primary) != expected_groups:
        raise ValueError('incomplete or duplicated E2 comparison groups')
    groups = {}
    for row in raw:
        key = (row['family'], row['path'])
        session = int(row['session'])
        if key not in expected_groups or row['qualified_task_count'] != '12':
            raise ValueError('unexpected E2 family/path or task count')
        values = groups.setdefault(key, {})
        if session in values:
            raise ValueError('duplicate E2 session')
        values[session] = float(row['log_latency_contrast'])
    estimates = []
    for family in FAMILIES:
        for path in PATHS:
            group = groups.get((family, path), {})
            if set(group) != set(range(6)):
                raise ValueError('sessions 0 through 5 required')
            values = estimate([group[s] for s in range(6)])
            source = primary[(family, path)]
            if abs(values['ratio'] - float(source['ratio'])) > 1e-12:
                raise ValueError('secondary point differs from primary estimate')
            estimates.append({
                'family': family, 'path': path,
                'primary_bootstrap95_lower': float(source['lower']),
                'primary_bootstrap95_upper': float(source['upper']),
                'practical_ratio_threshold': float(source['threshold']),
                **values,
            })
    return {
        'analysis_status': 'secondary_post_review_sensitivity',
        'primary_analysis': 'registered session bootstrap, unchanged',
        'source_git_blobs': SOURCE_PINS,
        'unit': 'session mean log(PQ latency / QB latency), fixed 12-input panel',
        'sessions': 6,
        'degrees_of_freedom': 5,
        't_critical_975': T_CRITICAL_DF5,
        't_interval_formula': 'exp(mean(log contrast) +/- t(0.975, 5) * s / sqrt(6))',
        't_interval_assumptions': 'independent, approximately normal session log means',
        'leave_one_session_out_order': list(range(6)),
        'new_model_executions': 0,
        'estimates': estimates,
    }


def table(result: dict) -> str:
    lines = [
        r'\begin{table*}[t]\centering\small',
        r'\caption{E2 session sensitivity on the fixed 12-input panel. Ratios are PQ/QB; $M$ is target-only and $C$ is speculative. The registered bootstrap remains primary. Secondary $t_5$ intervals assume independent, approximately normal session log means. The final column gives the range of six leave-one-session-out point estimates.}\label{tab:e2sensitivity}',
        r'\begin{tabular}{@{}llrrrr@{}}\toprule',
        r'Family & Path & Estimate & Primary bootstrap 95\% CI & Secondary $t_5$ 95\% CI & Omit-one range\\\midrule',
    ]
    for row in result['estimates']:
        family = 'Qwen3' if row['family'] == 'Qwen' else row['family']
        intervals = [f"[{row[a]:.6f}, {row[b]:.6f}]" for a, b in (
            ('primary_bootstrap95_lower', 'primary_bootstrap95_upper'),
            ('secondary_t95_lower', 'secondary_t95_upper'),
            ('leave_one_session_min', 'leave_one_session_max'),
        )]
        lines.append(f"{family} & ${row['path']}$ & {row['ratio']:.6f} & " + ' & '.join(intervals) + r'\\')
    lines.extend([r'\bottomrule\end{tabular}', r'\end{table*}', ''])
    return '\n'.join(lines)


def outputs(root: Path = ROOT) -> dict[str, str]:
    result = analyse(root)
    return {
        'anc/rtx104/e2_sensitivity.json': json.dumps(result, indent=2, allow_nan=False) + '\n',
        'tables/e2_sensitivity.tex': table(result),
    }


if __name__ == '__main__':
    for name, body in outputs().items():
        (ROOT / name).write_text(body, encoding='utf-8')
    print('Generated secondary E2 sensitivity from the six saved sessions; primary bootstrap unchanged.')
