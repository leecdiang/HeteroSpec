#!/usr/bin/env python3
"""Rebuild and run ONLY standard-library synthetic tests, never native ELFs.

Fresh short absolute --out required; failures/logs/partial fixtures are retained.
No model, vocabulary, backend, device query or native linked binary is invoked.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ALLOWED = {
    'budget_writer/hooks.hpp', 'budget_writer/posix.hpp',
    'budget_writer/sha256.hpp', 'budget_writer/durable_budget.hpp',
    'budget_writer/stream_writer.hpp', 'budget_writer/accounting_ipc.hpp',
    'budget_writer/launch_gate.hpp', 'budget_writer/test_mock.cpp',
    'budget_writer/test_ipc_mock.cpp', 'native/session.hpp',
    'native/raw_checks.hpp', 'native/active_kv_host.hpp',
    'native/test_active_kv_host.cpp', 'review/independent_budget_writer_mock.cpp',
    'review/independent_session_mock.cpp', 'review/independent_raw_checks_mock.cpp',
}
STDLIB = {'libstdc++.so.6', 'libgcc_s.so.1', 'libc.so.6', 'libm.so.6',
          'libpthread.so.0', 'librt.so.1', 'libdl.so.2', 'ld-linux-x86-64.so.2'}
TESTS = [
    ('component_normal', 'budget_writer/test_mock.cpp', False, 'component', 52),
    ('component_ndebug', 'budget_writer/test_mock.cpp', True, 'component', 52),
    ('ipc_normal', 'budget_writer/test_ipc_mock.cpp', False, 'ipc', 17),
    ('ipc_ndebug', 'budget_writer/test_ipc_mock.cpp', True, 'ipc', 17),
    ('independent_budget', 'review/independent_budget_writer_mock.cpp', False, 'directory', 8),
    ('independent_session', 'review/independent_session_mock.cpp', False, 'none', 12),
    ('independent_raw', 'review/independent_raw_checks_mock.cpp', False, 'directory', 5),
    ('active_kv_host', 'native/test_active_kv_host.cpp', False, 'none', 194),
]


def need(value, message):
    if not value:
        raise RuntimeError(message)


def ident(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return {'bytes': path.stat().st_size, 'sha256': h.hexdigest()}


def fresh_json(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, sort_keys=True, indent=2, allow_nan=False)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())


def inspect_source(root, relative, seen):
    need(relative in ALLOWED, 'Non-std source/include rejected: ' + relative)
    if relative in seen:
        return
    p = root / relative
    need(p.is_file() and not p.is_symlink(), 'Missing/symlink source: ' + relative)
    text = p.read_text(encoding='utf8')
    need(not re.search(r'\b(?:llama_\w+|ggml_\w+|cuda\w+|nvml_\w+|execve|execvp|execl|dlopen|system|popen)\s*\(', text),
         'Forbidden runtime/process-loader call in std-only source: ' + relative)
    seen[relative] = ident(p)
    for include in re.findall(r'^\s*#\s*include\s*"([^"]+)"', text, re.M):
        target = (p.parent / include).resolve()
        need(target.is_relative_to(root), 'Source include escapes successor')
        inspect_source(root, target.relative_to(root).as_posix(), seen)


def run(args):
    started = time.monotonic()
    root = Path(args.source_root).resolve()
    out = Path(args.out)
    need(out.is_absolute() and not out.exists(), 'Use a fresh absolute output directory; no reentry/retry')
    need(len(str(out / 'cases/ipc_ndebug/unreserved-launch/s').encode()) < 108,
         'Use a short absolute /tmp output path for private UNIX sockets')
    current = Path(out.anchor)
    for part in out.parent.parts[1:]:
        current /= part
        need(not current.is_symlink(), 'Output parent symlink rejected')
    out.mkdir(mode=0o700)
    (out / 'logs').mkdir(mode=0o700)
    (out / 'bin').mkdir(mode=0o700)
    (out / 'cases').mkdir(mode=0o700)
    receipt = {
        'schema': 'hs.N1chain.std-only-reproduction.v1', 'status': 'RUNNING',
        'scope': 'SYNTHETIC_CPU_COMPONENTS_NOT_NATIVE_QUALIFICATION',
        'model_creation': 0, 'vocabulary_only_model_creation': 0, 'backend_init': 0,
        'native_contexts': 0, 'placements': 0, 'forwards': 0,
        'real_linked_binary_executions': 0, 'native_authority': False,
        'source_files': {}, 'steps': [], 'tests': [], 'failures': [],
        'all_mock_ELFs_checked_before_first_mock_execution': False,
    }
    fresh_json(out / 'RUNNING.json', {'mode': receipt['scope'], 'native_authority': False})
    env = dict(os.environ)
    for key in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CXXFLAGS', 'LDFLAGS', 'LIBRARY_PATH',
                'CPATH', 'CPLUS_INCLUDE_PATH', 'GCC_EXEC_PREFIX', 'COMPILER_PATH'):
        env.pop(key, None)
    env['CUDA_VISIBLE_DEVICES'] = ''
    env['LC_ALL'] = 'C'

    def command(label, argv, seconds):
        left = args.total_timeout - (time.monotonic() - started)
        need(left > 0, 'Overall CPU reproduction timeout')
        stdout, stderr = out / 'logs' / (label + '.stdout'), out / 'logs' / (label + '.stderr')
        t = time.monotonic()
        with stdout.open('xb') as a, stderr.open('xb') as b:
            p = subprocess.Popen(argv, cwd=root, env=env, stdout=a, stderr=b, start_new_session=True)
            try:
                code = p.wait(timeout=min(seconds, left))
            except subprocess.TimeoutExpired:
                # Only this runner's own std-test/compiler process group exists
                # here; no native worker or unrelated process is signalled.
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait(timeout=2)
                code = -999
        step = {'id': label, 'argv': [str(v).replace(str(root), '${SOURCE}').replace(str(out), '${OUT}') for v in argv],
                'returncode': code, 'elapsed_seconds': time.monotonic() - t,
                'stdout': {'file': stdout.relative_to(out).as_posix(), **ident(stdout)},
                'stderr': {'file': stderr.relative_to(out).as_posix(), **ident(stderr)}}
        receipt['steps'].append(step)
        need(code == 0, 'Step failed; preserved without retry: ' + label)
        return stdout.read_text(encoding='utf8')

    try:
        cxx, readelf = shutil.which('g++'), shutil.which('readelf')
        need(cxx and readelf, 'Missing g++ or readelf: stop before any build/test; no installation or fallback')
        receipt['tools'] = {'g++': ident(Path(cxx).resolve()), 'readelf': ident(Path(readelf).resolve())}
        receipt['runner_source'] = ident(Path(__file__).resolve())
        for _, relative, _, _, _ in TESTS:
            inspect_source(root, relative, receipt['source_files'])
        for name, relative, ndebug, _, _ in TESTS:
            exe = out / 'bin' / name
            argv = [cxx, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror']
            if ndebug:
                argv.append('-DNDEBUG')
            command('compile_' + name, argv + [str(root / relative), '-o', str(exe)], 45)
            tags = command('readelf_' + name, [readelf, '-d', str(exe)], 10)
            libs = re.findall(r'Shared library: \[([^]]+)\]', tags)
            need(libs and set(libs) <= STDLIB, 'Non-stdlib/unknown ELF dependency before execution: ' + name)
            receipt['tests'].append({'id': name, 'ELF': ident(exe), 'needed_libraries': libs,
                                     'dependency_gate': 'STDLIB_ONLY_PASS', 'execution_status': 'NOT_RUN'})
        receipt['all_mock_ELFs_checked_before_first_mock_execution'] = True
        for (name, _, _, mode, expected), entry in zip(TESTS, receipt['tests']):
            argv = [str(out / 'bin' / name)]
            fixture = str(out / 'cases' / name)
            if mode == 'component':
                argv += ['--cpu-mock-selftest', fixture]
            elif mode == 'ipc':
                argv += ['--cpu-mock-ipc-selftest', fixture]
            elif mode == 'directory':
                argv += [fixture]
            text = command('run_' + name, argv, 45)
            lines = [v for v in text.splitlines() if v.startswith('{')]
            need(lines, 'Missing synthetic test result: ' + name)
            summary = json.loads(lines[-1])
            observed = summary.get('checks', summary.get('groups', summary.get('tests')))
            need(observed == expected and summary.get('failures', 0) == 0,
                 'Unexpected test count/result: ' + name)
            entry.update(execution_status='PASS', summary=summary)
        receipt['status'] = 'PASS'
    except Exception as e:
        receipt['status'] = 'FAILED'
        receipt['failures'].append(str(e))
    finally:
        receipt['elapsed_seconds'] = time.monotonic() - started
        receipt['partial_artifacts_preserved'] = True
        fresh_json(out / 'STATE.json', receipt)
    print(json.dumps({'status': receipt['status'], 'tests': len(receipt['tests']),
                      'native_authority': False, 'failures': receipt['failures']}))
    return 0 if receipt['status'] == 'PASS' else 2


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-root', default=str(Path(__file__).resolve().parent))
    p.add_argument('--out', required=True)
    p.add_argument('--total-timeout', type=int, default=240)
    a = p.parse_args()
    need(30 <= a.total_timeout <= 300, 'CPU reproduction must finish within30..300seconds')
    raise SystemExit(run(a))
