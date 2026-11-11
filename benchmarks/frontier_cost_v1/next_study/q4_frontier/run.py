"""Plan only by default; native execution requires an exact published source binding."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import time
from build import validate_dependencies
from protocol import (BUDGET, LIBRARIES, MODEL_BYTES, MODEL_SHA, NATIVE_TIMEOUT_SECONDS,
                      RAW_BYTE_LIMIT, atomic_json, cases, digest, identity, plan, source_identities)


def validate_publication(publication, current_sources):
    if not isinstance(publication, dict) or publication.get('remote_source_verified') is not True:
        raise ValueError('Root must verify the remote source commit before authorizing execution')
    if not re.fullmatch(r'[0-9a-f]{40}', publication.get('commit', '')):
        raise ValueError('Exact published source commit required')
    if publication.get('sources') != current_sources:
        raise ValueError('Published source manifest differs from exact prepared sources')


def environment(libraries):
    if os.environ.get('LD_PRELOAD') or os.environ.get('LD_AUDIT'):
        raise ValueError('LD_PRELOAD/LD_AUDIT must be absent')
    env = {k: v for k, v in os.environ.items() if not k.startswith(('GGML_', 'LLAMA_', 'HS_', 'OMP_', 'CUDA_'))
           and k not in ('LD_LIBRARY_PATH', 'LD_PRELOAD', 'LD_AUDIT')}
    env.update(LD_LIBRARY_PATH=str(libraries), OMP_NUM_THREADS='1', CUDA_VISIBLE_DEVICES='')
    return env


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    for name in ('build', 'model', 'publication', 'out'):
        parser.add_argument('--'+name, type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(plan(), indent=2, sort_keys=True));return
    if any(getattr(args, name) is None for name in ('build', 'model', 'publication', 'out')):
        parser.error('--execute requires --build --model --publication --out')
    here = Path(__file__).resolve().parent
    sources = source_identities(here)
    publication = json.loads(args.publication.read_text())
    validate_publication(publication, sources)
    build_dir, model, out = (p.resolve() for p in (args.build, args.model, args.out))
    build = json.loads((build_dir/'BUILD.json').read_text())
    if build.get('status') != 'BUILT_NOT_EXECUTED' or build.get('sources') != sources:
        raise ValueError('Build provenance or prepared source binding differs')
    paths = {k: Path(v) for k, v in build['paths'].items()}
    dependencies = validate_dependencies(paths['core'], paths['frontend'], paths['lib_dir'], paths['legacy_dir'])
    if dependencies != build['dependencies']:
        raise ValueError('Current dependencies differ from frozen build')
    binary = build_dir/'q4_frontier_probe'
    if identity(binary) != build['output'] or identity(model) != {'bytes': MODEL_BYTES, 'sha256': MODEL_SHA}:
        raise ValueError('Binary/model binding differs')
    out.mkdir(parents=True, exist_ok=False)
    report = {'schema': 'heterospec.q4-frontier-run.v1', 'status': 'ADMITTED_NOT_STARTED',
              'publication': publication, 'build': identity(build_dir/'BUILD.json'), 'binary': identity(binary),
              'model': identity(model), 'budget': BUDGET, 'performance_admitted': False, 'native_child_launches': 0,
              'resource_timeout_seconds': NATIVE_TIMEOUT_SECONDS, 'automatic_retry': False}
    save = lambda: atomic_json(out/'RUN.json', report)
    save()
    job = {'schema': 'heterospec.q4-frontier-job.v1', 'backend': 'cpu', 'threads': 1,
           'model': str(model), 'lib_dir': str(paths['lib_dir']), 'expected_native_libraries': LIBRARIES,
           'budget': BUDGET, 'raw_byte_limit': RAW_BYTE_LIMIT, 'cases': cases(),
           'source_binding': sources, 'published_source_commit': publication['commit']}
    atomic_json(out/'JOB.json', job)
    child = None
    try:
        argv = [str(binary), str(out/'JOB.json'), str(out/'native')]
        with (out/'stdout.log').open('xb') as stdout, (out/'stderr.log').open('xb') as stderr:
            # Only this one owned process can be killed; no shared workers, resets, or retry.
            start = time.monotonic()
            child = subprocess.Popen(argv, stdout=stdout, stderr=stderr, env=environment(paths['lib_dir']))
            report.update(status='RUNNING', native_child_launches=1, child_pid=child.pid, argv=argv);save()
            timed_out = False
            while child.poll() is None:
                remaining = NATIVE_TIMEOUT_SECONDS-(time.monotonic()-start)
                if remaining <= 0:
                    timed_out = True;child.kill();break
                try:
                    child.wait(timeout=min(5.0, remaining))
                except subprocess.TimeoutExpired:
                    pass
            child.wait(timeout=5)
        report.update(returncode=child.returncode, child_reaped=True, timed_out=timed_out,
                      resource_child_wall_seconds=time.monotonic()-start)
        report['logs'] = {name: identity(out/name) for name in ('stdout.log', 'stderr.log')}
        report['job'] = identity(out/'JOB.json')
        report['dependencies_unchanged'] = validate_dependencies(paths['core'], paths['frontend'], paths['lib_dir'], paths['legacy_dir']) == dependencies
        report['sources_unchanged'] = source_identities(here) == sources and identity(binary) == build['output']
        report['model_unchanged'] = identity(model) == report['model']
        if not all(report[k] for k in ('dependencies_unchanged', 'sources_unchanged', 'model_unchanged')):
            raise ValueError('Execution binding changed')
        result_path = out/'native/RESULT.json'
        if result_path.is_file():
            report['native_result'] = identity(result_path)
            report['native_status'] = json.loads(result_path.read_text()).get('status')
        report['status'] = 'TIMED_OUT_PARTIAL_RETAINED' if timed_out else 'COMPLETE_PENDING_INDEPENDENT_VERIFICATION'
        save()
        print(json.dumps({k: report.get(k) for k in ('status', 'returncode', 'timed_out', 'native_status')}, indent=2))
    except BaseException as error:
        if child is not None and child.poll() is None:
            child.kill();child.wait(timeout=5)
        report.update(status='FAILED_PARTIAL_RETAINED', error=str(error));save();raise


if __name__ == '__main__':
    main()
