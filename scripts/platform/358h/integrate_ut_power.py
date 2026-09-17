#!/usr/bin/env python3
"""Integrate Intel Unified Telemetry Chrome JSON power counters over an ITT task."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def marker_bounds(events: list[dict], marker: str) -> tuple[float, float]:
    exact = [e for e in events if e.get('name') == marker]
    complete = [e for e in exact if str(e.get('ph', '')).upper() == 'X' and 'dur' in e]
    if len(complete) == 1:
        return float(complete[0]['ts']), float(complete[0]['ts']) + float(complete[0]['dur'])
    begins = [e for e in exact if str(e.get('ph', '')).upper() == 'B']
    ends = [e for e in exact if str(e.get('ph', '')).upper() == 'E']
    if len(begins) == 1 and len(ends) == 1:
        return float(begins[0]['ts']), float(ends[0]['ts'])
    raise ValueError(f'expected one complete or B/E ITT marker named {marker!r}; found {len(exact)} events')


def interpolate(a, b, t):
    if b[0] == a[0]:
        return a[1]
    return a[1] + (b[1] - a[1]) * (t - a[0]) / (b[0] - a[0])


def integrate(samples: list[tuple[float, float]], start: float, end: float) -> tuple[float, int]:
    samples = sorted(samples)
    if len(samples) < 2 or start < samples[0][0] or end > samples[-1][0]:
        raise ValueError('marker is not fully covered by the selected sensor')
    points = [(t, v) for t, v in samples if start < t < end]
    for boundary in (start, end):
        for a, b in zip(samples, samples[1:]):
            if a[0] <= boundary <= b[0]:
                points.append((boundary, interpolate(a, b, boundary)))
                break
    points.sort()
    mw_us = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in zip(points, points[1:]))
    return mw_us / 1_000_000_000.0, len(points)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--trace', type=Path, required=True)
    boundary_group = p.add_mutually_exclusive_group(required=True)
    boundary_group.add_argument('--marker')
    boundary_group.add_argument('--boundary', type=Path,
                                help='JSON containing start_perf_counter_ns/end_perf_counter_ns')
    p.add_argument('--calibration', type=Path,
                   help='Required with --boundary; contains qpc_to_ut_offset_us')
    p.add_argument('--sensor', action='append', required=True,
                   help='Exact args key, e.g. Package_0 Power (mW); repeat for multiple separately reported domains')
    p.add_argument('--output-tokens', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    events = json.loads(args.trace.read_text(encoding='utf-8-sig'))
    if isinstance(events, dict):
        events = events.get('traceEvents', [])
    if args.marker:
        start, end = marker_bounds(events, args.marker)
        boundary_method = 'exact ITT task boundary'
    else:
        if not args.calibration:
            p.error('--calibration is required with --boundary')
        boundary = json.loads(args.boundary.read_text(encoding='utf-8-sig'))
        calibration = json.loads(args.calibration.read_text(encoding='utf-8-sig'))
        if not calibration.get('qualification_pass'):
            raise SystemExit('UT clock calibration is not qualified')
        offset = float(calibration['qpc_to_ut_offset_us'])
        start = float(boundary['start_perf_counter_ns']) / 1000 + offset
        end = float(boundary['end_perf_counter_ns']) / 1000 + offset
        boundary_method = 'host perf_counter/QPC boundary translated with adjacent qualified ITT clock calibration'
    domains = {}
    for sensor in args.sensor:
        samples = []
        for event in events:
            value = event.get('args', {}).get(sensor)
            if isinstance(value, (int, float)) and 'ts' in event:
                samples.append((float(event['ts']), float(value)))
        energy_j, points = integrate(samples, start, end)
        within = [v for t, v in samples if start <= t <= end]
        before = [v for t, v in samples if start - 5_000_000 <= t < start]
        after = [v for t, v in samples if end < t <= end + 5_000_000]
        deltas = [b[0] - a[0] for a, b in zip(samples, samples[1:])]
        domains[sensor] = {
            'unit': 'mW input; J after integration',
            'samples_total': len(samples),
            'integration_points': points,
            'nonzero_samples_in_boundary': sum(abs(v) > 0 for v in within),
            'median_sampling_delta_us': statistics.median(deltas) if deltas else None,
            'maximum_sampling_delta_us': max(deltas) if deltas else None,
            'mean_power_w': energy_j / ((end - start) / 1_000_000),
            'energy_j': energy_j,
            'energy_j_per_output_token': energy_j / args.output_tokens,
            'pre_marker_median_w': statistics.median(before) / 1000 if before else None,
            'post_marker_median_w': statistics.median(after) / 1000 if after else None,
        }
    result = {
        'schema_version': 1,
        'trace': str(args.trace.resolve()),
        'marker': args.marker,
        'marker_start_us': start,
        'marker_end_us': end,
        'duration_s': (end - start) / 1_000_000,
        'method': boundary_method + '; linear boundary interpolation; trapezoidal integration',
        'domains_reported_separately': True,
        'domains': domains,
        'formal_measurement': False if args.marker and args.marker.startswith('qualification|') else True,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
