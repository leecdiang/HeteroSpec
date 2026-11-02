"""B570 companion orchestration. Development continues; frozen confirmation is gated."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import audit
import budget
import design
from common import BASE, STUDY, TARGET, DRAFT, canonical, confined, digest, input_check, need, read, sha, utc, write

HERE = Path(__file__).resolve().parent


def code_identity():
    return {p.name: sha(p) for p in HERE.iterdir() if p.is_file()}


def build_files(receipt):
    b = read(receipt)
    need(b['status'] == 'BUILT_NOT_QUALIFIED', 'build incomplete')
    for f in b['files']:
        p = Path(f['path']);need(p.stat().st_size == f['bytes'] and sha(p) == f['sha256'], 'build bytes changed')
    need(sha(b['supervisor']) == b['supervisor_sha256'], 'supervisor changed')
    return b


def prepare(config, out):
    c = read(config);out = Path(out).resolve();need(not out.exists(), 'new epoch required')
    need(c.get('user_authorized') is True, 'native execution not authorized')
    need(sha(c['target']) == TARGET and sha(c['draft']) == DRAFT, 'same RTX Q8 weights required; no Q6 substitution')
    oracle, candidate = build_files(c['oracle_build']), build_files(c['candidate_build'])
    need(oracle['mode'] == 'oracle' and candidate['mode'] == 'candidate', 'distinct build roles')
    need(Path(oracle['executable']).parent != Path(candidate['executable']).parent, 'separate oracle/candidate libraries')
    need(c['threads'] > 0 and c['worker_timeout_seconds'] > 0, 'finite positive safety bound')
    need(c['min_vram_free_bytes'] > 0 and c['min_ram_free_bytes'] > 0 and c['min_disk_free_bytes'] > 0, 'memory/disk headroom')
    need(c['target_gpu_layers'] > 0 and c['draft_gpu_layers'] >= 0, 'placement profile')
    panel = read(c['development_panel']);need(len(panel) == 3, 'three retained controls')
    from common import DEVELOPMENT
    need([x['id'] for x in panel] == DEVELOPMENT, 'development IDs changed')
    for x in panel: input_check(x)
    root = Path(c['research_root']).resolve();need(root != out, 'research root and epoch differ')
    root.mkdir(parents=True, exist_ok=True)
    marker=root/'RESEARCH_IDENTITY.json'
    if marker.exists(): need(read(marker)['study_id']==STUDY, 'foreign study ledger')
    else:
        need(not (root/'LEDGER.jsonl').exists(), 'unidentified old ledger; do not adopt/reset')
        write(marker, {'study_id':STUDY, 'created':utc(), 'base':BASE})
    out.mkdir(parents=True)
    weights = {k: {'path': str(Path(c[k]).resolve()), 'sha256': sha(c[k]),
                 'bytes': Path(c[k]).stat().st_size, 'mtime_ns': Path(c[k]).stat().st_mtime_ns} for k in ('target', 'draft')}
    c['research_root'] = str(root);c['oracle'] = oracle;c['candidate'] = candidate
    c['study_id'] = STUDY;c['code'] = code_identity();c['weights'] = weights
    write(out / 'CONFIG.json', c);write(out / 'DEV.json', panel)
    write(out / 'EPOCH.json', {'created': utc(), 'base': BASE, 'config_sha256': sha(out / 'CONFIG.json'),
          'development_sha256': sha(out / 'DEV.json'), 'code': code_identity(),
          'source_policy': c.get('policy', {}), 'model_requests': 0})
    if not (root / 'LEDGER.jsonl').exists():
        budget.extend(root / 'LEDGER.jsonl', c.get('initial_credits', 16384), c.get('initial_seconds', 604800),
                      'Initial author-authorized renewable engineering/development reservation; not a scientific sample-size ceiling')
    return out


def check(epoch, full=False):
    epoch = Path(epoch);c = read(epoch / 'CONFIG.json');e = read(epoch / 'EPOCH.json')
    need(e['config_sha256'] == sha(epoch / 'CONFIG.json') and e['development_sha256'] == sha(epoch / 'DEV.json'), 'epoch config/panel drift')
    need(e['code'] == code_identity(), 'code changed: create a successor epoch, retain old records')
    for v in c['weights'].values():
        p = Path(v['path']);need(p.stat().st_size == v['bytes'] and p.stat().st_mtime_ns == v['mtime_ns'], 'weight identity metadata changed')
        if full: need(sha(p) == v['sha256'], 'weight content changed')
    for key in ('oracle_build', 'candidate_build'):
        if full: build_files(c[key])
    return c


def paths(epoch, attempt):
    unit = confined(Path(epoch) / 'units', attempt)
    receipt = read(unit / 'RECEIPT.json')
    need(receipt['success'], 'attempt incomplete; preserve it, use a new ID after engineering recovery')
    rows = read(unit / 'SLOTS.json')
    return [confined(unit / 'native', s['id'] + '.json') for s in rows]


def execute(epoch, attempt, slots, oracle=False, admit=False):
    need(os.name == 'nt', 'native execution requires Windows B570 host')
    epoch = Path(epoch);c = check(epoch);root = Path(c['research_root'])
    need(not any(s.get('probe_cycle', -1) >= 0 or s.get('trace') for s in slots if s['stage'] in ('measured', 'warmup', 'qualification', 'reference')), 'diagnostic mixed with confirmation')
    if any(s['stage'] in ('qualification', 'measured', 'warmup') for s in slots):
        frozen = read(epoch / 'FREEZE.json');need(frozen['epoch_sha256'] == sha(epoch / 'EPOCH.json') and frozen['environment_sha256'] == sha(epoch / 'ENVIRONMENT.json'), 'candidate/environment not frozen')
    if oracle: need(all(s['arm'] == 'R' for s in slots), 'oracle only R')
    if not admit:
        environment = read(epoch / 'ENVIRONMENT.json')
        for f in environment['loaded_module_pins']:
            need(Path(f['path']).stat().st_size == f['bytes'] and sha(f['path']) == f['sha256'], 'pre-forward loaded driver/OS/runtime identity changed')
    for s in slots:
        input_check(s['input']);confined(epoch / 'dummy', s['id'])
    unit = confined(epoch / 'units', attempt);need(not unit.exists(), 'new attempt ID required')
    need(shutil.disk_usage(epoch).free >= c['min_disk_free_bytes'], 'disk reserve')
    lock = Path(c['gpu_lock_file']);lock.parent.mkdir(parents=True, exist_ok=True)
    write(lock, {'pid': os.getpid(), 'epoch': str(epoch.resolve()), 'attempt': attempt, 'utc': utc()})
    started = False;cleaned = False;success = False;actual = 0;error = None;begin = time.monotonic()
    engine = c['oracle' if oracle else 'candidate']
    try:
        unit.mkdir(parents=True)
        write(unit / 'SLOTS.json', slots);write(unit / 'NATIVE_CONFIG.json', c)
        diagnostic = sum(5 for s in slots if s.get('probe_cycle', -1) >= 0)
        budget.reserve(root / 'LEDGER.jsonl', str(unit), 0 if admit else len(slots), 0 if admit else diagnostic, c['worker_timeout_seconds'])
        started = True
        # Whole-model hashing was done at epoch/session boundaries. Frozen EXE/DLLs
        # are rehashed by the native supervisor; stat identities are checked above.
        write(unit / 'FILES.json', {'files': engine['files']})
        if not admit:
            exposure = root / 'EXPOSURE.jsonl'
            with exposure.open('a', encoding='utf-8') as f:
                for s in slots:
                    x = s['input'];f.write(canonical({'id': x['id'], 'text_sha256': x.get('text_sha256'),
                        'prompt_ids_sha256': digest(x['prompt_ids']), 'attempt': str(unit), 'stage': s['stage'], 'utc': utc()}).decode() + '\n')
                f.flush();os.fsync(f.fileno())
        command = [sys.executable, '-B', engine['supervisor'], '--manifest', str(unit / 'FILES.json'),
                   '--receipt', str(unit / 'SUPERVISOR.json'), '--limit', str(int(c['worker_timeout_seconds'])),
                   '--minimum-free-bytes', str(c['min_disk_free_bytes']),
                   engine['executable'], str(unit / 'NATIVE_CONFIG.json'), str(unit / 'native'), str(unit / 'SLOTS.json')]
        if admit: command += ['--admit']
        write(unit / 'COMMAND.json', {'argv': command, 'engine': engine['mode'], 'epoch_sha256': sha(epoch / 'EPOCH.json'),
               'environment_sha256': sha(epoch / 'ENVIRONMENT.json') if (epoch / 'ENVIRONMENT.json').exists() else None})
        run = subprocess.run(command, timeout=c['worker_timeout_seconds'] + 180, check=False)
        receipt = read(unit / 'SUPERVISOR.json')
        cleaned = receipt.get('job_accounting', {}).get('active_processes') == 0
        native = read(unit / 'native/result.json')
        actual = len(native.get('records', []))
        need(run.returncode == 0 and receipt['status'] == 'complete' and cleaned, 'supervision/cleanup failure')
        need(native['status'] == ('RESOURCE_ADMITTED' if admit else 'COMPLETE') and native['normal_cleanup_returned'], 'native incomplete')
        need(actual == (0 if admit else len(slots)), 'request accounting')
        # Loaded libraries must include the bound runtime, not another DLL on PATH.
        loaded = {Path(x['path']).name.lower(): x['sha256'] for x in receipt['loaded_module_hashes']}
        for item in engine['files']:
            name = Path(item['path']).name.lower()
            if name in loaded:
                need(loaded[name] == item['sha256'], 'loaded numerical DLL bytes differ')
        for name in ('llama.dll', 'ggml.dll', 'ggml-base.dll', 'ggml-vulkan.dll'):
            need(name in loaded, 'required runtime DLL not observed loaded: ' + name)
        if admit:
            write(epoch / 'ENVIRONMENT.json', {'utc': utc(), 'source_receipt_sha256': sha(unit / 'SUPERVISOR.json'),
                 'loaded_module_pins': receipt['loaded_module_hashes'],
                 'scope': 'Modules observed during zero-forward admission; not all kernel-driver bodies or Vulkan pipeline identity'})
        if not admit:
            for s in slots:
                checked = audit.record(confined(unit / 'native', s['id'] + '.json'))
                need(checked['record']['slot'] == s, 'native schedule drift')
                if s['stage'] in ('measured', 'warmup'):
                    refs = read(epoch / 'QUALIFIED_REFERENCES.json')
                    need(checked['endpoint'] == refs[s['input']['id']], 'timing reference failure')
        success = True
    except BaseException as e:
        error = repr(e)
        if (unit / 'native/result.json').exists(): actual = len(read(unit / 'native/result.json').get('records', []))
        raise
    finally:
        seconds = time.monotonic() - begin
        # If the supervisor was interrupted without a cleanup receipt, retain the
        # lock and leave the ledger START unsettled; an agent must reconcile it.
        if (unit / 'SUPERVISOR.json').exists():
            receipt = read(unit / 'SUPERVISOR.json');cleaned = receipt.get('job_accounting', {}).get('active_processes') == 0
        if unit.exists():
            write(unit / 'RECEIPT.json', {'success': success, 'error': error, 'completed_model_requests': actual,
                  'cleanup_verified': cleaned, 'owned_seconds': seconds, 'utc': utc()})
        if started and cleaned:
            budget.append(root / 'LEDGER.jsonl', {'event': 'END', 'attempt': str(unit), 'completed_model_requests': actual,
                          'operator_calls': 0, 'seconds': seconds, 'success': success})
        if not started or cleaned: lock.unlink(missing_ok=True)
    return unit


def review_freeze(epoch, review_path):
    epoch = Path(epoch);check(epoch, full=True);r = read(review_path)
    need(r['disposition'] in ('EVIDENCED_REPAIR', 'NONTRIGGER_PORT_VALIDATION'), 'review disposition')
    need(r['mechanism'].strip() and r['regression_summary'].strip(), 'scientific review missing')
    need(r.get('baseline_oracle_stable') is True and r.get('observation_controls_pass') is True, 'baseline/observer gates')
    if r['disposition'] == 'EVIDENCED_REPAIR': need(r.get('ablation_pass') is True, 'repair needs intervention control')
    need(r.get('evidence'), 'review must pin actual reports, not booleans only')
    exposure = r.get('cross_project_exposure_audit')
    need(exposure and sha(exposure['path']) == exposure['sha256'], 'cross-project exposure audit is required before confirmation')
    for item in r['evidence']: need(sha(item['path']) == item['sha256'], 'review evidence drift')
    write(epoch / 'FREEZE.json', {'epoch_sha256': sha(epoch / 'EPOCH.json'), 'review': r,
          'review_sha256': sha(review_path), 'environment_sha256': sha(epoch / 'ENVIRONMENT.json'), 'frozen_utc': utc(), 'heldout_exposed': False})


def baseline(epoch):
    epoch = Path(epoch);panel = read(epoch / 'DEV.json')
    for name, slots, oracle in [('baseline-oracle', design.references(panel), True), ('baseline-candidate', design.baseline(panel), False)]:
        if (epoch / 'units' / name).exists():
            for p in paths(epoch, name): audit.record(p)
        else: execute(epoch, name, slots, oracle=oracle)
    result = audit.matrix(paths(epoch, 'baseline-candidate'), paths(epoch, 'baseline-oracle'), [x['id'] for x in panel])
    if (epoch / 'BASELINE_AUDIT.json').exists(): need(read(epoch / 'BASELINE_AUDIT.json') == result, 'baseline re-audit differs')
    else: write(epoch / 'BASELINE_AUDIT.json', result)
    return result


def confirm(epoch, panel_path):
    epoch = Path(epoch);check(epoch, full=True);frozen = read(epoch / 'FREEZE.json');panel = read(panel_path)
    selection = read(str(panel_path)+'.selection.json')
    need(selection['panel_sha256'] == sha(panel_path) and selection['candidate_freeze_sha256'] == sha(epoch / 'FREEZE.json'), 'panel selection/freeze binding')
    need(selection['new_model_requests'] == 0 and selection['tokenizer_binding'], 'native tokenizer-bound pre-forward selection required')
    need(len(panel) in (12, 24), 'prospective confirmation panel size')
    need(len({x['id'] for x in panel}) == len(panel), 'duplicate confirmation IDs')
    for x in panel: input_check(x)
    seal = epoch / 'PANEL_SEAL.json'
    if seal.exists(): need(read(seal)['panel_sha256'] == sha(panel_path), 'confirmation panel changed')
    else:
        c = read(epoch / 'CONFIG.json');exposure = Path(c['research_root']) / 'EXPOSURE.jsonl'
        rows = [json.loads(l) for l in exposure.read_text().splitlines()] if exposure.exists() else []
        seen_ids = {x['id'] for x in rows};seen_tokens = {x['prompt_ids_sha256'] for x in rows}
        need(all(x['id'] not in seen_ids and digest(x['prompt_ids']) not in seen_tokens for x in panel), 'already exposed panel')
        need(frozen['epoch_sha256'] == sha(epoch / 'EPOCH.json'), 'stale candidate freeze')
        write(seal, {'panel_sha256': sha(panel_path), 'selected_after_freeze': True, 'utc': utc(),
              'cross_project_exclusion_report': frozen['review']['cross_project_exposure_audit']})
    for name, slots, original in [('confirm-oracle', design.references(panel), True), ('confirm-candidate', design.qualification(panel), False)]:
        if not (epoch / 'units' / name).exists(): execute(epoch, name, slots, oracle=original)
        else:
            for p in paths(epoch, name): audit.record(p)
    result = audit.matrix(paths(epoch, 'confirm-candidate'), paths(epoch, 'confirm-oracle'), [x['id'] for x in panel])
    if not (epoch / 'QUALIFICATION.json').exists(): write(epoch / 'QUALIFICATION.json', result)
    need(result['all_reference_equal'], 'confirmation failed; retain exposed panel and develop a successor, no successful-subset timing')
    refs = {audit.record(p)['record']['input_id']: audit.record(p)['endpoint'] for p in paths(epoch, 'confirm-oracle')}
    if not (epoch / 'QUALIFIED_REFERENCES.json').exists(): write(epoch / 'QUALIFIED_REFERENCES.json', refs)
    all_paths = []
    for session in range(6):
        # Each warmup/measurement pair is one model-loaded worker. R uses the
        # original oracle binary; every arm has identical fresh-context lifecycle.
        schedule = design.timing(panel, session)
        for j in range(0, len(schedule), 2):
            pair = schedule[j:j+2];name = f's{session}-pair{j//2:03d}'
            if not (epoch / 'units' / name).exists(): execute(epoch, name, pair, oracle=pair[0]['arm'] == 'R')
            all_paths += paths(epoch, name)
    checked = [audit.record(p)['record'] for p in all_paths]
    need(all(audit.endpoint(r) == refs[r['input_id']] for r in checked), 'saved timing endpoint drift')
    report = audit.performance(checked, [x['id'] for x in panel])
    if (epoch / 'COST.json').exists(): need(read(epoch / 'COST.json') == report, 'cost re-audit differs')
    else: write(epoch / 'COST.json', report)
    return report['means']


def main():
    p = argparse.ArgumentParser(description=__doc__);sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('prepare');a.add_argument('--config', required=True);a.add_argument('--out', required=True)
    a = sub.add_parser('budget');a.add_argument('--root', required=True);a.add_argument('--credits', type=int, required=True);a.add_argument('--seconds', type=float, required=True);a.add_argument('--reason', required=True)
    for name in ('admit', 'baseline'):
        a = sub.add_parser(name);a.add_argument('--epoch', required=True)
    a = sub.add_parser('run');a.add_argument('--epoch', required=True);a.add_argument('--attempt', required=True);a.add_argument('--slots', required=True);a.add_argument('--oracle', action='store_true')
    a = sub.add_parser('freeze');a.add_argument('--epoch', required=True);a.add_argument('--review', required=True)
    a = sub.add_parser('confirm');a.add_argument('--epoch', required=True);a.add_argument('--panel', required=True)
    a = p.parse_args()
    if a.command == 'prepare': print(prepare(a.config, a.out))
    elif a.command == 'budget': print(budget.extend(Path(a.root) / 'LEDGER.jsonl', a.credits, a.seconds, a.reason))
    elif a.command == 'admit': execute(a.epoch, 'capacity', [], admit=True)
    elif a.command == 'baseline': print(baseline(a.epoch))
    elif a.command == 'run': execute(a.epoch, a.attempt, read(a.slots), oracle=a.oracle)
    elif a.command == 'freeze': review_freeze(a.epoch, a.review)
    elif a.command == 'confirm': print(confirm(a.epoch, a.panel))


if __name__ == '__main__': main()
