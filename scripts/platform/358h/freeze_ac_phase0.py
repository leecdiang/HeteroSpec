#!/usr/bin/env python3
"""Recompute replacement 358H Phase-0 gate from AC-qualified evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
Q = ROOT / 'runs/358h/qualification_ac_20260918'


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding='utf-8-sig'))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    evidence = {
        'environment_cpu': 'runs/358h/qualification_ac_20260918/environment_cpu.json',
        'cpu_smoke': 'runs/358h/qualification_ac_20260918/openvino_ir_smoke_cpu.json',
        'npu_smoke_8192': 'runs/358h/qualification_ac_20260918/openvino_ir_smoke_npu_ctx8192.json',
        'npu_binding_8192': 'runs/358h/qualification_ac_20260918/npu_cache_binding_ctx8192.json',
        'ut_cpu_manifest': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/cpu-ut.manifest.json',
        'ut_npu_manifest': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/npu-ut.manifest.json',
        'ut_sensor_sanity': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/sensor_sanity_gate.json',
        'ut_clock_calibration': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/clock_calibration.json',
        'ut_cpu_integration': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/cpu-power-integration.json',
        'ut_npu_integration': 'runs/358h/qualification_ac_20260918/unified_telemetry_smoke_100ms/npu-power-integration.json',
        'cpu_energy_overhead_short': 'runs/358h/qualification_ac_20260918/telemetry_overhead_v5_windows_rapl/overhead_qualification.json',
        'cpu_energy_overhead_representative': 'runs/358h/qualification_ac_20260918/telemetry_overhead_v6_phase1like/overhead_qualification.json',
        'cpu_energy_overhead_isolated': 'runs/358h/qualification_ac_20260918/telemetry_overhead_v7_phase1like_isolated/overhead_qualification.json',
        'npu_energy_overhead_last_attempt': 'runs/358h/qualification_ac_20260918/telemetry_overhead_v4_100ms_minimal/npu/overhead_qualification.json',
        'target_model': 'runs/358h/qualification_ac_20260918/target_model_manifest.json',
        'power_state_after': 'runs/358h/qualification_ac_20260918/power_state_after.json',
        'package_freeze': 'runs/358h/qualification_ac_20260918/pip-freeze.txt'
    }
    missing = [path for path in evidence.values() if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit('Phase-0 evidence missing: ' + ', '.join(missing))
    docs = {key: load(path) for key, path in evidence.items() if path.endswith('.json')}
    checks = {
        'cpu_low_level_binding': docs['environment_cpu'].get('qualification_pass') is True and 'CPU' in str(docs['environment_cpu']['devices']['CPU']['model_probe']['execution_devices']).upper(),
        'cpu_bounded_smoke': str(docs['cpu_smoke'].get('status', '')).startswith('PASS'),
        'npu_8192_bounded_smoke': str(docs['npu_smoke_8192'].get('status', '')).startswith('PASS'),
        'npu_strict_execution_devices': docs['npu_binding_8192'].get('qualification_pass') is True and str(docs['npu_binding_8192'].get('actual_execution_devices')).upper() == 'NPU',
        'ut_sensor_sanity': docs['ut_sensor_sanity'].get('qualification_pass') is True,
        'ut_clock_calibration': docs['ut_clock_calibration'].get('qualification_pass') is True and docs['ut_clock_calibration'].get('offset_spread_us', 1e9) <= 5000,
        'ut_cpu_ac': docs['ut_cpu_manifest'].get('power_online') is True and docs['ut_cpu_manifest'].get('discharging') is False,
        'ut_npu_ac': docs['ut_npu_manifest'].get('power_online') is True and docs['ut_npu_manifest'].get('discharging') is False,
        'telemetry_boundary_documented': (ROOT / 'reports/358h/358H_TELEMETRY_GATE_AUDIT.md').is_file(),
        'target_model_frozen': docs['target_model'].get('sha256') == '408b955510e196121c1c375201744783b5c9a43c7956d73fc78df54c66e883d6' and docs['target_model'].get('bytes') == 8_709_518_112,
        'power_state_after': docs['power_state_after'].get('power_online') is True and docs['power_state_after'].get('discharging') is False,
        'no_formal_data': all(doc.get('formal_measurement') is not True for key, doc in docs.items() if key not in ('power_state_after', 'target_model'))
    }
    artifacts = []
    for role, relative in evidence.items():
        path = ROOT / relative
        artifacts.append({'role': role, 'path': relative, 'bytes': path.stat().st_size, 'sha256': sha256(path)})
    for role in ('ut_cpu_manifest', 'ut_npu_manifest'):
        for artifact in docs[role].get('artifacts', []):
            path = Path(artifact['path'])
            if path.name.endswith('.manifest.json'):
                continue
            actual = sha256(path)
            if actual != artifact['sha256']:
                checks[f'{role}:{path.name}:hash'] = False
    passed = all(checks.values())
    energy_admissibility = {
        'cpu_package': {
            'admissible': docs['cpu_energy_overhead_short'].get('qualification_pass') is True and (
                docs['cpu_energy_overhead_representative'].get('qualification_pass') is True
                or docs['cpu_energy_overhead_isolated'].get('qualification_pass') is True
            ),
            'boundary': 'RAPL_Package0_PKG package power via Windows Energy Meter direct PDH API',
            'claim_limit': 'CPU package energy only; not wall/system energy and not an isolated CPU-core domain. If only the isolated representative gate passes, the energy-only workload must remain pinned to CPUs 0-11 and the collector to CPUs 12-15.',
        },
        'npu': {
            'admissible': False,
            'reason': 'The latest minimal SocWatch qualification failed the unchanged 1% overhead gate; package RAPL does not isolate NPU energy.',
        },
        'symmetric_cpu_vs_npu_energy_comparison': False,
    }
    manifest = {
        'schema': 'heterospec.358h.phase0_ac_requalification.v2',
        'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': ['CPU draft', 'NPU draft'],
        'supersedes_invalid_commit': 'a957791b9a13fe51a35e62b66a12f88ace83a6bb',
        'checks': checks,
        'qualification_pass': passed,
        'qualification_scope': 'core latency and break-even study; energy is a separately qualified conditional track',
        'energy_admissibility': energy_admissibility,
        'formal_data_collected': False,
        'artifacts': artifacts,
        'scientific_provenance': 'Canonical GGUF provenance and STRONGLY_SUPPORTED OpenVINO reconstruction are inherited unchanged from the frozen Phase-0 provenance records.'
    }
    (Q / 'phase0_ac_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    gate = {
        'schema_version': 5,
        'platform': 'Intel Core Ultra X7 358H',
        'scope': ['CPU draft', 'NPU draft'],
        'status': 'PASS' if passed else 'FAIL',
        'qualification_pass': passed,
        'qualification_scope': 'core latency and break-even study',
        'energy_admissibility': energy_admissibility,
        'formal_measurement_authorized': False,
        'reason_formal_not_authorized': (
            'Phase-1 preregistration must be frozen and committed after this gate.'
            if passed else
            'Phase-0 qualification failed: ' + ', '.join(name for name, ok in checks.items() if not ok)
        ),
        'replacement_manifest': 'runs/358h/qualification_ac_20260918/phase0_ac_manifest.json',
        'formal_data_collected': False
    }
    (ROOT / 'runs/358h/qualification/phase0_gate.json').write_text(json.dumps(gate, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'qualification_pass': passed, 'checks': checks}, indent=2))
    if not passed:
        raise SystemExit(2)


if __name__ == '__main__':
    main()

