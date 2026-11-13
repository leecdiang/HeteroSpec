"""Build four variants of the unchanged original M2 entry; run no executable."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
from protocol import ENTRY_SHA, HELPER_SHA, WORKER_SHA, digest, identity, write_new

SOURCE_MANIFEST_SHA = '8d37214bb699565c535b52d3fd4439786f3e45c2d40a1aaff6db948c27366a1f'
RECONSTRUCTION_SHA = '0ad149d7441b5d8027dd45c0cfdb2098a12e5a158f6969239b873b754e317198'
WRAPS = ['llama_model_load_from_file', 'llama_init_from_model', 'llama_memory_clear',
         'llama_memory_seq_rm', 'llama_free']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--core', type=Path, required=True)
    parser.add_argument('--frontend', type=Path, required=True)
    parser.add_argument('--lib-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    core, frontend, libs, out = (path.resolve() for path in (args.core, args.frontend, args.lib_dir, args.out))
    out.mkdir(exist_ok=False, parents=True)
    report = {'schema': 'heterospec.original-entry-build.v1', 'status': 'STARTED',
              'model_loads': 0, 'executable_runs': 0, 'GPU_executions': 0,
              'performance_admitted': False, 'stages': []}
    def save():
        temporary = out / 'BUILD.json.tmp'
        temporary.write_text(json.dumps(report, indent=2) + '\n')
        temporary.replace(out / 'BUILD.json')
    save()
    try:
        for name, expected in [('entry.cpp', ENTRY_SHA), ('worker.cpp', WORKER_SHA), ('lazy_draft_tail.hpp', HELPER_SHA)]:
            if digest(frontend / name) != expected:
                raise ValueError('Original frontend identity differs: ' + name)
        reconstruction = frontend.parent / 'RECONSTRUCTION.json'
        if digest(reconstruction) != RECONSTRUCTION_SHA:
            raise ValueError('Reconstructed frontend provenance differs')
        members = json.loads(reconstruction.read_text())['candidate_frontend']
        if {p.name for p in frontend.iterdir()} != set(members):
            raise ValueError('Unexpected frontend member set')
        for name, expected in members.items():
            if digest(frontend / name) != expected:
                raise ValueError('Frontend member changed: ' + name)
        manifest_path = core.parents[2] / 'SOURCE_ASSET_MANIFEST.json'
        if digest(manifest_path) != SOURCE_MANIFEST_SHA:
            raise ValueError('Numerical source manifest differs')
        source_manifest = json.loads(manifest_path.read_text())
        prefix = 'native/cores/loop4/'
        expected = {p[len(prefix):]: value for p, value in source_manifest['files'].items() if p.startswith(prefix)}
        actual = {str(p.relative_to(core)): p for p in core.rglob('*') if p.is_file()}
        if set(actual) != set(expected):
            raise ValueError('Numerical source member set changed')
        for name, path in actual.items():
            if path.is_symlink() or identity(path) != {'bytes': expected[name]['bytes'], 'sha256': expected[name]['sha256']}:
                raise ValueError('Numerical source bytes changed: ' + name)
        numerical = {str(p.resolve()): identity(p) for p in libs.glob('lib*.so*')
                     if p.is_file() and p.name.startswith(('libllama', 'libggml'))}
        if not all((libs / name).is_file() for name in ['libllama.so', 'libggml.so', 'libggml-base.so', 'libggml-cpu.so']):
            raise ValueError('Required original numerical libraries absent')
        source = Path(__file__).with_name('request_audit.cpp').resolve()
        report.update(frontend={name: identity(frontend / name) for name in members},
                      numerical_source_members=len(actual), numerical_source_manifest_sha256=SOURCE_MANIFEST_SHA,
                      numerical_libraries=numerical, audit_source=identity(source), build_source=identity(__file__),
                      core=str(core), frontend_path=str(frontend), lib_dir=str(libs), wrap_symbols=WRAPS)
        includes = [frontend, core/'include', core/'src', core/'ggml/include', core/'vendor']
        common = [shutil.which('g++'), '-std=c++17', '-O2', '-DPHASE_CANDIDATE=1']
        common += [arg for path in includes for arg in ['-I', str(path)]]
        link = [str(out/'sha256.o'), '-L', str(libs), '-Wl,-rpath,'+str(libs),
                '-lllama', '-lggml', '-lggml-base', '-lggml-cpu', '-pthread', '-ldl']
        commands = [[shutil.which('gcc'), '-O2', '-I', str(core/'vendor/hash'), '-c',
                     str(core/'vendor/hash/sha256/sha256.c'), '-o', str(out/'sha256.o')]]
        for capture in (False, True):
            for mode in (0, 1):
                name = ('capture_' if capture else 'clean_') + str(mode)
                command = common + [f'-DHETEROSPEC_DEFER_DRAFT_TAIL={mode}', str(frontend/'entry.cpp')]
                if capture:
                    command += [str(source)] + ['-Wl,--wrap=' + symbol for symbol in WRAPS]
                commands.append(command + link + ['-o', str(out/name)])
        for index, command in enumerate(commands):
            process = subprocess.run(command, capture_output=True)
            for suffix, data in [('.stdout', process.stdout), ('.stderr', process.stderr)]:
                (out/(str(index)+suffix)).write_bytes(data)
            report['stages'].append({'argv': command, 'returncode': process.returncode,
                                     'stdout': identity(out/(str(index)+'.stdout')),
                                     'stderr': identity(out/(str(index)+'.stderr'))})
            save()
            if process.returncode:
                raise RuntimeError('Compilation failed; retained stage ' + str(index))
        if numerical != {path: identity(path) for path in numerical} or identity(source) != report['audit_source']:
            raise ValueError('Build inputs changed')
        report['outputs'] = {name: identity(out/name) for name in ['clean_0', 'clean_1', 'capture_0', 'capture_1']}
        report['status'] = 'BUILT_NOT_EXECUTED_NOT_QUALIFIED'
        save()
        print(json.dumps({'status': report['status'], 'outputs': report['outputs'], 'model_loads': 0}, indent=2))
    except Exception as error:
        report.update(status='FAILED', error=str(error)); save(); raise


if __name__ == '__main__':
    main()
