#!/usr/bin/env python3
"""Fail-closed sanity gate for qualification-only 358H UT power traces."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--cpu', type=Path, required=True)
    p.add_argument('--npu', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    cpu = json.loads(args.cpu.read_text(encoding='utf-8-sig'))['domains']['Package_0 Power (mW)']
    npu_doc = json.loads(args.npu.read_text(encoding='utf-8-sig'))['domains']
    npu_pkg = npu_doc['Package_0 Power (mW)']
    npu = npu_doc['NPU (mW)']
    checks = {
        'cpu_package_points_at_least_10': cpu['integration_points'] >= 10,
        'npu_package_points_at_least_10': npu_pkg['integration_points'] >= 10,
        'npu_domain_points_at_least_10': npu['integration_points'] >= 10,
        'all_max_gaps_at_most_500ms': max(cpu['maximum_sampling_delta_us'], npu_pkg['maximum_sampling_delta_us'], npu['maximum_sampling_delta_us']) <= 500_000,
        'cpu_package_scale_1_to_100w': 1 <= cpu['mean_power_w'] <= 100,
        'npu_package_scale_1_to_100w': 1 <= npu_pkg['mean_power_w'] <= 100,
        'npu_domain_scale_0_1_to_50w': 0.1 <= npu['mean_power_w'] <= 50,
        'cpu_load_at_least_twice_idle': cpu['mean_power_w'] >= 2 * max(cpu['pre_marker_median_w'], cpu['post_marker_median_w']),
        'npu_domain_nonzero_under_load': npu['nonzero_samples_in_boundary'] > 0 and npu['mean_power_w'] > 0,
        'npu_domain_zero_idle_medians': npu['pre_marker_median_w'] == 0 and npu['post_marker_median_w'] == 0,
    }
    result = {
        'schema_version': 1,
        'formal_measurement': False,
        'criteria_frozen_before_formal_measurement': True,
        'checks': checks,
        'qualification_pass': all(checks.values()),
        'note': 'Qualification values test units, cadence, and idle-load-idle response only; they are inadmissible as performance results.'
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not result['qualification_pass']:
        raise SystemExit('Unified Telemetry sanity gate failed')


if __name__ == '__main__':
    main()

