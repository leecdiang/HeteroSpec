"""Build the operator helper using the authenticated native build toolchain."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import time


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--native-build', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(exist_ok=False)
    binary = a.out / 'bin'
    binary.mkdir()
    source = Path(__file__).with_name('attention_replay.cpp').resolve()
    shutil.copyfile(source, a.out / source.name)
    source = a.out / source.name
    b = json.loads((a.native_build / 'BUILD.json').read_text())
    assert b['status'] == 'BUILT_NOT_QUALIFIED'
    commands = {x['label']: x['argv'] for x in b['commands']}
    obj, exe = a.out / 'attention.obj', binary / 'attention-replay.exe'
    compile_cmd = [str(source) if str(x).replace('\\', '/').endswith('/worker.cpp') else
                   str(obj) if str(x).replace('\\', '/').endswith('/worker.obj') else x
                   for x in commands['worker']]
    link_cmd = [str(obj) if str(x).replace('\\', '/').endswith('/worker.obj') else
                str(exe) if str(x).endswith('rtx-scope-transfer.exe') else x
                for x in commands['link']]
    assert str(source) in compile_cmd and str(obj) in compile_cmd
    assert str(obj) in link_cmd and str(exe) in link_cmd
    receipt = {'status': 'BUILDING', 'source': str(source.resolve()), 'source_sha256': sha(source),
               'native_build_receipt_sha256': sha(a.native_build / 'BUILD.json'),
               'numerical_modules': b['numerical_modules'], 'commands': [], 'model_requests': 0}
    def save():
        (a.out / 'BUILD.json').write_text(json.dumps(receipt, indent=2))
    save()
    for name, cmd in [('compile', compile_cmd), ('link', link_cmd)]:
        started = time.monotonic()
        with (a.out / (name + '.log')).open('xb') as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=600)
        receipt['commands'].append({'argv': cmd, 'exit_code': r.returncode, 'seconds': time.monotonic()-started})
        save()
        r.check_returncode()
    for name, h in b['numerical_modules'].items():
        original = a.native_build / 'bin' / name
        assert sha(original) == h
        shutil.copyfile(original, binary / name)
        assert sha(binary / name) == h
    receipt.update(status='BUILT_NOT_REPLAY_VALIDATED', executable=str(exe.resolve()), executable_sha256=sha(exe))
    save()
    print(receipt['status'])


if __name__ == '__main__':
    main()
