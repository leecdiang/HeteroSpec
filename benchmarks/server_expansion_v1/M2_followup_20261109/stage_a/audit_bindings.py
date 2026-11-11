"""Reconstruct generated text and hash ELF files; no build or native execution."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, shutil

PR210_ZERO_GPU_AUDIT = True


def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(4 * 1024**2), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(p.read_text())


def inventory(p):
    return {str(x.relative_to(p)): sha(x) for x in sorted(p.rglob('*')) if x.is_file()}


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument('--root', type=Path, required=True)
    cli.add_argument('--expected-source', type=Path, required=True)
    cli.add_argument('--out', type=Path, required=True)
    a = cli.parse_args()
    r, out = a.root.resolve(), a.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    native = r / 'm2-native-source-01'
    frozen = read(r / 'm2-run-03/SOURCE_FREEZE.json')
    assert sha(r / 'm2-native-source-01.tar.gz') == frozen['native_source_tar_sha256']
    source = read(a.expected_source)
    for name, digest in source.items():
        assert sha(native / name) == digest, name
    lock = read(r / 'run-01/stage-04/SOURCE_LOCK.json')
    template = r / 'run-01/stage-04/frontend'
    assert inventory(template) == lock['frontend']
    generated = out / 'regenerated-frontend'
    shutil.copytree(template, generated)
    spec = importlib.util.spec_from_file_location('pinned_transform', native / 'transform.py')
    transform = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transform)
    transform.transform(generated)
    shutil.copy2(native / 'native/tapes.hpp', generated / 'm2_tapes.hpp')
    shutil.copy2(native / 'native/capability.hpp', generated / 'm1_capability.hpp')
    p = generated / 'entry.cpp'
    s = p.read_text()
    needle = 'static json module_inventory()'
    assert s.count(needle) == 1
    s = s.replace(needle, '#include "m1_capability.hpp"\n' + needle, 1)
    needle = '        phase1_profiling=job.value("profile",false);'
    assert s.count(needle) == 1
    s = s.replace(needle, '        m1_capability(job,pool,t,d,spec,root,result);\n' + needle, 1)
    p.write_text(s)
    actual = inventory(r / 'm2-build-01/frontend')
    assert inventory(generated) == actual == read(r / 'm2-build-01/BUILD_COMPLETE.json')['frontend']
    binaries = {}
    for role in ('loop4', 'packed', 'reference'):
        directory = r / 'm2-build-01' / role if role != 'reference' else r / 'run-01/build-R-01'
        b = read(directory / 'BUILD.json')
        exe = Path(b['executable'])
        assert exe.open('rb').read(4) == b'\x7fELF'
        assert sha(exe) == b['executable_sha256']
        if role != 'reference':
            assert b['frontend'] == actual
        binaries[role] = dict(executable_sha256=b['executable_sha256'], build_receipt_sha256=sha(directory / 'BUILD.json'), ELF=True)
    checked = read(r / 'm2-run-03/panel-01/CHECKED.json')
    modules = {}
    current_module_files = {}
    for role in ('loop4', 'packed'):
        worker = next(x for x in checked if x['core'] == role)
        p = r / 'm2-run-03/panel-01/runs' / worker['id'] / 'LOADED_MODULES.json'
        assert sha(p) == worker['loaded_modules_sha256']
        modules[role] = dict(saved_module_map_sha256=sha(p), ELF_file_hashes={Path(k).name:v['sha256'] for k,v in read(p).items() if v['kind']=='ELF_file'})
        for name, entry in read(p).items():
            if entry['kind'] != 'ELF_file':
                continue
            if name not in current_module_files:
                current_module_files[name] = sha(Path(name))
            assert current_module_files[name] == entry['sha256'], name
    models = read(r / 'run-01/inputs-01/MODELS.json')['Qwen']
    model_binding = {role:dict(sha256=models[role+'_sha256'], bytes=Path(models[role+'_model']).stat().st_size,
                              identity='Saved full model-hash binding from native runs; payload not rehashed by this static audit') for role in ('target', 'draft')}
    value = dict(passed=True, source_protocol_head='3268a63dcbde99d5d9f8dd461f34d56e9840d3a0',
        M2_native_source='61bcce0552b1a80e9345fa199238ebb7bc63e6ff', M2_driver_source='ae287bce170f3af2c998bf9b2892703ff2257685',
        source_input_hashes=source, generated_files=actual, generated_text_reconstruction_exact=True,
        binaries=binaries, saved_loaded_module_maps=modules, models=model_binding,
        current_module_file_hashes_match_saved_maps=True, unique_current_ELF_module_files=len(current_module_files),
        reference_freeze_sha256=sha(r/'run-01/reference-01/REFERENCE_FREEZE.json'),
        compilation_performed=False, binary_executed=False, CUDA_initialized=False, new_native_requests=0,
        scope='Exact generated-source reproduction and current ELF-byte identities; historical module/model bindings. Not a post-reboot numerical qualification.')
    (out/'BINDINGS_CHECKED.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(passed=True,generated_files=len(actual),ELF_binaries=len(binaries),new_native_requests=0)),flush=True)


if __name__ == '__main__':
    main()
