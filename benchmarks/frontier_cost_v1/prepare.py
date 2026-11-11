#!/usr/bin/env python3
"""Prepare an isolated, pinned numerical library and candidate frontend.

This command builds source only. It never loads a model or starts a GPU job.
CPU is the default; CUDA compilation requires an explicit backend selection.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent


def identity(path: Path) -> dict:
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--work', type=Path, required=True, help='New isolated output directory')
    p.add_argument('--archive', type=Path, help='Optional exact source ZIP already downloaded')
    p.add_argument('--backend', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--cuda-arch', default='86', help='CUDA compile architecture, not a performance claim')
    p.add_argument('--jobs', type=int, default=2)
    p.add_argument('--cmake', default=shutil.which('cmake'))
    args = p.parse_args()
    if args.jobs < 1 or args.jobs > 16 or not args.cmake:
        p.error('CMake and 1..16 build jobs are required')
    if not args.cuda_arch.isdigit():
        p.error('One explicit numeric CUDA architecture is required')
    if args.work.exists() or args.work.is_symlink():
        p.error('Use a fresh work directory; previous attempts are retained')
    if args.archive is not None and not args.archive.is_file():
        p.error('The source archive must be an existing regular file')
    work = args.work.resolve()
    work.mkdir(parents=True)
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    record = {'schema': 'heterospec.frontier-cost.prepare.v1',
              'backend_build': args.backend, 'source_edits': False,
              'model_loads': 0, 'GPU_kernel_executions': 0,
              'numerical_qualification': 'NOT_RUN', 'steps': [],
              'script': identity(Path(__file__)),
              'support': {x.name: identity(x) for x in (HERE/'support').iterdir() if x.is_file()}}
    receipt = work/'PREPARED.json'

    def save() -> None:
        receipt.write_text(json.dumps(record, indent=2)+'\n')

    def run(name: str, argv: list) -> None:
        start = time.monotonic()
        stdout = work/(name+'.stdout')
        stderr = work/(name+'.stderr')
        with stdout.open('xb') as out, stderr.open('xb') as err:
            result = subprocess.run([str(a) for a in argv], cwd=work, env=env,
                                    stdout=out, stderr=err)
        record['steps'].append({'name': name, 'argv': [str(a) for a in argv],
                                'returncode': result.returncode,
                                'wall_seconds': time.monotonic()-start,
                                'stdout': identity(stdout), 'stderr': identity(stderr)})
        save()
        if result.returncode:
            raise RuntimeError(name+' failed; original logs retained in '+str(work))

    record['status'] = 'PREPARING_SOURCE_ONLY'
    save()
    try:
        acquisition = [sys.executable, HERE/'support/acquire_sourcekit.py', '--out', work/'sourcekit']
        if args.archive is not None:
            acquisition += ['--archive', args.archive.resolve()]
        run('acquire', acquisition)
        run('frontend', [sys.executable, HERE/'support/reconstruct_m2_candidate.py',
                         '--kit', work/'sourcekit', '--out', work/'frontend'])
        core = work/'sourcekit/native/cores/loop4'
        build = work/'numerical_build'
        flags = {'GGML_CUDA': 'ON' if args.backend == 'cuda' else 'OFF',
                 'GGML_VULKAN': 'OFF', 'GGML_METAL': 'OFF', 'GGML_NATIVE': 'OFF',
                 'GGML_CCACHE': 'OFF', 'BUILD_SHARED_LIBS': 'ON',
                 'LLAMA_BUILD_TESTS': 'OFF', 'LLAMA_BUILD_TOOLS': 'OFF',
                 'LLAMA_BUILD_EXAMPLES': 'OFF', 'LLAMA_BUILD_SERVER': 'OFF',
                 'LLAMA_BUILD_COMMON': 'OFF', 'LLAMA_OPENSSL': 'OFF',
                 'LLAMA_BUILD_UI': 'OFF', 'LLAMA_SUBPROCESS': 'OFF',
                 'CMAKE_BUILD_TYPE': 'Release', 'CMAKE_EXPORT_COMPILE_COMMANDS': 'ON'}
        if args.backend == 'cuda':
            flags['CMAKE_CUDA_ARCHITECTURES'] = args.cuda_arch
        run('configure', [args.cmake, '-S', core, '-B', build]
            + ['-D'+key+'='+value for key,value in flags.items()])
        run('build', [args.cmake, '--build', build, '--target', 'llama', '-j', str(args.jobs)])
        libraries = {x.name: identity(x) for x in (build/'bin').glob('*.so*')
                     if x.is_file() and not x.is_symlink()}
        if not any(name.startswith('libllama.so') for name in libraries):
            raise RuntimeError('No built libllama shared object was produced')
        record.update(status='BUILT_NOT_QUALIFIED', core=str(core),
                      lib_dir=str(build/'bin'),
                      candidate_frontend=str(work/'frontend/candidate_frontend'),
                      numerical_libraries=libraries,
                      acquisition=identity(work/'sourcekit/ACQUISITION.json'),
                      reconstruction=identity(work/'frontend/RECONSTRUCTION.json'))
        save()
    except Exception as exc:
        record.update(status='FAILED_SOURCE_OR_BUILD', error=str(exc))
        save()
        raise
    print(json.dumps({k: record[k] for k in ('status','core','lib_dir','candidate_frontend',
                                            'backend_build','model_loads','numerical_qualification')}, indent=2))


if __name__ == '__main__':
    main()
