"""Compile/link source-bound controller worker; NEVER execute a native ELF."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from make_worker_descendant import derive

PINNED_BUILDER_SHA256 = '0568bcef13ded6da8b58f900428b17fa62145a7d5f1cf7877e031c45c1615c2b'


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--producer-build', type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    pinned = here.parent / 'native_chain_successor_20261112'
    if args.out.exists():
        raise SystemExit('Fresh output required; every failed epoch is retained')
    source_manifest = json.loads((pinned / 'BUILD_EVIDENCE/COMPILE_INPUTS.json').read_text())
    for item in source_manifest['inputs']:
        path = pinned / item['file']
        if path.stat().st_size != item['bytes'] or digest(path) != item['sha256']:
            raise SystemExit('PR228 original compile input mismatch: ' + item['file'])
    original = (pinned / 'build_native.py').read_bytes()
    if hashlib.sha256(original).hexdigest() != PINNED_BUILDER_SHA256:
        raise SystemExit('Complete original builder identity mismatch')
    worker, worker_receipt = derive(pinned / 'native/worker.cpp')
    driver = args.out.parent / (args.out.name + '-driver')
    driver.mkdir(parents=True)  # existence is an error, never reuse a driver epoch
    generated_worker = driver / 'worker.cpp'
    generated_worker.write_bytes(worker)
    (driver / 'WORKER_DERIVATION.json').write_text(json.dumps(worker_receipt, indent=2) + '\n')
    text = original.decode('utf-8')
    substitutions = [
        ('root=a.host_root.resolve();here=Path(__file__).resolve().parent;binding=json.loads(a.bindings.read_text())',
         'root=a.host_root.resolve();here=Path(' + repr(str(pinned)) + ');controlled=Path(' + repr(str(here)) + ');descendant_worker=Path(' + repr(str(generated_worker)) + ');binding=json.loads(a.bindings.read_text())'),
        ("here/'native',a.out]", "here/'native',controlled,a.out]"),
        ("obj=out/(name+'.o');run([compiler]+flags+['-c',str(here/'native'/(''+name+'.cpp')),'-o',str(obj)],role+'-'+name+'-compile.log');objects.append(obj)",
         "obj=out/(name+'.o');source=descendant_worker if name=='worker' else here/'native'/(''+name+'.cpp');run([compiler]+flags+['-c',str(source),'-o',str(obj)],role+'-'+name+'-compile.log');objects.append(obj)"),
        ("'prepare_native_worker','NativeProducer::advance'):",
         "'prepare_native_worker','NativeProducer::advance','ControlledNativeClient','controller_io'):")
    ]
    for old, new in substitutions:
        if text.count(old) != 1:
            raise SystemExit('Exact original builder derivation site changed')
        text = text.replace(old, new)
    program = driver / 'compile_link_driver.py'
    program.write_text(text)
    command = [sys.executable, '-B', str(program), '--host-root', str(args.host_root),
               '--out', str(args.out), '--bindings', str(pinned / 'ORIGINAL_BUILD_BINDINGS.json'),
               '--producer-build', str(args.producer_build)]
    env = os.environ.copy()
    env['CUDA_VISIBLE_DEVICES'] = ''
    with (driver / 'COMPILER_STDOUT_STDERR.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                env=env, timeout=600, check=False)
    if result.returncode:
        raise SystemExit('Compilation/link failed; retained complete driver and logs: ' + str(driver))
    receipt = json.loads((args.out / 'BUILD.private.json').read_text())
    receipt['controller_descendant'] = {
        'original_PR228_source_inputs_verified': len(source_manifest['inputs']),
        'original_builder_sha256': PINNED_BUILDER_SHA256,
        'generated_driver_sha256': digest(program),
        'worker_derivation': worker_receipt,
        'controller_client': {'bytes': (here / 'native_client.hpp').stat().st_size,
                              'sha256': digest(here / 'native_client.hpp')},
        'native_production_gate': 'UNCHANGED_PERMANENT_DENIAL',
        'native_executable_invocations': 0,
        'GPU_execution_authorized': False,
        'scope': 'Compile/link and static readers only; no loader, backend or model selftest'
    }
    (args.out / 'CONTROLLER_BUILD.private.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'status': receipt['status'],
                      'roles': [x['role'] for x in receipt['artifacts']],
                      'elapsed_s': receipt['elapsed_s'],
                      'native_executables_started': 0,
                      'GPU_execution_authorized': False}))


if __name__ == '__main__':
    main()
