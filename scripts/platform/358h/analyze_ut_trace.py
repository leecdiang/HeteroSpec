#!/usr/bin/env python3
"""Inventory power/NPU event names in an Intel Unified Telemetry Perfetto JSON."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk(child)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument('--trace', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--require-npu', action='store_true')
    args = p.parse_args()
    document = json.loads(args.trace.read_text(encoding='utf-8-sig'))
    terms = ('power', 'energy', 'watt', 'package', 'npu', 'socwatch', 'pwr')
    found = Counter()
    numeric_domains: dict[str, list[float]] = defaultdict(list)
    for obj in walk(document):
        for key in ('name', 'cat', 'category', 'metric', 'domain', 'track'):
            value = obj.get(key)
            if isinstance(value, str) and any(term in value.lower() for term in terms):
                found[value] += 1
        arguments = obj.get('args')
        if isinstance(arguments, dict):
            for key, value in arguments.items():
                if isinstance(key, str) and any(term in key.lower() for term in terms):
                    found[key] += 1
                    if isinstance(value, (int, float)):
                        numeric_domains[key].append(float(value))
    names = sorted(found)
    package_present = any(('package' in n.lower() or 'pkg' in n.lower()) and any(x in n.lower() for x in ('power', 'energy', 'pwr')) for n in names)
    npu_domains = {k: v for k, v in numeric_domains.items() if 'npu' in k.lower()}
    npu_present = any(v for v in npu_domains.values())
    npu_nonzero = any(any(abs(x) > 0 for x in values) for values in npu_domains.values())
    result = {
        'schema_version': 1,
        'trace': str(args.trace.resolve()),
        'candidate_event_names': [{'name': n, 'occurrences': found[n]} for n in names],
        'numeric_domains': {
            name: {
                'samples': len(values),
                'nonzero_samples': sum(abs(x) > 0 for x in values),
                'minimum': min(values),
                'maximum': max(values)
            } for name, values in sorted(numeric_domains.items()) if values
        },
        'package_power_or_energy_present': package_present,
        'npu_power_or_energy_present': npu_present,
        'npu_nonzero_activity_present': npu_nonzero,
        'qualified': package_present and ((npu_present and npu_nonzero) or not args.require_npu),
        'note': 'Name discovery is only the first gate; units, cadence, gaps, idle-load-idle response, and overhead still require qualification.'
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    if not result['qualified']:
        required = 'Package and NPU' if args.require_npu else 'Package'
        raise SystemExit(f'Required {required} power/energy domains were not identified.')


if __name__ == '__main__':
    main()

