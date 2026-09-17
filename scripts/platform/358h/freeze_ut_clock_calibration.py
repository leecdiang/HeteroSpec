#!/usr/bin/env python3
"""Freeze QPC/perf_counter_ns to Unified Telemetry microsecond clock mapping."""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--pair', action='append', nargs=3, metavar=('PROBE_JSON', 'TRACE_JSON', 'MARKER'), required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--max-spread-us', type=float, default=5000)
    args = p.parse_args()
    offsets = []
    records = []
    for probe_name, trace_name, marker in args.pair:
        probe = json.loads(Path(probe_name).read_text(encoding='utf-8-sig'))
        trace = json.loads(Path(trace_name).read_text(encoding='utf-8-sig'))
        events = trace.get('traceEvents', []) if isinstance(trace, dict) else trace
        found = [e for e in events if e.get('name') == marker and str(e.get('ph', '')).upper() == 'X']
        if len(found) != 1:
            raise SystemExit(f'expected one complete marker {marker!r}')
        event = found[0]
        start_offset = float(event['ts']) - float(probe['start_perf_counter_ns']) / 1000
        end_offset = float(event['ts']) + float(event['dur']) - float(probe['end_perf_counter_ns']) / 1000
        offsets.extend((start_offset, end_offset))
        records.append({'probe': probe_name, 'trace': trace_name, 'marker': marker,
                        'start_offset_us': start_offset, 'end_offset_us': end_offset})
    spread = max(offsets) - min(offsets)
    result = {
        'schema_version': 1,
        'qpc_to_ut_offset_us': statistics.mean(offsets),
        'offset_spread_us': spread,
        'maximum_allowed_spread_us': args.max_spread_us,
        'qualification_pass': spread <= args.max_spread_us,
        'records': records,
        'policy': 'Repeat adjacent to each formal trace before and after; reject the trace if combined spread/drift exceeds 5 ms.'
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not result['qualification_pass']:
        raise SystemExit('clock calibration spread exceeded threshold')


if __name__ == '__main__':
    main()
