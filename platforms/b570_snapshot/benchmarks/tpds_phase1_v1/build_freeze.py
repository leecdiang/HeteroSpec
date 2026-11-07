"""Small build-input closure recorder, not a compiler or remote attestation system.

The native agent imports compiler dependency output (depfiles, MSVC source-
dependencies/include logs) into a JSON report with units[{source,dependencies}].
All listed paths are explicit author-supplied inputs. No environment/key scanning.
Freeze AFTER generated files and native qualification exist, BEFORE formal timing.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from design import require, write_new

ENV_KEYS = {'PATH', 'INCLUDE', 'LIB', 'LIBPATH', 'CC', 'CXX', 'CFLAGS', 'CXXFLAGS',
            'CPPFLAGS', 'LDFLAGS', 'CUDA_PATH', 'CUDACXX', 'CMAKE_PREFIX_PATH',
            'VULKAN_SDK', 'GGML_CUDA_FORCE_MMQ', 'GGML_CUDA_FORCE_CUBLAS'}


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def file_key(path):
    return os.path.normcase(str(Path(path).resolve()))


def capture(config):
    require(config.get('schema') == 'phase1.build-inputs.v2', 'Build-input specification v2 required')
    require(config.get('phase') == 'after_native_qualification_before_formal_timing',
            'Do dependency discovery/build/qualification before performance freeze')
    require(set(config.get('build_environment', {})) <= ENV_KEYS, 'Only explicit build-relevant environment keys')
    require(isinstance(config.get('qualification_binding'),str) and config['qualification_binding'], 'Bind the native qualification receipt')
    files = config.get('files', {})
    require(files and isinstance(files, dict), 'Complete explicit build input map required')
    bound = {}
    for name, record in files.items():
        p = Path(record['path'])
        require(p.is_file() and not p.is_symlink(), 'Missing/symlink input: '+name)
        require(p.name not in ('.env', 'credentials') and p.suffix.lower() not in ('.key', '.pem'), 'Do not include secrets')
        require(record.get('role') in ('source','header','generated','build_config','response',
                'dependency_report','link_input','toolchain','runtime_module','executable','runtime_report'), 'Missing input role')
        bound[name] = dict(path=str(p.resolve()), role=record['role'], sha256=sha(p), bytes=p.stat().st_size)
    lookup = {file_key(v['path']): k for k,v in bound.items()}
    require(len(lookup) == len(bound), 'One identity per physical input path')
    # Dependency report is machine-derived by the existing build adapter, not
    # a list of five hand-picked cpp/hpp files. The original report is retained.
    report_id = config.get('dependency_report')
    require(report_id in bound and bound[report_id]['role'] == 'dependency_report', 'Compiler dependency report missing')
    report = json.loads(Path(bound[report_id]['path']).read_text(encoding='utf8'))
    require(report.get('source') in ('compiler_depfile', 'msvc_source_dependencies', 'compiler_include_trace'),
            'Use real compiler-produced dependency information')
    require(report.get('original_reports'), 'Retain original compiler dependency outputs')
    for raw in report['original_reports']:
        require(file_key(raw) in lookup, 'Raw compiler dependency output is not frozen')
    units = report.get('units', [])
    require(units, 'No translation units')
    source_paths = set()
    for unit in units:
        src = file_key(unit['source']); require(src in lookup, 'Unfrozen translation unit')
        require(src not in source_paths, 'Duplicate dependency unit'); source_paths.add(src)
        deps = unit.get('dependencies')
        require(isinstance(deps, list) and deps, 'No transitive dependencies for a compiled unit')
        for path in deps:
            require(file_key(path) in lookup, 'Unfrozen header/generated/dependency: '+str(path))
    commands = config.get('compile_commands', [])
    require(commands and {file_key(c['source']) for c in commands} == source_paths,
            'Compile commands and dependency units must cover the same sources')
    for c in commands:
        require(isinstance(c.get('argv'), list) and c['argv'] and all(isinstance(x, str) for x in c['argv']), 'Exact compiler argv required')
        require(c.get('working_directory'), 'Compiler working directory missing')
        require(c.get('compiler') in bound and bound[c['compiler']]['role'] == 'toolchain', 'Compiler bytes must be frozen')
        for arg in c['argv']:
            if arg.startswith('@'):
                key=file_key(Path(c['working_directory'])/arg[1:].strip(chr(34)))
                require(key in lookup and bound[lookup[key]]['role']=='response', 'Unfrozen @response file')
        for ref in c.get('response_files', []):
            require(ref in bound and bound[ref]['role'] == 'response', 'Response-file bytes missing')
    require(config.get('link_commands'), 'Exact link inputs/options required')
    for c in config['link_commands']:
        require(c.get('argv') and c.get('working_directory'), 'Link command missing')
        require(c.get('linker') in bound and bound[c['linker']]['role'] == 'toolchain', 'Linker identity missing')
        require(c.get('inputs') and all(x in bound for x in c['inputs']), 'Unfrozen static library/object/link input')
        for arg in c['argv']:
            if arg.startswith('@'):
                key=file_key(Path(c['working_directory'])/arg[1:].strip(chr(34)))
                require(key in lookup and bound[lookup[key]]['role']=='response', 'Unfrozen linker response file')
    for field in ('generated_files', 'build_configuration_files'):
        require(field in config and isinstance(config[field], list), 'Explicit list required: '+field)
        require(all(x in bound for x in config[field]), 'Unfrozen '+field)
    runtime_id = config.get('runtime_report')
    require(runtime_id in bound and bound[runtime_id]['role'] == 'runtime_report', 'Actual native module report missing')
    runtime = json.loads(Path(bound[runtime_id]['path']).read_text(encoding='utf8'))
    require(runtime.get('observed_after_qualification') is True and runtime.get('modules'),
            'A directory listing is not a loaded-module observation')
    for observed in runtime['modules']:
        key = file_key(observed['path'])
        require(key in lookup and bound[lookup[key]]['sha256'] == observed.get('sha256'), 'Loaded module bytes not bound')
        require(bound[lookup[key]]['role'] in ('runtime_module','executable'), 'Invalid runtime module role')
    return dict(schema='phase1.build-freeze.v2', config_sha256=hashlib.sha256(canonical(config)).hexdigest(),
                files=bound, compile_commands=commands, link_commands=config['link_commands'],
                build_environment=config.get('build_environment', {}), loaded_modules=runtime['modules'],
                qualification_binding=config.get('qualification_binding'),
                status='BUILD_INPUT_CLOSURE_RECORDED_NOT_A_NUMERICAL_PROOF')


def verify(config, frozen, observed_modules=None):
    require(capture(config) == frozen, 'Build input, generated file, options, toolchain or recorded module changed; make a new version')
    if observed_modules is not None:
        expected = {file_key(x['path']): x['sha256'] for x in frozen['loaded_modules']}
        actual = {file_key(x['path']): x['sha256'] for x in observed_modules}
        require(len(actual)==len(observed_modules) and actual == expected, 'Actual loaded modules differ from frozen qualification')
        require(all(sha(k)==h for k,h in actual.items()), 'Loaded module files changed')
    return True


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('task', choices=('freeze','verify')); p.add_argument('config',type=Path);p.add_argument('receipt',type=Path)
    p.add_argument('--observed-modules',type=Path)
    a=p.parse_args();config=json.loads(a.config.read_text())
    if a.task=='freeze': write_new(a.receipt,capture(config))
    else:
        observed=json.loads(a.observed_modules.read_text()) if a.observed_modules else None
        verify(config,json.loads(a.receipt.read_text()),observed)
    print('BUILD_INPUT_CHECK_ONLY; no GPU launched')

if __name__=='__main__':main()
