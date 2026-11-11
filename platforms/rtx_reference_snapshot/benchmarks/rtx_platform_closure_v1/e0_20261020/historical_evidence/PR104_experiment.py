"""Prospective RTX PQ/QB replication. CPU planning/analysis and pinned native adapter.

No new GPU result is bundled. Python >=3.11; native execution is Windows-only.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import statistics
import struct
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone

BASELINE_COMMIT = '3235d44c26edd92db33e574094c26af8e29d2452'
FAMILIES = ('Qwen', 'SmolLM2', 'Llama')
PATHS = ('M', 'C')
SESSIONS = 6
SOURCE_BLOBS = {
    'resident.py': 'd19ccfdb927d23fcd562b176d01235ff5ecce88a',
    'run_common.py': 'dd991088f480972e862139a33d6bc46384fa1900',
}
RESULT_BLOBS = {
    'P0_PLAN.json': '07eaaa3245affb8f5eb2ebf28dd51f1bcdf51c08',
    'NATIVE_BUILD.json': 'd46555368bba38eeff3bd2940c629870d4538f63',
    'MODEL_CONTRACT.json': '43f8ab27dceb8c559c4045c194c4913bca911a0d',
}
ROUTING_BLOBS = {
    'NATIVE_BUILD_V02.json': '02c2110d532c227e844188b324456de3669a6d1b',
    'RESOURCE_CORRECTION.json': 'f09219d0695ed52732150b2c6e1a7b0c7fd8b07f',
    'LIVE_PREFLIGHT.json': 'ebb03677fbd619240610ddc82144d834da571eef',
    'EXECUTION_DEPENDENCIES.json': '0084373c1de6e6bcc5d13355c81dbb89da0978c3',
}
ARMS = ('R', 'M_PQ', 'M_QB', 'C_PQ', 'C_QB')
CAPTURE_BLOB = 'd56faa2d4f6c904c1d583ae31c85dda87ebb2ca1'
REPLAY_BLOB = '7c4cb5bb51cadff7b6b829c5ad4aee855e1d0396'


def require(ok, message):
    if not ok: raise ValueError(message)


def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encoded(x): return (json.dumps(x, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode()
def digest(b): return hashlib.sha256(b).hexdigest()
def utc(): return datetime.now(timezone.utc).isoformat()


def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def blob(b): return hashlib.sha1(b'blob ' + str(len(b)).encode() + b'\0' + b).hexdigest()


def save(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f:
        f.write(encoded(value)); f.flush(); os.fsync(f.fileno())


def pin(p):
    p = Path(p).resolve()
    return dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))


def signature(r):
    o = r['output']
    return {k: o[k] for k in ('ids', 'eog_flags', 'length', 'terminal_id', 'stop_reason', 'cached_tokens', 'truncated')}


def condition(name):
    if name == 'R':
        return dict(name=name, prefill_ub=1, maximum_k=0, mask=0, spec=False, required_output_rows=1, layout='QB')
    prefix, layout = name.split('_')
    require(prefix in PATHS and layout in ('PQ', 'QB'), 'invalid comparison arm')
    return dict(name=name, prefill_ub=4, maximum_k=3 if prefix == 'C' else 0,
                mask=3, spec=prefix == 'C', required_output_rows=4 if prefix == 'C' else 1, layout=layout)


def runtime_manifest(root):
    """The exact PR98 corrected routing, independent of observed performance."""
    builds = {name: read(root/name) for name in ('NATIVE_BUILD.json', 'NATIVE_BUILD_V02.json')}
    for name, build in builds.items():
        expected = (RESULT_BLOBS | ROUTING_BLOBS)[name]
        require(blob((root/name).read_bytes()) == expected, 'runtime build manifest differs: '+name)
    require(builds['NATIVE_BUILD.json']['numerical_DLL_sha256'] == builds['NATIVE_BUILD_V02.json']['numerical_DLL_sha256'], 'corrected runtime changed numerical DLLs')
    routes = []
    for family in FAMILIES:
        for arm in ARMS:
            corrected = family in ('SmolLM2', 'Llama') and arm.endswith('_PQ')
            name = 'NATIVE_BUILD_V02.json' if corrected else 'NATIVE_BUILD.json'
            build = builds[name]
            routes.append(dict(family=family, arm=arm,
                               binary='llama-server-pq-metadata4.exe' if corrected else 'llama-server.exe',
                               binary_sha256=build['server_sha256'], build_manifest=name,
                               build_manifest_sha256=sha(root/name),
                               source_inventory_sha256=build['source_inventory_sha256']))
    return dict(schema=1, baseline_commit=BASELINE_COMMIT, routes=routes,
                numerical_DLL_sha256=builds['NATIVE_BUILD.json']['numerical_DLL_sha256'],
                selection='PR98: metadata4 only for SmolLM2/Llama M_PQ/C_PQ; original for all other arms')


def verify_runtime_manifest(out):
    expected = runtime_manifest(out)
    require(read(out/'RUNTIME_MANIFEST.json') == expected, 'family/arm runtime routing changed')
    for route in expected['routes']:
        require(sha(out/'native/build/bin'/route['binary']) == route['binary_sha256'], 'selected binary differs')
    return expected


def runtime_worker(native, out, ledger, family, c, phase, name):
    """Bind command, source identity and module verification to one fixed arm.

    The inherited helper files remain byte-pinned and unmodified. The selected
    build view is active only while this single owned worker is in its context.
    """
    manifest = read(out/'RUNTIME_MANIFEST.json')
    route = next(r for r in manifest['routes'] if (r['family'], r['arm']) == (family, c['name']))
    build = read(out/route['build_manifest'])
    executable = (out/'native/build/bin'/route['binary']).resolve()
    require(sha(executable) == route['binary_sha256'], 'arm executable changed')
    original_read = native.read

    class BoundResident(native.Resident):
        def __init__(self):
            super().__init__(ledger, family, c, phase, name)
            self.cmd[0] = str(executable)
            self.runtime_route = route
        def __enter__(self):
            def selected_read(path):
                return build if Path(path).resolve() == (out/'NATIVE_BUILD.json').resolve() else original_read(path)
            native.read = selected_read
            try:
                result = super().__enter__()
                save(self.d/'RUNTIME_ROUTE.json', route)
                return result
            except BaseException:
                self.__exit__(None, None, None)
                raise
        def verify_modules(self, obs):
            # The legacy verifier recognizes only the original executable name.
            matches = [Path(p).resolve() for p in obs['modules'] if Path(p).name.lower() == executable.name.lower()]
            require(matches == [executable], 'actual loaded executable differs from arm manifest')
            require(sha(matches[0]) == route['binary_sha256'], 'loaded executable bytes differ')
            super().verify_modules(obs)
        def __exit__(self, *args):
            try:
                p = getattr(self, 'p', None)
                if p is not None and p.poll() is None:
                    p.terminate()
                    try: p.wait(timeout=10)
                    except subprocess.TimeoutExpired: p.kill(); p.wait(timeout=10)
                if hasattr(self, 'log') and not self.log.closed: self.log.close()
                if hasattr(self, 'start') and not (self.d/'LIFETIME.json').exists():
                    seconds = time.perf_counter()-self.start
                    save(self.d/'LIFETIME.json', dict(seconds=seconds, utc=utc(), pid=p.pid if p else None,
                                                   exit_code=p.returncode if p else None, phase=self.phase))
                    self.ledger.life += seconds
            finally:
                native.read = original_read
    return BoundResident()


def validate_panel(panel):
    require(set(panel) == set(FAMILIES), 'exactly three inherited families required')
    for family, tasks in panel.items():
        require(len(tasks) == 12 and len({t['id'] for t in tasks}) == 12, 'twelve unique tasks per family')
        for t in tasks:
            require(t['cap'] == 128 and isinstance(t['prompt_ids'], list), 'direct-ID cap128 contract')
            require(0 < len(t['prompt_ids']) <= 768 and all(type(i) is int and i >= 0 for i in t['prompt_ids']), 'invalid prompt IDs')


def schedule(panel, seed=20261014):
    validate_panel(panel)
    rng = random.Random(seed); blocks = []
    for session in range(SESSIONS):
        families = list(FAMILIES); rng.shuffle(families)
        for family in families:
            tasks = list(panel[family]); rng.shuffle(tasks)
            family_blocks = [('R', tasks)]
            paths = list(PATHS); rng.shuffle(paths)
            for path in paths:
                for group in range(4):
                    triplet = tasks[group*3:group*3+3]
                    arms = ['PQ', 'QB'] if (session + group) % 2 == 0 else ['QB', 'PQ']
                    for arm in arms: family_blocks.append((path + '_' + arm, triplet))
            family_blocks.append(('R', tasks))
            for index, (arm, subset) in enumerate(family_blocks):
                blocks.append(dict(id=f's{session}/{family}/b{index:02d}', session=session, family=family,
                                   arm=arm, order=len(blocks), tasks=[t['id'] for t in subset],
                                   reference_side=('before' if index == 0 else 'after') if arm == 'R' else None))
    require(len(blocks) == 324 and sum(len(b['tasks']) + 1 for b in blocks) == 1620, 'budget accounting error')
    return blocks


def prepare(results: Path, legacy: Path, runtime: Path, out: Path, holdout: Path | None = None):
    results, legacy, runtime, out = (p.resolve() for p in (results, legacy, runtime, out))
    require(not out.exists(), 'new isolated work directory required')
    for root, registry in ((results, RESULT_BLOBS), (legacy, SOURCE_BLOBS)):
        for name, expected in registry.items(): require(blob((root/name).read_bytes()) == expected, 'baseline changed: ' + name)
    for name, expected in ROUTING_BLOBS.items():
        require(blob((results/name).read_bytes()) == expected, 'corrected baseline changed: '+name)
    for name, expected in read(results/'EXECUTION_DEPENDENCIES.json')['reused_authenticated_parent_code'].items():
        require(sha(legacy/name) == expected, 'inherited helper differs: '+name)
    old = read(results/'P0_PLAN.json')
    panel = read(holdout) if holdout else old['P2_panel']
    validate_panel(panel)
    if holdout:
        for family in FAMILIES:
            old_ids = {t['id'] for t in old['P2_panel'][family]}
            old_prompts = {tuple(t['prompt_ids']) for t in old['P2_panel'][family]}
            require(not any(t['id'] in old_ids or tuple(t['prompt_ids']) in old_prompts for t in panel[family]), 'holdout overlaps old P2 panel')
    contract = read(results/'MODEL_CONTRACT.json')
    for family in FAMILIES:
        for task in panel[family]:
            require(all(i < contract['families'][family]['vocabulary_tokens'] for i in task['prompt_ids']), 'ID exceeds native vocabulary')
    out.mkdir(parents=True); target = out/'native/build/bin'; target.mkdir(parents=True)
    build = read(results/'NATIVE_BUILD.json')
    for name, expected in {'llama-server.exe': build['server_sha256'], **build['numerical_DLL_sha256']}.items():
        require(sha(runtime/name) == expected, 'runtime bytes differ: ' + name)
        shutil.copy2(runtime/name, target/name)
    corrected = read(results/'NATIVE_BUILD_V02.json')
    name = 'llama-server-pq-metadata4.exe'
    require(sha(runtime/name) == corrected['server_sha256'], 'corrected runtime bytes differ')
    shutil.copy2(runtime/name, target/name)
    for name in ('MODEL_CONTRACT.json', 'NATIVE_BUILD.json', 'NATIVE_BUILD_V02.json', 'RESOURCE_CORRECTION.json', 'COUNTER_SEMANTICS.md'):
        shutil.copy2(results/name, out/name)
    save(out/'RUNTIME_MANIFEST.json', runtime_manifest(out))
    plan = dict(schema=1, study='rtx-pq-qb-independent-blocks-v1', baseline_commit=BASELINE_COMMIT,
                legacy=str(legacy), results=str(results), panel=panel, warmups=old['warmups'], blocks=schedule(panel),
                input_exposure='USER_SUPPLIED_DISJOINT_FROM_P2_ONLY' if holdout else 'EXPOSED_PANEL_NEW_EXECUTION_BLOCKS',
                sessions=SESSIONS, minimum_session_gap_seconds=3600, minimum_total_span_seconds=86400,
                whole_request_cap=1620, owned_seconds_cap=43200, practical_speed_ratio=1.02,
                seed=20261014, estimator='equal-weight session means of paired task log(PQ/QB)',
                stopping='six registered sessions or explicit failure/budget stop; no significance-dependent extension')
    save(out/'PLAN.json', plan)
    files = list(legacy.glob('*.py')) + list(Path(__file__).parent.glob('*.py'))
    files += [Path(__file__).parent/'RUNTIME_ADAPTER_AMENDMENT.md', Path(__file__).parent/'runtime_adapter_v02/CPU_TESTS.log']
    files += list(target.iterdir()) + [out/n for n in ('PLAN.json', 'MODEL_CONTRACT.json', 'NATIVE_BUILD.json', 'NATIVE_BUILD_V02.json', 'RESOURCE_CORRECTION.json', 'COUNTER_SEMANTICS.md', 'RUNTIME_MANIFEST.json')]
    for family in FAMILIES:
        for role, item in contract['families'][family]['models'].items():
            p = Path(item['path']); require(p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], 'model pin differs')
            files.append(p)
    sys.path.insert(0, str(legacy))
    common = importlib.import_module('run_common')
    host = common.host(); inherited = read(results/'LIVE_PREFLIGHT.json')['sample']
    identity = ('gpu', 'driver', 'total_MiB', 'power_scheme_guid')
    require(all(host[k] == inherited[k] for k in identity), 'host identity differs from PR98')
    require(host['AC'] == 1, 'AC power required')
    host['clock_and_power_raw'] = subprocess.check_output(['nvidia-smi','--query-gpu=uuid,clocks.sm,clocks.mem,power.limit','--format=csv,noheader,nounits'],timeout=15).decode().strip()
    save(out/'PHASE0_HOST.json', host); files.append(out/'PHASE0_HOST.json')
    files.extend((Path(sys.executable), Path(os.environ['SystemRoot'])/'System32/nvcuda.dll'))
    frozen_files = [pin(p) for p in sorted(set(files))]
    manifest = verify_runtime_manifest(out)
    prior = read(Path(__file__).parent/'execution_20261014/UNREGISTERED_PLAN.json')
    require(plan['blocks'] == prior['blocks'] and plan['panel'] == prior['panel'], 'registered study design differs from stopped attempt')
    gate = dict(schema=2, status='PASS', created_utc=utc(), native_requests_started=0,
                checks=dict(baseline_blobs='PASS', inherited_helpers='PASS', binary_and_DLL_hashes='PASS',
                            model_hashes='PASS', host_identity='PASS', AC='PASS', runtime_routes='PASS',
                            unchanged_panel_schedule_budget='PASS'),
                routes_checked=len(manifest['routes']), files_checked=len(frozen_files),
                preserved_failure_commit='ccfbc2e4c3ab3026a6bbec5caf4c98646781913c',
                loaded_module_full_offload='DEFERRED_TO_EACH_OWNED_E2_WORKER')
    save(out/'PHASE0_GATE.json', gate); frozen_files.append(pin(out/'PHASE0_GATE.json'))
    save(out/'FREEZE.json', dict(schema=2, study='rtx-pq-qb-independent-blocks-v1', baseline_commit=BASELINE_COMMIT,
                                created_utc=utc(), new_gpu_forwards=0, phase0_admitted=True,
                                runtime_manifest_sha256=sha(out/'RUNTIME_MANIFEST.json'),
                                host_identity={k:host[k] for k in identity},
                                phase0_gate_sha256=sha(out/'PHASE0_GATE.json'), files=frozen_files))
    print('PREPARED: 864 PQ/QB + 432 reference + 324 warmup = 1620 native request starts. Commit FREEZE.json before execution.')


def verify_freeze(out, repo, commit, registration, remote=True):
    require(not sys.flags.optimize, 'do not run inherited guards with python -O')
    require(len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'full freeze commit required')
    body = subprocess.check_output(['git', 'show', f'{commit}:{registration}'], cwd=repo)
    require(body == (out/'FREEZE.json').read_bytes(), 'freeze commit differs')
    if remote:
        actual = subprocess.check_output(['gh', 'api', f'repos/leecdiang/HeteroSpec/contents/{registration}?ref={commit}', '-H', 'Accept: application/vnd.github.raw+json'], cwd=repo)
        require(actual == body, 'authenticated remote freeze differs')
    frozen = read(out/'FREEZE.json')
    require(frozen.get('schema') == 2, 'schema-2 family/arm freeze required')
    require(frozen.get('phase0_admitted') is True, 'Phase 0 not admitted')
    require(sha(out/'PHASE0_GATE.json') == frozen['phase0_gate_sha256'] and read(out/'PHASE0_GATE.json')['status']=='PASS', 'Phase 0 gate differs')
    require(sha(out/'RUNTIME_MANIFEST.json') == frozen['runtime_manifest_sha256'], 'runtime manifest freeze differs')
    verify_runtime_manifest(out)
    for item in frozen['files']:
        p = Path(item['path'])
        require(p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], 'frozen file changed: ' + str(p))


def telemetry(native):
    value = native.host()
    command = ['nvidia-smi', '--query-gpu=uuid,clocks.sm,clocks.mem,power.limit', '--format=csv,noheader,nounits']
    value['clock_and_power_raw'] = subprocess.check_output(command, timeout=15).decode().strip()
    return value


def cool(native, destination, expected=None):
    samples = []; begin = time.monotonic()
    while time.monotonic() - begin <= 300:
        s = telemetry(native); samples.append(s)
        if expected:
            require(all(s[k] == expected[k] for k in ('gpu', 'driver', 'total_MiB', 'power_scheme_guid')), 'host identity/power scheme changed')
        last = samples[-3:]
        if len(last) == 3 and all(x['AC'] == 1 and x['util'] <= 5 and x['temp'] <= 55 for x in last) and max(x['temp'] for x in last)-min(x['temp'] for x in last) <= 2:
            save(destination, dict(status='PASS', samples=samples)); return s
        time.sleep(5)
    save(destination, dict(status='HOST_ADMISSION_FAILED', samples=samples))
    raise RuntimeError('host cooling gate failed; no arm substitution')


class Ledger:
    def __init__(self, root):
        self.root = root/'ledger'; self.root.mkdir(exist_ok=True)
        self.events = [read(p) for p in sorted(self.root.glob('*.json'))]
        self.life = sum(read(p)['seconds'] for p in (root/'runs').rglob('LIFETIME.json'))
        self.active_start = None
    def lifetime(self): return self.life
    def owned(self): return self.life + (time.perf_counter()-self.active_start if self.active_start is not None else 0)
    def charge(self, family, phase, kind, slot):
        require(not any(e['slot'] == slot for e in self.events), 'started slot immutable; no retry')
        require(self.owned() < 43200-252, 'owned process time cap')
        if kind != 'load': require(sum(e['kind'] != 'load' for e in self.events) < 1620, 'native request cap')
        item = dict(family=family, phase=phase, kind=kind, slot=slot, utc=utc())
        save(self.root/f'{len(self.events):06d}.json', item); self.events.append(item)


def run_session(out, repo, commit, registration, session):
    require(os.name == 'nt' and 0 <= session < SESSIONS, 'Windows and session 0..5 required')
    verify_freeze(out, repo, commit, registration)
    plan = read(out/'PLAN.json'); sys.path.insert(0, plan['legacy'])
    common = importlib.import_module('run_common'); native = importlib.import_module('resident')
    for module in (common, native): module.LOCAL = out; module.PUB = out; module.PORT = 19614
    active = {}
    def environment(mask, trace):
        env = {k:v for k,v in os.environ.items() if not k.startswith(('HS_', 'LLAMA_ARG_', 'GGML_', 'CUDA_'))}
        env.update(HS_SCOPE_MASK=str(mask), HS_NATIVE_CAPTURE=str(trace), HS_Q95_LAYOUT=active['layout'])
        return env
    native.clean_env = environment
    receipt = out/'F0B_REMOTE_RECEIPT.json'
    if not receipt.exists(): save(receipt, dict(commit=commit, registration=registration))
    require(read(receipt)['commit'] == commit, 'cannot change freeze between sessions')
    for previous in range(session): require((out/f'SESSION-{previous}-COMPLETE.json').exists(), 'earlier session incomplete')
    lock = out/'EXECUTION.lock'
    with lock.open('x') as f: f.write(str(os.getpid()))
    try:
        session_path = out/f'SESSION-{session}.json'
        if not session_path.exists():
            if session:
                prev = read(out/f'SESSION-{session-1}-COMPLETE.json')
                require(time.time()-prev['epoch'] >= 3600, 'separate adjacent sessions by >=1h after completion')
            if session == SESSIONS-1:
                require(time.time()-read(out/'SESSION-0.json')['epoch'] >= 86400, 'last session must be >=24h after first')
            save(session_path, dict(utc=utc(), epoch=time.time(), session=session))
        ledger = Ledger(out)
        host_file = out/'HOST.json'; expected = read(host_file) if host_file.exists() else read(out/'PHASE0_HOST.json')
        tasks = {f:{t['id']:t for t in plan['panel'][f]} for f in FAMILIES}
        for block in (b for b in plan['blocks'] if b['session'] == session):
            result_path = out/'blocks'/(block['id'].replace('/', '_')+'.json')
            if result_path.exists():
                require(read(result_path)['status'] == 'COMPLETED', 'failed block cannot be retried'); continue
            sample = cool(native, out/'cooldown'/(block['id'].replace('/', '_')+'.json'), expected)
            if not host_file.exists(): save(host_file, sample)
            c = condition(block['arm']); active.clear(); active.update(c)
            worker = runtime_worker(native, out, ledger, block['family'], c, 'formal', block['id'])
            stop = threading.Event(); watch = None; records = []
            try:
                with worker as w:
                    ledger.active_start = w.start
                    def watchdog():
                        while not stop.wait(.5):
                            if ledger.owned() >= 43200-2:
                                if w.p.poll() is None: w.p.kill()
                                return
                    watch = threading.Thread(target=watchdog, daemon=True); watch.start()
                    meta = dict(pid=w.p.pid, environment_snapshot=sample, runtime_route=w.runtime_route)
                    w.complete(plan['warmups'][block['family']], block['id']+'/WARM', warmup=True, meta={'followup_block':block, 'excluded_warmup':True, **meta})
                    for position, task in enumerate(block['tasks']):
                        records.append(w.complete(tasks[block['family']][task], block['id']+'|'+task,
                                                  meta={'followup_block':block, 'task_position':position, **meta}))
                save(result_path, dict(status='COMPLETED', block=block, records=records, after_host=telemetry(native)))
            except BaseException as error:
                if not result_path.exists(): save(result_path, dict(status='FAILED', block=block, records=records, error=repr(error), utc=utc()))
                raise
            finally:
                stop.set()
                if watch: watch.join(timeout=2)
                ledger.active_start = None
        save(out/f'SESSION-{session}-COMPLETE.json', dict(epoch=time.time(), utc=utc(), session=session))
    finally: lock.unlink()
    print('SESSION_COMPLETE', session)


def quantile(xs, p):
    xs = sorted(xs); k = (len(xs)-1)*p; lo = int(k); hi = min(lo+1, len(xs)-1)
    return xs[lo]*(hi-k)+xs[hi]*(k-lo) if hi != lo else xs[lo]


def contrast(session_logs, seed=20261014):
    require(len(session_logs) == SESSIONS and all(math.isfinite(x) for x in session_logs), 'six finite independent session contrasts required')
    rng = random.Random(seed)
    boot = [statistics.fmean(rng.choices(session_logs, k=SESSIONS)) for _ in range(10000)]
    point = math.exp(statistics.fmean(session_logs)); interval = [math.exp(quantile(boot, p)) for p in (.025, .975)]
    return dict(speed_ratio_PQ_over_QB=point, QB_latency_reduction=1-1/point,
                session_cluster_percentile_interval=interval,
                session_ratios=[math.exp(x) for x in session_logs],
                practical_threshold=1.02, interval_entirely_above_threshold=interval[0] > 1.02,
                inference_scope='approximate six-session bootstrap, fixed tasks/single host; not a cross-device or well-powered date-cluster interval')


def analyze_blocks(plan, blocks):
    expected = {b['id']:b for b in plan['blocks']}; rows = {}; failures = []
    for item in blocks:
        b = item['block']; require(b['id'] in expected and b == expected[b['id']], 'unknown/changed block')
        require(b['id'] not in rows, 'duplicate block')
        rows[b['id']] = item
        if item['status'] != 'COMPLETED': failures.append(b['id'])
    answers = []
    for family in FAMILIES:
        for path in PATHS:
            needed = [b for b in plan['blocks'] if b['family'] == family and (b['arm'] == 'R' or b['arm'].startswith(path+'_'))]
            missing = [b['id'] for b in needed if b['id'] not in rows]
            bad = [b['id'] for b in needed if b['id'] in failures]
            refs = {}; times = {}; mismatches = []
            for b in needed:
                if b['id'] not in rows or b['id'] in failures: continue
                records = rows[b['id']]['records']
                require(len(records) == len(b['tasks']), 'incomplete block records')
                for task, r in zip(b['tasks'], records):
                    require(r['task'] == task and r['family'] == family and r['condition'] == b['arm'], 'record coordinate differs')
                    require(r['followup_block'] == b and r['slot'] == b['id']+'|'+task, 'record block binding differs')
                    valid = r['contract_valid'] and not r['workload_error'] and r['runtime_identity_verified']
                    valid = valid and r['measurement_mode'] == 'counts' and not r['warmup']
                    valid = valid and all(r['observation'][k] is False for k in ('phase_timers','heavy_capture','etw','added_sync'))
                    if not valid: mismatches.append(r['slot']); continue
                    require(math.isfinite(r['wall_ms']) and r['wall_ms'] > 0, 'invalid latency')
                    key = (b['session'], task)
                    if b['arm'] == 'R': refs.setdefault(key, []).append(signature(r))
                    else:
                        coord = key+(b['arm'],); require(coord not in times, 'duplicate arm/task')
                        times[coord] = r
            session_logs = []; task_rows = []; global_refs = {}; session_rows = []; task_failures = []
            for session in range(SESSIONS):
                logs = []
                for t in plan['panel'][family]:
                    key = (session, t['id']); ref = refs.get(key, [])
                    pair = [times.get(key+(path+'_'+a,)) for a in ('PQ','QB')]
                    if len(ref) != 2 or ref[0] != ref[1] or any(r is None for r in pair):
                        task_failures.append(dict(session=session,task=t['id'],reason='missing_pair_or_unstable_serial_endpoints',
                                                  reference_count=len(ref),reference_signatures=ref,
                                                  missing_arms=[path+'_'+a for a,r in zip(('PQ','QB'),pair) if r is None]))
                        continue
                    previous = global_refs.setdefault(t['id'], ref[0])
                    if previous != ref[0] or any(signature(r) != ref[0] for r in pair):
                        mismatches.append(f'{family}/{session}/{t["id"]}')
                        task_failures.append(dict(session=session,task=t['id'],reason='output_mismatch_or_cross_session_reference_change',
                                                  reference=ref[0],PQ=signature(pair[0]),QB=signature(pair[1])))
                        continue
                    value = math.log(pair[0]['wall_ms']/pair[1]['wall_ms']); logs.append(value)
                    task_rows.append(dict(session=session, task=t['id'], speed_ratio=math.exp(value),
                                          log_latency_contrast=value, PQ_latency_ms=pair[0]['wall_ms'],QB_latency_ms=pair[1]['wall_ms']))
                if len(logs) == 12: session_logs.append(statistics.fmean(logs))
                session_rows.append(dict(session=session,qualified_task_count=len(logs),
                                         log_latency_contrast=statistics.fmean(logs) if len(logs)==12 else None))
            qualified = not missing and not bad and not mismatches and len(session_logs) == SESSIONS
            answers.append(dict(family=family, path=path, status='QUALIFIED_FINITE_PANEL' if qualified else 'PENDING_OR_NONQUALIFIED',
                                estimate=contrast(session_logs) if qualified else None, missing=missing, failed=bad,
                                mismatches=mismatches, task_ratios=task_rows,
                                session_log_contrasts=session_rows,task_failures=task_failures,
                                task_regressions=sum(r['speed_ratio'] < 1 for r in task_rows)))
    return dict(comparisons=answers, extra_block_failure_count=len(failures), input_exposure=plan['input_exposure'])


def analyze(out):
    plan = read(out/'PLAN.json')
    frozen = read(out/'FREEZE.json')
    for p in frozen['files']:
        if Path(p['path']).name in ('PLAN.json', 'MODEL_CONTRACT.json', 'NATIVE_BUILD.json', 'NATIVE_BUILD_V02.json', 'RUNTIME_MANIFEST.json', 'COUNTER_SEMANTICS.md'):
            require(sha(Path(p['path'])) == p['sha256'], 'frozen analysis input differs')
    manifest=verify_runtime_manifest(out)
    blocks = [read(p) for p in sorted((out/'blocks').glob('*.json'))]
    contract = read(out/'MODEL_CONTRACT.json')['families']
    tasks = {f:{t['id']:t for t in plan['panel'][f]} for f in FAMILIES}
    for block in blocks:
        for record in block.get('records', []):
            slug = hashlib.sha256(record['slot'].encode()).hexdigest()[:24]
            p = out/'runs/formal'/record['family']/block['block']['id']/'requests'/slug/'RECORD.json'
            require(read(p) == record and read(p.parent/'COMPLETED.json')['record_sha256'] == sha(p), 'native record/export mismatch')
            route=next(r for r in manifest['routes'] if (r['family'],r['arm'])==(record['family'],record['condition']))
            require(record['runtime_route']==route, 'record family/arm runtime differs')
            build=read(out/route['build_manifest'])
            identity=dict(native_source=build['source_inventory_sha256'],server=build['server_sha256'],
                          DLLs=build['numerical_DLL_sha256'],models=contract[record['family']]['models'],
                          contract_sha256=sha(out/'MODEL_CONTRACT.json'))
            identity_hash=digest(json.dumps(identity,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())
            require(record['source_identity_sha256']==identity_hash, 'selected runtime source identity differs')
            worker=p.parents[2]
            require(read(worker/'RUNTIME_ROUTE.json')==route and read(worker/'COMMAND.json')['command'][0]==str((out/'native/build/bin'/route['binary']).resolve()), 'worker executable selection differs')
            require(read(worker/'PROCESS.json')['pid']==record['pid']==read(worker/'MODULE_IDENTITY.json')['pid'], 'request process identity differs')
            body = read(p.parent/'REQUEST_STARTED.json')['body']
            task = tasks[record['family']][record['task']]
            require(body['prompt'] == task['prompt_ids'] and body['n_predict'] == 128 and body['cache_prompt'] is False, 'native request differs from frozen IDs/cap/cache contract')
            o = record['output']; ids = o['ids']; c = contract[record['family']]
            require(0 < len(ids) <= 128 and len(ids) == o['length'], 'invalid native output length')
            require(all(type(i) is int and 0 <= i < c['vocabulary_tokens'] for i in ids), 'invalid native output ID')
            flags = [i in c['eog'] for i in ids]
            require(o['eog_flags'] == flags and not any(flags[:-1]) and o['terminal_id'] == ids[-1], 'invalid native EOG/terminal contract')
            require(o['stop_reason'] == ('EOG' if flags[-1] else 'CAP') and (flags[-1] or len(ids) == 128), 'invalid endpoint stop contract')
            require(o['cached_tokens'] == 0 and o['truncated'] is False and record['response']['tokens'] == ids, 'cache/truncation/raw-response mismatch')
    result = analyze_blocks(plan, blocks)
    sessions = [read(out/f'SESSION-{i}.json') for i in range(SESSIONS) if (out/f'SESSION-{i}.json').exists()]
    complete = len(sessions) == SESSIONS and all((out/f'SESSION-{i}-COMPLETE.json').exists() for i in range(SESSIONS))
    spacing = complete and sessions[-1]['epoch']-sessions[0]['epoch'] >= 86400
    if spacing:
        spacing = all(sessions[i]['epoch']-read(out/f'SESSION-{i-1}-COMPLETE.json')['epoch'] >= 3600 for i in range(1,SESSIONS))
    result['time_block_gate'] = 'PASS' if spacing else 'PENDING_OR_BLOCKED'
    if not spacing:
        for row in result['comparisons']: row['estimate']=None; row['status']='TIME_BLOCK_NOT_ADMITTED'
    result['new_gpu_results_bundled_with_code'] = False
    return result


def replace_once(s, old, new):
    require(s.count(old) == 1, 'source patch anchor mismatch: ' + old)
    return s.replace(old, new)


def patch_e1(capture: Path, replay: Path, out: Path):
    """Emit diagnostic-only source replacements; do not modify paid runtime."""
    a, b = capture.read_bytes(), replay.read_bytes()
    require(blob(a) == CAPTURE_BLOB and blob(b) == REPLAY_BLOB, 'exact PR98 source required')
    require(not out.exists(), 'new diagnostic patch output required'); out.mkdir(parents=True)
    s = a.decode(); helper = '''inline int setting(const char * name,int fallback,int maximum) {
    const char * p=std::getenv(name);if(!p)return fallback;
    char * end=nullptr;long value=std::strtol(p,&end,10);
    if(!*p||*end||value<0||value>maximum)throw std::runtime_error("invalid E1 capture selector");
    return int(value);
}
inline int layer(){return setting("HS_E1_LAYER",0,255);}
inline bool selected_phase(){return setting("HS_E1_PHASE",0,1)==(hsc::w.prefill?0:1);}
'''
    s = replace_once(s, 'inline bool opened[2]', helper+'inline bool opened[2]')
    s = replace_once(s, 'if(!enabled())return false;', 'if(!enabled()||!selected_phase())return false;')
    for old in ('kq-0', 'kq_soft_max-0', 'kqv-0'):
        s = replace_once(s, '"'+old+'"', '(std::string("'+old[:-1]+'")+std::to_string(layer())).c_str()')
    s = replace_once(s, 'q->ne[1]<=1 || q->ne[1]>4 || q->ne[3]!=1',
                     'q->ne[1]<1 || q->ne[1]>4 || q->ne[3]!=1 || q->ne[1]!=setting("HS_E1_Q",1,4) || t->src[0]->ne[1]<setting("HS_E1_MIN_KEY",0,1024)')
    s = replace_once(s, '{"layer",0}', '{"layer",layer()},{"captured_key_extent",t->src[0]->ne[1]}')
    s = s.replace('#include <cstring>', '#include <cstring>\n#include <cstdlib>\n#include <string>')
    r = replace_once(b.decode(), 'q->ne[1]<2', 'q->ne[1]<1')
    r = replace_once(r, 'const bool pq=arm=="PQ",qb=arm=="QB";', 'const bool pq=arm=="PQ" && width>1,qb=arm=="QB" && width>1;')
    (out/'capture95.h').write_text(s, encoding='utf-8', newline='\n')
    (out/'replay95.cpp').write_text(r, encoding='utf-8', newline='\n')
    save(out/'PATCH_RECEIPT.json', dict(baseline_commit=BASELINE_COMMIT, original_capture_blob=CAPTURE_BLOB,
                                      original_replay_blob=REPLAY_BLOB, outputs=[pin(out/'capture95.h'),pin(out/'replay95.cpp')],
                                      compiled=False, new_gpu_forwards=0, paid_runtime_must_remain_unchanged=True))


def canonical(root, meta):
    require(meta['type'] == 0 and len(meta['ne']) == len(meta['nb']) == 4, 'F32 four-dimensional tensor required')
    path=(root/meta['file']).resolve()
    require(path.is_relative_to(root.resolve()), 'tensor path escapes snapshot root')
    b=path.read_bytes(); ne,nb=meta['ne'],meta['nb']
    require(all(type(x) is int and x > 0 for x in ne) and all(type(x) is int and x >= 0 for x in nb), 'invalid shape/stride')
    result=bytearray()
    for i3 in range(ne[3]):
        for i2 in range(ne[2]):
            for i1 in range(ne[1]):
                for i0 in range(ne[0]):
                    off=sum(x*y for x,y in zip((i0,i1,i2,i3),nb))
                    require(off+4 <= len(b), 'truncated strided tensor')
                    result.extend(b[off:off+4])
    return bytes(result)


def compare_e1(snapshot, replay_root):
    """CPU own-path gate and numerical correspondence on actual native files."""
    m=read(snapshot/'snapshot.json'); stages=('QK','softmax','AV'); values={}; hashes={}
    for arm in ('MQ','PQ','QB'):
        values[arm]=[]
        for repeat in range(2):
            d=replay_root/f'{arm}-r{repeat}'; receipt=read(d/'REPLAY.json')
            require(receipt['arm'] == arm and receipt['backend']=='CUDA0', 'wrong runtime/arm')
            require(set(receipt['fixed_inputs']) == {'Q','K','V','mask'}, 'missing fixed input receipt')
            require(all(x['readback_bitwise_equal'] for x in receipt['fixed_inputs'].values()), 'replay input readback failed')
            for name in ('Q','K','V','mask'):
                require(all(receipt['fixed_inputs'][name][k] == m[name][k] for k in ('ne','nb','type')), 'replay input geometry changed')
            values[arm].append({s:(d/(s+'.bin')).read_bytes() for s in stages})
            hashes[f'{arm}-r{repeat}']={p.name:sha(p) for p in d.iterdir() if p.is_file()}
    own={s:canonical(snapshot,m['native_'+s])==values['MQ'][0][s] for s in stages}
    repeats={a:values[a][0]==values[a][1] for a in values}
    qualified=all(own.values()) and all(repeats.values())
    return dict(own_path=own,repeatability=repeats,qualification='PASS' if qualified else 'NOT_ADMITTED',
                PQ_QB_bitwise={s:values['PQ'][0][s]==values['QB'][0][s] for s in stages} if qualified else None,
                MQ_QB_bitwise={s:values['MQ'][0][s]==values['QB'][0][s] for s in stages} if qualified else None,
                geometry={k:m[k] for k in ('layer','phase','q_occupancy')}, artifacts=hashes,
                kernel_reduction_tree='UNKNOWN', paid_cost=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='command',required=True)
    p=sub.add_parser('prepare')
    for name in ('results','legacy','runtime','out'): p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--holdout',type=Path)
    r=sub.add_parser('run-session'); r.add_argument('--out',type=Path,required=True); r.add_argument('--repo',type=Path,required=True)
    r.add_argument('--freeze-commit',required=True); r.add_argument('--registration',required=True); r.add_argument('--session',type=int,required=True)
    a=sub.add_parser('analyze'); a.add_argument('--out',type=Path,required=True)
    e=sub.add_parser('patch-e1')
    for name in ('capture','replay','out'):e.add_argument('--'+name,type=Path,required=True)
    c=sub.add_parser('compare-e1'); c.add_argument('--snapshot',type=Path,required=True); c.add_argument('--replays',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='prepare':prepare(args.results,args.legacy,args.runtime,args.out,args.holdout)
    elif args.command=='run-session':run_session(args.out.resolve(),args.repo,args.freeze_commit,args.registration,args.session)
    elif args.command=='analyze':print(json.dumps(analyze(args.out.resolve()),indent=2))
    elif args.command=='patch-e1':patch_e1(args.capture,args.replay,args.out)
    else:print(json.dumps(compare_e1(args.snapshot,args.replays),indent=2))


if __name__=='__main__':main()
