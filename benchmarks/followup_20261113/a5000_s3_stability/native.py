"""Bounded successor controller for the unchanged S3 native JOB OUT ABI.

Only this campaign's journal and scratch are writable. Original readers, native
arithmetic, clocks, qualification fixtures and historical journals are reused.
"""
import argparse
from contextlib import ExitStack
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time

from adapter import ELF_SHA, MODEL_SHA, read, need


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda: f.read(8 * 1024**2), b''):
            h.update(part)
    return h.hexdigest()


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n'); f.flush(); os.fsync(f.fileno())
    tmp.replace(path)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


class Budget:
    """No inheritance, refunds or implicit retries; one controller holds the lock."""
    def __init__(self, path):
        self.path = Path(path)

    def entries(self):
        return [json.loads(s) for s in self.path.read_text().splitlines()] if self.path.exists() else []

    def event(self, value):
        with self.path.open('a') as f:
            f.write(json.dumps({'utc': utc(), **value}, allow_nan=False) + '\n')
            f.flush(); os.fsync(f.fileno())

    def reserve(self, cohort, worker):
        rows = self.entries()
        reserved = [x for x in rows if x['event'] == 'RESERVE']
        need(not any(x['worker_id'] == worker['worker_id'] for x in reserved), 'Never relaunch a reserved worker')
        for name, ceiling, row_ceiling in [('ALL', 468, 149760), ('R', 292, 93440), ('H', 176, 56320)]:
            selected = [x for x in reserved if name == 'ALL' or x['cohort'] == name]
            if name == 'ALL' or name == cohort:
                need(sum(x['requests'] for x in selected) + worker['requests'] <= ceiling, 'Request ceiling')
                need(sum(x['reserved_rows'] for x in selected) + worker['reserved_rows'] <= row_ceiling, 'Row ceiling')
        self.event(dict(event='RESERVE', cohort=cohort, **worker,
                        operation_ids=[worker['worker_id'] + ':' + x for x in worker['roles']]))


def prune_states(directory, keep):
    """Discard only new successfully compared state files; retain every F32 output."""
    removed = []
    for path in sorted(Path(directory).rglob('sequence.bin')):
        if path in keep:
            continue
        removed.append(dict(path=str(path), bytes=path.stat().st_size))
    if not removed:
        return
    write(Path(directory) / 'DISPOSAL.json', dict(utc=utc(), policy='New compared states only; vectors and proofs retained', files=removed))
    for item in removed:
        Path(item['path']).unlink()


class Campaign:
    def __init__(self, config):
        self.c = read(config)
        self.root = Path(self.c['output_root'])
        self.root.mkdir(parents=True, exist_ok=True)
        self.budget = Budget(self.root / 'requests.jsonl')
        self.stack = ExitStack()
        original = Path(self.c['original_source'])
        sys.path.insert(0, str(original / 'execution_s3_v1'))
        import verify
        from host import resource
        self.verify, self.resource = verify, resource
        self.profile = read(self.c['state_profile'])
        self.modules = {str(Path(p).resolve()): digest for p, digest in read(self.c['compiled_closure'])['files'].items()}
        self.modules.update({str(Path(x['path']).resolve()): x['sha256'] for x in self.c['executables'].values()})

    def preflight(self):
        c = self.c
        need(len(c['source_commit']) == 40, 'Immutable public successor source freeze required')
        need(c['authority']['new_requests_authorized'] is True, 'Successor authority required')
        need(c['authority']['planned'] == 444 and c['authority']['ceiling'] == 468, 'Frozen new budget')
        need(c['model']['sha256'] == MODEL_SHA and sha(c['model']['path']) == MODEL_SHA, 'Exact full model')
        for key in ('R', 'model'):
            need(sha(c['executables'][key]['path']) == ELF_SHA[key], 'Original ELF: ' + key)
        need(sha(c['state_profile']) == c['state_profile_sha256'], 'Original state profile')
        need(sha(c['S1_certificate']) == c['S1_certificate_sha256'], 'Retained unchanged S1 evidence')
        need(read(c['S1_certificate'])['status'] == 'ALL_REQUIRED_S1_GATES_PASSED', 'Retained qualification')
        for path, digest in self.modules.items():
            need(sha(path) == digest, 'Original compiled dependency: ' + path)
        for path, digest in c['successor_files'].items():
            need(sha(path) == digest, 'Successor source/input freeze: ' + path)
        for path, digest in c['protected_files'].items():
            need(sha(path) == digest, 'Old artifact changed before launch')
        need(read(c['exposure_report'])['status'] == 'REVIEWED_EXPOSURE_UNKNOWN', 'H exposure review required')
        need(c['storage_bound_bytes'] <= 80 * 1024**3, '80 GiB capture bound')
        return self.resource(c)

    def launch(self, panel, worker, job, panel_start):
        c = self.c
        need(not (self.root / 'STOP_REQUESTED').exists(), 'Stop requested')
        self.resource(c)
        used = sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file() and not p.is_symlink())
        need(used + 10 * 1024**3 <= 80 * 1024**3, 'Scratch plus next-worker 10 GiB bound exceeds 80 GiB')
        plan = Path(c['plans']) / panel
        need(sha(plan / worker['job']) == worker['job_sha256'], 'Frozen native job')
        exe = c['executables'][worker['executable']]['path']
        need(sha(exe) == ELF_SHA[worker['executable']], 'Native ELF changed')
        for path, digest in c['successor_files'].items():
            need(sha(path) == digest, 'Controller/input source changed')
        out = self.root / panel / 'workers' / worker['worker_id']
        if out.exists() and self.resuming:
            need(read(out / 'JOB.json') == job and read(out / 'WORKER.json') == worker, 'Exact retained first reference')
            host = read(out / 'HOST.json')
            need(host['returncode'] == 0 and host['error'] is None, 'Only known successful native exit can be reused')
            need(read(out / 'native/result.json')['status'] == 'COMPLETE' and (out / 'ACTUAL_MODULES.private.json').exists()
                 and (out / 'ACTUAL_REQUESTS.json').exists(), 'Complete original native evidence')
            events = self.budget.entries()
            exits = [x for x in events if x['event'] == 'EXIT' and x['worker_id'] == worker['worker_id']]
            if not exits:
                self.budget.event(dict(event='EXIT', cohort=panel[0], worker_id=worker['worker_id'], **host,
                                       recovery='Original successful HOST/native evidence; controller UTC-key bookkeeping failure; no new launch'))
            else:
                need(len(exits) == 1 and all(exits[0][k] == v for k, v in host.items()), 'Recorded successful exit must match retained HOST')
            return out
        need(not out.exists(), 'Preserve previous worker')
        out.mkdir(parents=True)
        write(out / 'JOB.json', job); write(out / 'WORKER.json', worker)
        self.budget.reserve(panel[0], worker)
        formal = worker['stage'] == 'formal'
        if formal:
            need((self.root / panel / 'QUALIFIED.json').exists(), 'Full panel qualification before timing')
        # These ABI fields refer to actual retained S1 evidence and this new
        # frozen source/input inventory, never to a historical spending grant.
        grant = dict(schema='hs.strong.native-reservation.v1', phase='S3' if formal else 'S3_QUAL',
                     GPU_authorized=True, complete_F0_readback=True, complete_F2_readback=True,
                     prior_S1_qualified=True, budget_reserved=True,
                     private_gpu_uuid=c['gpu_uuid'], job_sha256=sha(out / 'JOB.json'),
                     successor_authority=c['authority'], successor_source_commit=c['source_commit'],
                     retained_S1_certificate_sha256=c['S1_certificate_sha256'])
        if formal:
            grant.update(numerically_qualified=True, new_root_oracles_frozen=True)
        write(out / 'GRANT.private.json', grant)
        env = dict(os.environ, CUDA_VISIBLE_DEVICES=c['gpu_uuid'], CUDA_DEVICE_ORDER='PCI_BUS_ID',
                   OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='1', HS_STRONG_GPU_ADMISSION_FILE=str(out / 'GRANT.private.json'))
        if worker['arm'] == 'R':
            env.pop('GGML_CUDA_DISABLE_GRAPHS', None)
        argv = [c['executables']['guard']['path'], '--parent', str(os.getpid()), '--',
                'taskset', '-c', c['native_cpu_affinity'], exe, str(out / 'JOB.json'), str(out / 'native')]
        begin = time.monotonic_ns(); process = None; error = None
        try:
            with (out / 'stdout.log').open('xb') as stdout, (out / 'stderr.log').open('xb') as stderr, (out / 'RESOURCE.private.jsonl').open('x') as telemetry:
                process = subprocess.Popen(argv, env=env, stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL, start_new_session=True)
                write(out / 'LAUNCH.private.json', dict(pid=process.pid, argv=argv, utc=utc(), boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                                                       launch_begin_monotonic_ns=begin, executable_sha256=sha(exe)))
                while process.poll() is None:
                    sample = self.resource(c, process.pid)
                    telemetry.write(json.dumps(sample) + '\n'); telemetry.flush()
                    time.sleep(2)
                need(process.returncode == 0, 'Native nonzero exit; inspect retained stderr')
            result = read(out / 'native/result.json')
            need(result['status'] == 'COMPLETE', 'Incomplete native result')
            actual = result.get('native_module_maps', result.get('modules_after'))
            need(actual is not None, 'Native loaded modules missing')
            checked = {}
            for path in actual:
                if path == 'linux-vdso.so.1': continue
                resolved = str(Path(path).resolve())
                need(resolved in self.modules and sha(resolved) == self.modules[resolved], 'Actual loaded module changed: ' + path)
                checked[resolved] = self.modules[resolved]
            write(out / 'ACTUAL_MODULES.private.json', checked)
            requests = []
            for entry in job['inputs']:
                receipt = read(out / 'native' / entry['name'] / 'receipt.json')
                requests.append(dict(name=entry['name'], prompt_tokens=len(entry['input']['prompt_ids']),
                                     emitted_tokens=len(receipt['ids']), actual_forward_rows=len(entry['input']['prompt_ids']) + len(receipt['ids']) - 1))
            need(sum(x['actual_forward_rows'] for x in requests) <= worker['reserved_rows'], 'Actual rows exceed reservation')
            write(out / 'ACTUAL_REQUESTS.json', requests)
        except BaseException as exc:
            error = str(exc)
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait()
            raise
        finally:
            host = dict(launch_begin_monotonic_ns=begin, exit_observed_monotonic_ns=time.monotonic_ns(),
                        returncode=process.returncode if process is not None else None, error=error,
                        wall_s=(time.monotonic_ns() - begin) / 1e9, utc=utc())
            write(out / 'HOST.json', host)
            self.budget.event(dict(event='EXIT', cohort=panel[0], worker_id=worker['worker_id'], **host))
        return out

    def panel(self, panel, resume=False):
        c = self.c; destination = self.root / panel
        manifest = read(Path(c['plans']) / panel / 'MANIFEST.json')
        self.resuming = resume
        if resume:
            need(read(destination / 'STATUS.json')['status'] == 'STOPPED', 'Inspect stopped panel before explicit continuation')
        else:
            need(not destination.exists(), 'Panel already started; inspect evidence before continuation')
            destination.mkdir()
        xs = manifest['roots']['inputs']
        self.stack = ExitStack()
        started = time.monotonic()
        try:
            for path in [self.root / 'controller.lock', Path(c['activity_lock']), Path(c['gpu_lock'])]:
                lock = self.stack.enter_context(path.open('a+'))
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            write(destination / 'PREFLIGHT.private.json', self.preflight())
            if panel == 'R2':
                first = read(self.root / 'R1' / 'STATUS.json')
                need(first['status'] == 'COMPLETE', 'R1 complete prerequisite')
                need((dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(first['utc'])).total_seconds() >= 86400, '24h date separation')
            if resume:
                write(destination / ('RESUME-' + str(time.monotonic_ns()) + '.json'), dict(utc=utc(), source_commit=c['source_commit'],
                      reason='Continue only unstarted registered workers; reuse proven successful native exits; failed attempts stay charged'))
            else:
                write(destination / 'START.json', dict(utc=utc(), panel=panel, deployment='Original native ELF and full compiled closure', source_commit=c['source_commit']))
            references = read(self.root / 'R1' / 'ORACLES.json') if panel == 'R2' else {}
            pending = {}; tapes = {}
            for w in manifest['workers']:
                if w['stage'] != 'qualification': continue
                slot = w['slot']; name = f'new-root{slot:02d}'
                service = dict(id=name, input=xs[slot])
                out = self.launch(panel, w, read(Path(c['plans']) / panel / w['job']), started)
                native = out / 'native'
                if w['arm'] == 'R':
                    if w['roles'] == ['reference'] and w['worker_id'].endswith('R0'):
                        pending[slot] = str(native)
                    else:
                        if self.resuming and (out / 'CHECKED.json').exists():
                            proof = read(out / 'CHECKED.json')
                            need(proof[0]['input_id'] == name and proof[0]['endpoint'] == read(native / name / 'receipt.json'), 'Retained complete repeated-R proof/receipt binding')
                            need((native / 'DISPOSAL.json').exists(), 'Intermediate repeat states were intentionally disposed after checking')
                        else:
                            proof = self.verify.repeated_R(pending[slot], native, service, self.profile)
                            write(out / 'CHECKED.json', proof)
                            prune_states(native, set())
                        references[str(slot)] = pending[slot]
                else:
                    if self.resuming and (out / 'CHECKED.json').exists():
                        proof = read(out / 'CHECKED.json')
                        need(proof['heavy_receipt_sha256'] == sha(native / (name + '-heavy') / 'receipt.json') and
                             proof['clean_receipt_sha256'] == sha(native / (name + '-clean') / 'receipt.json'), 'Retained complete bridge proof/receipt binding')
                    else:
                        proof = self.verify.complete_bridge(native, name + '-heavy', native, name + '-clean',
                                                            references[str(slot)], service, self.profile, w['arm'], out / 'checker-view')
                        write(out / 'CHECKED.json', proof)
                    heavy = read(native / (name + '-heavy') / 'receipt.json')
                    tapes[f'{slot}:{w["arm"]}'] = heavy['semantic_tape_sha256']
                    prune_states(native, {native / (name + '-clean') / 'post-service-terminal/sequence.bin'})
                    if w['arm'] == 'C' and slot not in (0, 6):
                        ref = Path(references[str(slot)])
                        receipt = read(ref / name / 'receipt.json')
                        final = len(xs[slot]['prompt_ids']) + len(receipt['ids']) - 1
                        prune_states(ref, {ref / name / 'captures' / str(final) / 'sequence.bin'})
                write(destination / 'STATUS.json', dict(status='QUALIFYING', worker=w['worker_id'], utc=utc()))
            if panel == 'R2':
                old = read(self.root / 'R1' / 'TAPES.json'); old.update(tapes); tapes = old
            write(destination / 'ORACLES.json', references); write(destination / 'TAPES.json', tapes)
            write(destination / 'QUALIFIED.json', dict(status='ALL_REGISTERED_ROOT_BRIDGES_PASSED', roots=sorted(pending), utc=utc(),
                   retention='Full R0 oracle trajectories only for fixed slots 0 and 6; all F32 outputs retained; other heavy KV removed after strict comparisons'))
            rows = []
            for w in manifest['workers']:
                if w['stage'] != 'formal': continue
                slot = w['slot']; name = f'new-root{slot:02d}'
                job = read(Path(c['plans']) / panel / w['job'])
                out = self.launch(panel, w, job, started)
                proof = []
                for ordinal, role in enumerate(w['roles']):
                    path = out / 'native' / role
                    proof.append(self.verify.clean(path, references[str(slot)], dict(id=name, input=xs[slot]),
                                                   self.profile, w['arm'], tapes[f'{slot}:{w["arm"]}']))
                    legacy = dict(w, block=w['round'] - 1, operations=[dict(operation_id=w['worker_id'] + ':' + r) for r in w['roles']])
                    row = self.verify.row(legacy, ordinal, path, job, read(out / 'HOST.json'))
                    row.update(cohort=panel[0], day=manifest['day'], round=w['round'], pair_id=w['pair_id'], root_id=xs[slot]['id'])
                    rows.append(row)
                write(out / 'CHECKED.json', proof)
                write(destination / 'ROWS.json', rows)
                write(destination / 'STATUS.json', dict(status='MEASURING', worker=w['worker_id'], checked_requests=len(rows), utc=utc()))
            for path, digest in c['protected_files'].items():
                need(sha(path) == digest, 'Protected historical artifact changed')
            write(destination / 'STATUS.json', dict(status='COMPLETE', utc=utc(), checked_requests=len(rows), panel_wall_s=time.monotonic() - started))
        except BaseException as exc:
            write(destination / 'STATUS.json', dict(status='STOPPED', utc=utc(), error=str(exc), panel_wall_s=time.monotonic() - started))
            raise
        finally:
            self.stack.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--panel', choices=['R1', 'R2', 'H1'])
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    campaign = Campaign(args.config)
    if args.preflight: print(json.dumps(campaign.preflight(), indent=2))
    else:
        need(args.panel is not None, 'Panel required')
        campaign.panel(args.panel, args.resume)
