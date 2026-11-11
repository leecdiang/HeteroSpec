"""Verify pinned source and CPU libraries, compile the diagnostic, run no model."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from protocol import (LEGACY_SHA, LIBRARIES, RECONSTRUCTION_SHA, SOURCE_MANIFEST_SHA,
                      atomic_json, digest, identity, source_identities)


def validate_dependencies(core, frontend, libraries, legacy):
    if digest(legacy/'matched_cost_probe.cpp') != LEGACY_SHA:
        raise ValueError('Pinned imported probe differs')
    reconstruction = frontend.parent/'RECONSTRUCTION.json'
    if digest(reconstruction) != RECONSTRUCTION_SHA:
        raise ValueError('Frontend reconstruction identity differs')
    members = json.loads(reconstruction.read_text())['candidate_frontend']
    if {p.name for p in frontend.iterdir()} != set(members):
        raise ValueError('Frontend member set differs')
    for name, expected in members.items():
        if digest(frontend/name) != expected:
            raise ValueError('Frontend source differs: '+name)
    manifest_path = core.parents[2]/'SOURCE_ASSET_MANIFEST.json'
    if digest(manifest_path) != SOURCE_MANIFEST_SHA:
        raise ValueError('Numerical source manifest differs')
    prefix = 'native/cores/loop4/'
    expected = {p[len(prefix):]: value for p, value in json.loads(manifest_path.read_text())['files'].items()
                if p.startswith(prefix)}
    actual = {str(p.relative_to(core)): p for p in core.rglob('*') if p.is_file()}
    if set(actual) != set(expected):
        raise ValueError('Numerical source member set differs')
    for name, path in actual.items():
        if path.is_symlink() or identity(path) != {k: expected[name][k] for k in ('bytes', 'sha256')}:
            raise ValueError('Numerical source changed: '+name)
    actual_libraries = {p.resolve().name: digest(p) for p in libraries.glob('lib*.so*')
                        if p.is_file() and p.name.startswith(('libllama', 'libggml'))}
    if actual_libraries != LIBRARIES:
        raise ValueError('CPU numerical library member set or bytes differ')
    return {'legacy_probe': identity(legacy/'matched_cost_probe.cpp'), 'numerical_source_members': len(actual),
            'numerical_source_manifest_sha256': SOURCE_MANIFEST_SHA,
            'frontend': {name: identity(frontend/name) for name in members}, 'libraries': actual_libraries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('core', 'frontend', 'lib-dir', 'legacy-dir', 'out'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    core, frontend, libraries, legacy, out = [p.resolve() for p in
        (args.core, args.frontend, args.lib_dir, args.legacy_dir, args.out)]
    out.mkdir(parents=True, exist_ok=False)
    here = Path(__file__).resolve().parent
    report = {'schema': 'heterospec.q4-frontier-build.v1', 'status': 'STARTED', 'model_loads': 0,
              'native_executable_runs': 0, 'performance_admitted': False, 'stages': []}
    save = lambda: atomic_json(out/'BUILD.json', report)
    save()
    try:
        report['dependencies'] = validate_dependencies(core, frontend, libraries, legacy)
        report['sources'] = source_identities(here)
        report['paths'] = {'core': str(core), 'frontend': str(frontend), 'lib_dir': str(libraries), 'legacy_dir': str(legacy)}
        includes = [frontend, core/'include', core/'src', core/'ggml/include', core/'vendor', legacy]
        commands = [
            [shutil.which('gcc'), '-O2', '-I', str(core/'vendor/hash'), '-c', str(core/'vendor/hash/sha256/sha256.c'), '-o', str(out/'sha256.o')],
            [shutil.which('g++'), '-std=c++17', '-O2', '-Wall', '-Wextra'] +
            [a for p in includes for a in ('-I', str(p))] +
            [str(here/'frontier_probe.cpp'), str(out/'sha256.o'), '-L', str(libraries), '-Wl,-rpath,'+str(libraries),
             '-lllama', '-lggml', '-lggml-base', '-lggml-cpu', '-pthread', '-ldl', '-o', str(out/'q4_frontier_probe')],
        ]
        for index, command in enumerate(commands):
            process = subprocess.run(command, capture_output=True, timeout=120)
            for suffix, data in (('stdout', process.stdout), ('stderr', process.stderr)):
                (out/f'{index}.{suffix}').write_bytes(data)
            report['stages'].append({'argv': command, 'returncode': process.returncode,
                'stdout': identity(out/f'{index}.stdout'), 'stderr': identity(out/f'{index}.stderr')})
            save()
            if process.returncode:
                raise RuntimeError('Compilation failed; failed stage retained')
        link = subprocess.run(['ldd', str(out/'q4_frontier_probe')], capture_output=True, text=True, timeout=10)
        (out/'ldd.txt').write_text(link.stdout+link.stderr)
        if link.returncode or 'not found' in link.stdout:
            raise RuntimeError('Link check failed')
        for name in LIBRARIES:
            stem = name.split('.so')[0]+'.so'
            lines = [line for line in link.stdout.splitlines() if line.strip().startswith(stem)]
            if len(lines) != 1 or str(libraries)+'/' not in lines[0]:
                raise ValueError('Numerical library does not resolve to pinned directory: '+name)
        if report['dependencies'] != validate_dependencies(core, frontend, libraries, legacy):
            raise ValueError('Build dependencies changed during compilation')
        if report['sources'] != source_identities(here):
            raise ValueError('Diagnostic sources changed during compilation')
        report['output'] = identity(out/'q4_frontier_probe')
        report['link_check'] = identity(out/'ldd.txt')
        report['status'] = 'BUILT_NOT_EXECUTED'
        save()
        print(json.dumps({k: report[k] for k in ('status', 'model_loads', 'native_executable_runs', 'output')}, indent=2))
    except Exception as error:
        report.update(status='FAILED', error=str(error));save();raise


if __name__ == '__main__':
    main()
