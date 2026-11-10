"""New scheduling epoch: CPU-only validation of the unchanged B2 native code.

Never calls a model or imports a legacy main. All 32 saved numerical cells are
recomputed, in addition to the complete original capture/dependency hashes.
The old expired waiter and its execution function are never used.
"""
import argparse
import datetime as dt
import difflib
import importlib.util
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace


def need(value, message):
    if not value:
        raise RuntimeError(message)


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(root, work, main_admission, original_source):
    need(sys.flags.optimize == 0, 'Original numerical checker requires assertions enabled')
    started = time.monotonic()
    old = load_module('_unchanged_B2_prepare', original_source)
    need(old.sha(original_source) == '389e25bc972f6ae5041f271de0ebabcf1975d9f68c17ad4094c199bab1322c1d',
         'Original B2 preparation source identity')
    admission = old.read(main_admission)
    need(admission['GPU_authorized'] is True and admission['execution_phase'] == 'S1',
         'Current allocation authority missing')
    # This function only reads files and creates CPU metadata. No old execute,
    # waiter, allocation deadline, or old activation is inherited.
    old.prepare(SimpleNamespace(root=root, work=work))
    plan = old.read(work/'PLAN.json')
    need(len(plan['reuse']['heavy_capture_commitments']) == 352, 'All 352 candidate qualification payloads required')
    # The historical archive has1728 binary payloads in total;352 belong to
    # the32 candidate cells. Recheck the entire archive, including its R data,
    # rather than repeating the historical ambiguous capture-count label.
    archive_files = old.read(root/'pr210-stage-b-export-03/BINARY_CAPTURE_INDEX.json')['files']
    need(len(archive_files) == 1728, 'Complete original binary archive index')
    for item in archive_files:
        relative = Path(item['path'])
        need(not relative.is_absolute() and '..' not in relative.parts, 'Safe original archive path')
        path = root/relative
        need(path.stat().st_size == item['bytes'] and old.sha(path) == item['sha256'],
             'Original binary archive payload missing or changed')
    native_source = root/'pr210-stage-b-source-05/run.py'
    need(old.sha(native_source) == plan['reuse']['original_checker_source_sha256'], 'Original B checker source changed')
    b = root/'pr210-stage-b-20261109-05'
    sys.path.insert(0, str(b/'runtime'))
    checks = load_module('_unchanged_B_numeric_checks', b/'runtime/native_checks.py')
    frozen_source = Path(next(p for p in admission['source_files'] if p.endswith('/readers_legacy/active_kv.py'))).parent.parent
    sys.path.insert(0, str(frozen_source))
    from readers_legacy.active_kv import parse
    import numpy as np
    module = load_module('_unchanged_B32_checker', native_source)
    checker = module.Runner.__new__(module.Runner)
    checker.oracles = {i: b/f'runs/R-trunk-{i}/native/trunk/captures' for i in range(4)}
    checker.checks, checker.parse = checks, parse
    checker.profile = old.read(root/'run-01/qualification-02/STATE_PROFILES.json')['Qwen']
    first_job = old.read(work/plan['workers'][0]['job'])
    structure = checks.gguf_structure(first_job['target_model'])
    need(len(checker.profile['layers']) == structure['layers'] and
         [x['id'] for x in checker.profile['layers']] == list(range(structure['layers'])) and
         checker.profile['target_model_sha256'] == first_job['target_sha256'],
         'Complete original 8B state profile must match the pinned GGUF, not an assumed layer count')
    proofs = []
    original = old.read(b/'QUALIFIED.json')['cells']
    for core in ('loop4', 'packed'):
        for origin in range(4):
            name = f'qualification-{core}-{origin}'
            job = old.read(b/'jobs'/(name+'.json'))
            out = b/'runs'/name
            need(old.read(out/'HOST.json')['status'] == 'COMPLETE', 'Saved qualification worker incomplete')
            need(old.read(out/'LOADED_MODULES.json') == plan['reuse']['builds'][core]['loaded_modules'],
                 'Original qualification module closure differs')
            need(old.read(out/'native/result.json')['context'] == plan['reuse']['builds'][core]['context'],
                 'Original qualification context differs')
            for item in job['diagnostics']:
                proof = module.Runner.check(checker, out/'native', item, core, True)
                previous = [x for x in original if x['core'] == core and x['name'] == item['name']]
                need(len(previous) == 1 and proof == previous[0], 'Full saved numerical comparison changed')
                d = out/'native'/item['name']
                for p, positions in [(d/'initial/sequence.bin', item['position']),
                                     (d/'final-sequence.bin', item['position']+8)]:
                    active, metadata = parse(p.read_bytes(), list(range(positions)), checker.profile)
                    need(np.isfinite(np.frombuffer(active, dtype='<f2')).all(), 'Nonfinite original active KV')
                proofs.append(proof)
    need(len(proofs) == 32, 'All original numerical cells required')
    old.save(work/'RECOMPUTED_32_CELLS.json', dict(passed=True, cells=proofs,
             numerical_GPU_requests=0, scope='Saved original raw vectors and active KV/frontier; no new GPU qualification'))
    # Fresh scheduler only; native source, arithmetic, graph policy and timers
    # remain unchanged. The original stage-B adapter's 79-request local limit
    # cannot admit a 128-operation B2 panel and must not be silently inherited.
    path = work/'runtime/host.py'
    before = path.read_text()
    needle = "need(sum(r['requests'] for r in reserved)+req<=79,'Stage B ceiling, no stage transfer')"
    need(before.count(needle) == 1, 'Exact original stage-local ceiling anchor')
    after = before.replace(needle, "need(sum(r['requests'] for r in reserved)+req<=136,'B2 fixed128 plus8 reserved failure slots; no native retry')")
    path.write_text(after)
    old.save(work/'SCHEDULING_ADAPTER_DIFF.json', dict(native_changed=False, original_source_sha256=old.sha(original_source),
             diff=''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile='old-host', tofile='new-host'))))
    config = old.read(work/'config.private.json')
    need(config['gpu_uuid'] == admission['gpu_uuid'], 'New allocation differs from qualified hardware')
    config.update(allocation_id='explicit-user-PR217-B2-20261110', approved_by_user=True)
    # This is a fresh file in a fresh epoch, never a rewrite of an old config.
    old.save(work/'CURRENT_ALLOCATION.private.json', config)
    inherited = old.read(work/'INHERITED_ACCOUNTING.json')
    need(inherited['requests'] == 1909 and inherited['rows'] == 3053954, 'Re-audit all actual prior 8B ledgers')
    need(inherited['requests'] + 128 + 8 <= 2048, 'Whole fixed panel and8 failure slots must fit')
    old.save(work/'B2_BUDGET.json', dict(inherited_requests=inherited['requests'], inherited_rows=inherited['rows'],
             fixed_warm=64, fixed_measured=64, fixed_rows=33024, GPU_requalification=0, setup_requests=0,
             failure_closeout_reserve=8, incremental_ceiling=136, cumulative_registered_ceiling=2045,
             unchanged_absolute_ceiling=2048, row_ceiling=8000000, panel_endpoint_without_failure=2037,
             no_refunds=True, no_automatic_native_retry=True, cannot_borrow_32B=True))
    old.save(work/'CPU_REUSE_COMPLETE.json', dict(status='SAVED_NUMERICAL_REUSE_CHECKS_PASSED_EXECUTION_NOT_ADMITTED',
             utc=dt.datetime.now(dt.timezone.utc).isoformat(), caller_s=time.monotonic()-started,
             original_32_cells_recomputed=True, retained_archive_binary_files=1728, candidate_qualification_binary_files=352,
             native_ELF_and_dependencies_rehashed=True, native_requests_started=0,
             remaining=['Verify driver/hardware/environment binding', 'Freeze all new host/guard/ledger code and128 operations',
                        'Whole panel window and public complete-byte readback', 'Main32B delivery complete before B2 execution'] ))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('root', 'work', 'main-admission', 'original-source'):
        p.add_argument('--'+name, type=Path, required=True)
    a = p.parse_args()
    prepare(a.root, a.work, a.main_admission, a.original_source)
