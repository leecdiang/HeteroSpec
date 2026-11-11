"""Frozen CPU q4 frontier diagnostic; importing this module executes no native code."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

SCHEMA = 'heterospec.q4-frontier-protocol.v1'
MODEL_SHA = 'e4b4f329077cc07036a307566f652a35b10e6f41c3b7a98478f2dfca4b09c044'
MODEL_BYTES = 7084832
LEGACY_SHA = '4cc4c7114262bea71957e95478e963486a95cc416a0465d37bb897e971f838ec'
SOURCE_MANIFEST_SHA = '8d37214bb699565c535b52d3fd4439786f3e45c2d40a1aaff6db948c27366a1f'
RECONSTRUCTION_SHA = '0ad149d7441b5d8027dd45c0cfdb2098a12e5a158f6969239b873b754e317198'
LIBRARIES = {
    'libggml-cpu.so.0.23.0': 'c6e6e7451cd331ec3c89e5a8ab417ab3888a59c29585ac33af0c6f0fdf1ae2bc',
    'libggml-base.so.0.23.0': '301735d962b61d5434b19ab9dfafacc9801db8d1fa0319c54c0446320c31bc8f',
    'libllama.so.0.4.0': '445a5cc6f2162287ef7ea003eacbd4427797f85ee9138edcbf376764bfa15d53',
    'libggml.so.0.23.0': '658533d605a997f2850ccc51d1dcacc020b1fa33207cc4d6da3c817e89819813',
}
RAW_BYTE_LIMIT = 256 * 1024 * 1024
NATIVE_TIMEOUT_SECONDS = 180
BUDGET = {'contexts': 14, 'native_calls': 146, 'target_rows': 3612, 'trim_calls': 4, 'model_loads': 1}
ARMS = [
    {'name': 'macro_reference', 'schedule': [4, 4], 'shared_rows': 8, 'frontier': 8, 'reference': None},
    {'name': 'macro_reference_repeat', 'schedule': [4, 4], 'shared_rows': 8, 'frontier': 8, 'reference': 'macro_reference'},
    {'name': 'macro_wide', 'schedule': [8], 'shared_rows': 8, 'frontier': 8, 'reference': 'macro_reference'},
    {'name': 'frontier4_reference', 'schedule': [4], 'shared_rows': 4, 'frontier': 4, 'reference': None},
    {'name': 'frontier4_wide_trim', 'schedule': [8], 'shared_rows': 4, 'frontier': 4, 'reference': 'frontier4_reference'},
    {'name': 'frontier5_reference_materialize', 'schedule': [4, 1], 'shared_rows': 4, 'frontier': 5, 'reference': None},
    {'name': 'frontier5_wide_trim', 'schedule': [8], 'shared_rows': 4, 'frontier': 5, 'reference': 'frontier5_reference_materialize'},
]
SOURCES = ['protocol.py', 'frontier_probe.cpp', 'build.py', 'run.py', 'verify.py', 'test_protocol.py', 'README.md', 'PLAN.json']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def identity(path):
    path = Path(path)
    return {'bytes': path.stat().st_size, 'sha256': digest(path)}


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temporary.replace(path)


def cases():
    return [{'name': f'controlled-p{p}', 'history': [(3 + 7*i) % 128 for i in range(p)],
             'rows': [(p + 5 + 11*i) % 128 for i in range(8)], 'continuation': 37} for p in (248, 252)]


def calculated_budget():
    total = {'contexts': 0, 'native_calls': 0, 'target_rows': 0, 'trim_calls': 0, 'model_loads': 1}
    for case in cases():
        p = len(case['history'])
        for arm in ARMS:
            total['contexts'] += 1
            total['native_calls'] += (p + 31)//32 + len(arm['schedule']) + 1
            total['target_rows'] += p + sum(arm['schedule']) + 1
            total['trim_calls'] += int(sum(arm['schedule']) > arm['frontier'])
    return total


def plan():
    assert calculated_budget() == BUDGET
    return {'schema': SCHEMA, 'status': 'PREPARED_NOT_EXECUTED', 'backend': 'cpu', 'threads': 1,
            'model': {'sha256': MODEL_SHA, 'bytes': MODEL_BYTES, 'trained': False, 'storage': 'F32',
                      'layers': 2, 'vocabulary': 128, 'seed': 178},
            'reference': 'same deployment LOCAL q4+q4 diagnostic; not the historical paper R',
            'prefix_producer_width': 32, 'n_ubatch': 32, 'n_ctx': 1024, 'KV': 'F16', 'flash_attention': False,
            'arms_in_order': ARMS, 'cases': cases(), 'budget': BUDGET, 'raw_byte_limit': RAW_BYTE_LIMIT,
            'owned_native_timeout_seconds': NATIVE_TIMEOUT_SECONDS,
            'qualification': 'Stop at the first required mismatch or guard failure; preserve partial outputs; no retry.',
            'comparison': 'Bitwise full vocabulary vectors and serialized active sequence state; exact native geometry.',
            'frontier5_contract': 'Only the first four operation vectors are shared consumer obligations; the fifth output is saved as a nonconsumer diagnostic and cannot by itself fail the primary contract.',
            'requested_output_masks': 'Original frontend masks unchanged: all operation rows requested; prefix last row per width32 call; continuation one row.',
            'scope': 'Known forced histories and continuations, not natural acceptance, EOG, CAP, production q8 full-mask equivalence, or historical-R qualification.',
            'performance_admitted': False, 'timing_phase': False, 'new_numerical_source': False}


def source_identities(directory):
    return {name: identity(Path(directory)/name) for name in SOURCES}
