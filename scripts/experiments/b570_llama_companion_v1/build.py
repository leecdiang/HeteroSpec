"""Native builds use separate directories and retain exact command/source receipts."""
from pathlib import Path
import argparse
import subprocess
import sys
from common import read, sha, write, need, utc
from source import stage, supervisor


def build(config_path, out, mode):
    c = read(config_path);out = Path(out).resolve();need(not out.exists(), 'fresh build root')
    source = stage(c['repo'], c['archive'], out / 'source', mode)
    code = Path(__file__).resolve().parent
    extension_receipt = None
    if mode == 'candidate' and c.get('extension'):
        extension = Path(c['extension']).resolve()
        need(sha(extension) == c['extension_sha256'], 'reviewed source-extension identity')
        before = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
        cmd = [sys.executable, '-B', str(extension), '--source', str(source)]
        with (out / 'extension.log').open('xb') as log:
            subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=c.get('command_timeout_seconds', 14400))
        after = {p.relative_to(source).as_posix(): sha(p) for p in source.rglob('*') if p.is_file()}
        extension_receipt = {'script_sha256': sha(extension), 'argv': cmd, 'before': before, 'after': after}
        write(out / 'SOURCE_EXTENSION.json', extension_receipt)
    commands = [[c.get('cmake', 'cmake'), '-S', str(code), '-B', str(out / 'build'),
        '-G', c.get('generator', 'Visual Studio 17 2022'), '-A', 'x64',
        '-DLLAMA_SOURCE=' + str(source), '-DHS_COMPANION_ORACLE=' + ('ON' if mode == 'oracle' else 'OFF'),
        '-DCMAKE_PREFIX_PATH=' + c['vulkan_sdk'], '-DLLAMA_BUILD_NUMBER=10839', '-DLLAMA_BUILD_COMMIT=0cae43063'],
        [c.get('cmake', 'cmake'), '--build', str(out / 'build'), '--config', 'Release', '--parallel', str(c.get('jobs', 4))]]
    write(out / 'COMMANDS.json', {'mode': mode, 'utc': utc(), 'argv': commands, 'config_sha256': sha(config_path)})
    for i, command in enumerate(commands):
        with (out / f'command-{i}.log').open('xb') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=c.get('command_timeout_seconds', 14400))
    exe = out / 'build/bin/Release/b570_llama.exe'
    need(exe.exists(), 'native executable missing')
    files = [exe] + sorted(exe.parent.glob('*.dll'))
    need(len(files) > 1, 'numerical libraries not in delivery directory')
    sup = supervisor(c['repo'], out / 'supervisor.py')
    write(out / 'BUILD.json', {'status': 'BUILT_NOT_QUALIFIED', 'mode': mode, 'source': read(out / 'source/SOURCE.json'),
          'source_extension_sha256': sha(out / 'SOURCE_EXTENSION.json') if extension_receipt else None,
          'executable': str(exe), 'files': [{'path': str(p), 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in files],
          'supervisor': str(sup), 'supervisor_sha256': sha(sup),
          'authoring_files': {p.name: sha(p) for p in code.iterdir() if p.is_file()}})
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--config', required=True);p.add_argument('--out', required=True)
    p.add_argument('--mode', required=True, choices=['oracle', 'candidate']);a = p.parse_args();print(build(a.config, a.out, a.mode))
