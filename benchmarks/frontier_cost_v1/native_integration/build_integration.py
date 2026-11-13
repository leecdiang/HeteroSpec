"""Build the unchanged frontend's request function inside a separate CPU harness."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

WORKER_SHA = '05e395aa3082b08229946139c1f0d298bfc1c3064f001ba5c10aefcc9487eecb'
HELPER_SHA = '8602ac1e2ad93972d36ff8fc3f7dca5e16c0a8385ac058bd1b367331f6c2f62f'


def identity(path):
    p = Path(path).resolve()
    data = p.read_bytes()
    return {'name': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--core', '--source', dest='source', type=Path, required=True)
    p.add_argument('--frontend', type=Path, required=True)
    p.add_argument('--lib-dir', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.source = a.source.resolve(); a.frontend = a.frontend.resolve(); a.lib_dir = a.lib_dir.resolve()
    a.out = a.out.resolve(); a.out.mkdir(exist_ok=False)
    result = {'schema': 'heterospec.cpu-integration-build.v1', 'status': 'STARTED', 'stages': []}
    receipt = a.out/'BUILD.json'
    def save(): receipt.write_text(json.dumps(result, indent=2)+'\n')
    save()
    try:
        if identity(a.frontend/'worker.cpp')['sha256'] != WORKER_SHA:
            raise ValueError('Unknown candidate worker bytes')
        if identity(a.frontend/'lazy_draft_tail.hpp')['sha256'] != HELPER_SHA:
            raise ValueError('Unknown helper bytes')
        result['frontend'] = {x.name: identity(x) for x in a.frontend.iterdir() if x.is_file()}
        result['harness'] = identity(Path(__file__).with_name('cpu_request_driver.cpp'))
        result['libraries_before'] = {n: identity(a.lib_dir/n) for n in ['libllama.so','libggml.so','libggml-base.so','libggml-cpu.so']}
        includes = [a.frontend, a.source/'include', a.source/'src', a.source/'ggml/include', a.source/'vendor']
        common = [shutil.which('g++'), '-std=c++17', '-O2', '-DPHASE_CANDIDATE=1']
        common += [v for x in includes for v in ['-I', str(x)]]
        libs = [str(a.out/'sha256.o'), '-L', str(a.lib_dir), '-Wl,-rpath,'+str(a.lib_dir),
                '-lllama', '-lggml', '-lggml-base', '-lggml-cpu', '-pthread', '-ldl']
        commands = [[shutil.which('gcc'), '-O2', '-I', str(a.source/'vendor/hash'), '-c',
                     str(a.source/'vendor/hash/sha256/sha256.c'), '-o', str(a.out/'sha256.o')]]
        for mode in (0,1):
            commands.append(common+[f'-DHETEROSPEC_DEFER_DRAFT_TAIL={mode}',
                str(Path(__file__).with_name('cpu_request_driver.cpp'))]+libs+['-o',str(a.out/f'cpu_request_{mode}')])
        commands.append(common+['-DHETEROSPEC_DEFER_DRAFT_TAIL=1',str(a.frontend/'entry.cpp')]+libs+['-o',str(a.out/'guarded_entry')])
        commands.append(common+['-DHETEROSPEC_DEFER_DRAFT_TAIL=0',str(a.frontend/'entry.cpp')]+libs+['-o',str(a.out/'guarded_entry_eager')])
        for n, command in enumerate(commands):
            proc = subprocess.run(command, capture_output=True)
            stdout = a.out/f'{n}.stdout'; stderr = a.out/f'{n}.stderr'
            stdout.write_bytes(proc.stdout); stderr.write_bytes(proc.stderr)
            result['stages'].append({'argv': command, 'returncode': proc.returncode,
                'stdout': identity(stdout), 'stderr': identity(stderr)})
            save()
            if proc.returncode:
                raise RuntimeError(f'Build step {n} failed; see retained stderr')
        result['libraries_after'] = {n: identity(a.lib_dir/n) for n in result['libraries_before']}
        if result['libraries_before'] != result['libraries_after']:
            raise RuntimeError('Library bytes changed while building')
        result['harness_after'] = identity(Path(__file__).with_name('cpu_request_driver.cpp'))
        if result['harness_after'] != result['harness']:
            raise RuntimeError('Harness bytes changed while building')
        if result['frontend'] != {x.name: identity(x) for x in a.frontend.iterdir() if x.is_file()}:
            raise RuntimeError('Frontend bytes changed while building')
        result['outputs'] = {n: identity(a.out/n) for n in ['cpu_request_0','cpu_request_1','guarded_entry','guarded_entry_eager']}
        result['status'] = 'BUILT_NOT_EXECUTED'; save()
        print(json.dumps({'status':result['status'],'receipt':str(receipt)}))
    except Exception as exc:
        result['status'] = 'FAILED'; result['error'] = str(exc); save(); raise


if __name__ == '__main__':
    main()
