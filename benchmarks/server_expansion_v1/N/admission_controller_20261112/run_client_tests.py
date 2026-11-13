"""Build/run only std-only synthetic controller client tests, never native ELF."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out
    if not out.is_absolute() or out.exists() or len(str(out)) > 32:
        raise SystemExit('Fresh short absolute CPU mock output directory required')
    here = Path(__file__).resolve().parent
    parent = here.parent / 'native_chain_successor_20261112/budget_writer'
    sources = [here / 'native_client.hpp', here / 'test_client.cpp']
    sources += [parent / x for x in ['accounting_ipc.hpp', 'durable_budget.hpp',
                                    'posix.hpp', 'sha256.hpp', 'hooks.hpp']]
    for path in sources:
        value = path.read_text()
        if re.search(r'\b(?:llama_backend_init|llama_model_load|llama_init_from_model|llama_decode|dlopen|cudaSetDevice|cuInit)\s*\(', value):
            raise SystemExit('Native/loader call in std-only CPU fixture: ' + path.name)
    out.mkdir(mode=0o700)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='')
    commands = []
    start = time.monotonic()
    tests = []
    source_identities = [{'name': str(p.relative_to(here.parent)), 'bytes': p.stat().st_size,
                          'sha256': sha(p)} for p in sources]

    def run(command, name, timeout=45):
        commands.append(command)
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, env=env, timeout=timeout, check=False)
        (out / name).write_text(result.stdout)
        if result.returncode:
            raise RuntimeError('CPU mock step failed; preserve output: ' + name)
        return result.stdout

    for mode in ['normal', 'ndebug']:
        executable = out / ('client-' + mode)
        command = ['/usr/bin/g++', '-std=c++17', '-O2', '-Wall', '-Wextra']
        if mode == 'ndebug':
            command += ['-DNDEBUG']
        command += [str(here / 'test_client.cpp'), '-o', str(executable)]
        run(command, mode + '-compile.log')
        dynamic = run(['readelf', '-d', str(executable)], mode + '-readelf.log')
        needed = re.findall(r'Shared library: \[([^\]]+)\]', dynamic)
        if not needed or set(needed) - {'libstdc++.so.6', 'libgcc_s.so.1', 'libc.so.6', 'libm.so.6'}:
            raise RuntimeError('Non-stdlib dependency; no test executable will be run')
        tests.append({'mode': mode, 'executable': str(executable),
                      'sha256': sha(executable), 'bytes': executable.stat().st_size,
                      'needed_libraries': needed})
    for test in tests:
        mode = test['mode']
        text = run([test['executable'], '--cpu-only-client-test', str(out / ('cases-' + mode))],
                   mode + '-tests.log')
        summary = json.loads(text.strip().splitlines()[-1])
        if summary.get('status') != 'CPU_ONLY_CONTROLLED_CLIENT_PASS' or summary.get('groups') != 19:
            raise RuntimeError('Unexpected synthetic test count/status')
        test['summary'] = summary
        test['status'] = 'PASS'
    result = {'schema': 'hs.N1a.controlled-client.cpu-tests.v1', 'status': 'PASS',
              'scope': 'STD_ONLY_SYNTHETIC_CLIENT_TRANSPORT_NOT_NATIVE_QUALIFICATION',
              'source_files': source_identities, 'tests': tests, 'commands': commands,
              'all_mock_dependencies_checked_before_first_execution': True,
              'elapsed_s': time.monotonic() - start,
              'actual_backend_model_context_placement_forward_calls': 0,
              'native_linked_ELF_invocations': 0, 'native_authority': False}
    (out / 'RECEIPT.private.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['status', 'elapsed_s', 'native_linked_ELF_invocations', 'native_authority']}))


if __name__ == '__main__':
    main()
