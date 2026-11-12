"""Std-only bounded supervisor tests; no native ELF is executed."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() or not a.out.is_absolute() or len(str(a.out)) > 40:
        raise SystemExit('Fresh short absolute CPU fixture output directory required')
    here = Path(__file__).resolve().parent
    sources = [here / x for x in ['bounded_launcher.hpp', 'native_client.hpp',
                                  'bounded_native_launcher.cpp', 'test_launcher.cpp']]
    a.out.mkdir(mode=0o700)
    begin = time.monotonic()
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    steps = []

    def run(command, name, timeout=30):
        steps.append(command)
        r = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           text=True, env=env, timeout=timeout, check=False)
        (a.out / name).write_text(r.stdout)
        if r.returncode:
            raise RuntimeError('CPU supervisor step failed; retain all output: ' + name)
        return r.stdout

    tests = []
    for mode in ['normal', 'ndebug']:
        exe = a.out / ('mock-' + mode)
        command = ['/usr/bin/g++', '-std=c++17', '-O2', '-Wall', '-Wextra']
        if mode == 'ndebug':
            command += ['-DNDEBUG']
        command += [str(here / 'test_launcher.cpp'), '-o', str(exe)]
        run(command, mode + '-compile.log')
        dynamic = run(['readelf', '-d', str(exe)], mode + '-readelf.log')
        needed = re.findall(r'Shared library: \[([^\]]+)\]', dynamic)
        if not needed or set(needed) - {'libstdc++.so.6', 'libgcc_s.so.1', 'libc.so.6', 'libm.so.6'}:
            raise RuntimeError('Mock dependency precheck failed; do not run any mock')
        tests.append({'mode': mode, 'executable': str(exe), 'sha256': digest(exe),
                      'bytes': exe.stat().st_size, 'needed_libraries': needed})
    # Compile the closed real entry separately. Inspect only, NEVER run it.
    wrapper = a.out / 'native-launcher-not-admitted'
    run(['/usr/bin/g++', '-std=c++17', '-O0', '-g', '-fno-inline', '-fno-lto',
         str(here / 'bounded_native_launcher.cpp'), '-o', str(wrapper)], 'wrapper-compile.log')
    run(['readelf', '-d', str(wrapper)], 'wrapper-readelf.log')
    nm = run(['nm', '-C', str(wrapper)], 'wrapper-symbols.log')
    for symbol in ['native_controller_launch_entry', 'guarded_native_launch', 'execve', 'timerfd_settime']:
        if symbol not in nm:
            raise RuntimeError('Closed launcher actual body symbol absent: ' + symbol)
    for test in tests:
        text = run([test['executable'], '--cpu-only-launcher-test',
                    str(a.out / ('cases-' + test['mode']))], test['mode'] + '-tests.log')
        result = json.loads(text.strip().splitlines()[-1])
        if result.get('status') != 'CPU_ONLY_BOUNDED_LAUNCHER_PASS' or result.get('groups') != 18:
            raise RuntimeError('Unexpected bounded CPU fixture count/status')
        test['result'] = result
        test['status'] = 'PASS'
    receipt = {'schema': 'hs.N1a.bounded-launcher.cpu-tests.v1', 'status': 'PASS',
               'scope': 'FIXED_STD_ONLY_CPU_CHILDREN_NOT_NATIVE_GPU_QUALIFICATION',
               'source_files': [{'file': x.name, 'bytes': x.stat().st_size,
                                 'sha256': digest(x)} for x in sources],
               'tests': tests, 'commands': steps,
               'closed_launcher': {'bytes': wrapper.stat().st_size,
                                   'sha256': digest(wrapper), 'executed': False,
                                   'CLI': 'NOT_ADMITTED_NO_PRODUCTION_JOB_PARSER'},
               'all_mock_dependencies_checked_before_first_mock_execution': True,
               'elapsed_s': time.monotonic() - begin,
               'actual_backend_model_context_placement_forward_calls': 0,
               'native_executables_started': 0, 'native_authority': False,
               'device_quiescence_at_watchdog': 'NOT_RUN_REQUIRES_NATIVE_VALIDATION',
               'native_controller_CLI_supervisor_glue': 'BLOCKED_PENDING_SEPARATE_REVIEW'}
    (a.out / 'RECEIPT.private.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': 'PASS', 'elapsed_s': receipt['elapsed_s'],
                      'mock_groups': 36, 'native_executables_started': 0}))


if __name__ == '__main__':
    main()
