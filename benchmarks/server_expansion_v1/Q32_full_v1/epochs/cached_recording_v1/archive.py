"""Terminal-only full text/commitment export and descriptive statistics; zero GPU.

Raw binary captures, including licensed operand weights, stay on the authorized
host. Every original text and binary byte commitment is retained. Public resource
evidence omits unrelated process/device identifiers. A hash is not a numerical
comparison or independent access to the private capture payloads.
"""
from pathlib import Path
from collections import defaultdict
import argparse, hashlib, json, lzma, os, re, time
from build import read, sha, save

def alive(x):
    try:
        raw = Path(f"/proc/{x['pid']}/stat").read_text()
        s = raw[raw.rfind(')') + 2:].split()
        return s[19] == x['start_ticks'] and s[0] != 'Z'
    except FileNotFoundError:
        return False

def analysis(w):
    complete = w / 'panel-01/COMPLETE.json'
    if not complete.exists():
        return dict(complete=False, performance_claim=False, scope='No complete eligible descriptive panel; preserve all partial/failure costs')
    plan = read(w / 'panel-01/PLAN.json')
    rows = []
    for worker in plan['workers']:
        run = w / 'panel-01/runs' / worker['id']
        job = read(w / 'panel-01' / worker['job'])
        for x in job['inputs']:
            if not x['name'].startswith('root-'):continue
            r = read(run / 'native' / x['name'] / 'receipt.json')
            if 'service_seconds' in r:
                service = float(r['service_seconds'])
            elif 'request_wall_s' in r:
                service = float(r['request_wall_s'])
            elif 'request_s' in r:
                service = float(r['request_s'])
            elif 'service_s' in r:
                service = float(r['service_s'])
            elif 'wall_s' in r:
                service = float(r['wall_s'])
            else:
                raise RuntimeError('Unknown native service cost schema: ' + ','.join(r))
            rows.append(dict(round=worker['round'], position=worker['position'], arm=worker['arm'], root=x['input']['id'], service_s=service, receipt_sha256=sha(run / 'native' / x['name'] / 'receipt.json')))
    assert len(rows) == 96
    totals = defaultdict(float)
    for x in rows:
        totals[x['arm']] += x['service_s']
    return dict(complete=True, descriptive_only=True, rows=rows, total_service_s=dict(totals), scope='Exposed4 roots x4 rounds, partial balanced six-arm deployment; model size/precision/recipe all changed; no population confirmation or size-only attribution')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--work', type=Path, required=True)
    a = p.parse_args()
    (w, r) = (a.work, a.root)
    while not (w / 'PIPELINE_LAUNCH_07.private.json').exists():
        time.sleep(2)
    launched = read(w / 'PIPELINE_LAUNCH_07.private.json')['processes']
    while any((alive(launched[n]) for n in ('qualification-07', 'finish-06'))):
        time.sleep(10)
    while not (w / 'PIPELINE_COORDINATOR_CLOSED07.private.json').exists():
        time.sleep(1)
    import subprocess
    cfg = read(w / 'config.private.json')
    while True:
        active = False
        query = subprocess.run(['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True)
        for line in query.stdout.splitlines():
            (uuid, pid) = [x.strip() for x in line.split(',')]
            if uuid != cfg['gpu_uuid']:
                continue
            try:
                own = b'q32-q4-full' in Path(f'/proc/{pid}/cmdline').read_bytes()
            except FileNotFoundError:
                own = False
            active = active or own
        if not active:
            break
        time.sleep(5)
    for phase in ('qualification-07', 'closure-07'):
        d = w / phase / 'control'
        if d.exists():
            while not (d / 'GUARD_STOPPED.private.json').exists() and (not (d / 'PAUSE.json').exists()):
                time.sleep(1)
    out = w / 'export-09'
    out.mkdir()
    started = time.monotonic()
    texts = []
    binary = []
    other = []
    resources = []

    def sanitize(s):
        s = s.replace(str(r), '$HS_ROOT').replace(str(Path.home()), '$HOME')
        s = re.sub('GPU-[0-9a-fA-F-]{36}', '<allocated-or-redacted-GPU>', s)
        s = re.sub('\\b(?:10|192\\.168)\\.\\d+(?:\\.\\d+){1,2}\\b', '<private-network>', s)
        s = re.sub('/home/[A-Za-z0-9_.-]+', '$HOME_USER', s)
        s = re.sub('GPU-[0-9a-fA-F-]{8,}', '<allocated-or-redacted-GPU>', s)
        s = re.sub('\\b192\\.168(?:\\.\\d{1,3}){1,2}\\b', '<private-network>', s)
        assert not re.search('/home/[a-z]|GPU-[a-fA-F0-9]{8}|192\\.168\\.\\d', s)
        return s
    groups = [('work', w)] + [(p.name, p) for p in sorted(r.glob('q32-q4-full-*')) if p.is_dir() and p != w]
    payload = out / 'TEXT_RECORDS.jsonl.xz'
    with lzma.open(payload, 'xb', preset=9) as compressed:
        for (alias, directory) in groups:
            for f in sorted(directory.rglob('*')):
                if not f.is_file() or any((x.startswith('export-') for x in f.relative_to(directory).parts)) or '__pycache__' in f.parts:
                    continue
                path = alias + '/' + str(f.relative_to(directory))
                size = f.stat().st_size
                if f.suffix in ('.bin', '.f32'):
                    binary.append(dict(path=path, bytes=size, sha256=sha(f)))
                    continue
                if f.name == 'PAUSE.json' or any((k in f.name for k in ('RESOURCE_GUARD', 'GUARD_BASELINE', 'LAUNCH', 'PIPELINE_'))):
                    if f.name == 'RESOURCE_GUARD.private.jsonl':
                        samples = []
                        for line in f.read_text().splitlines():
                            x = json.loads(line)
                            selected = [g for g in x['gpu'] if g['device'] == cfg['gpu_uuid']]
                            samples.append(dict(epoch=x['epoch'], selected_foreign_processes=sum((not g['own'] for g in selected)), foreign_cpu_on_assigned_cores=x['foreign_cpu_on_assigned_cores'], event_kinds=[e['kind'] for e in x['events']]))
                        resources.append(dict(path=path, raw_bytes=size, raw_sha256=sha(f), samples=samples))
                    else:
                        other.append(dict(path=path, bytes=size, sha256=sha(f), scope='Private control provenance, no public process identities'))
                    continue
                if f.suffix not in ('.json', '.jsonl', '.log', '.py', '.hpp', '.cpp', '.inc', '.h', '.md', '.d', '.map'):
                    other.append(dict(path=path, bytes=size, sha256=sha(f)))
                    continue
                raw = f.read_bytes()
                try:
                    source = raw.decode('utf8')
                except UnicodeDecodeError:
                    other.append(dict(path=path, bytes=size, sha256=hashlib.sha256(raw).hexdigest()))
                    continue
                text = sanitize(source)
                b = text.encode()
                texts.append(dict(path=path, raw_bytes=size, raw_sha256=hashlib.sha256(raw).hexdigest(), public_bytes=len(b), public_sha256=hashlib.sha256(b).hexdigest()))
                compressed.write((json.dumps(dict(path=path, text=text), ensure_ascii=True, separators=(',', ':')) + '\n').encode())
    save(out / 'TEXT_INDEX.json', dict(files=texts))
    save(out / 'BINARY_CAPTURE_INDEX.json', dict(files=binary, raw_payloads_private=True))
    save(out / 'OTHER_PRIVATE_INDEX.json', dict(files=other))
    save(out / 'RESOURCE_CHECKED.json', dict(records=resources, sampling_s=5, limitations='No exclusion of all brief/shared-interconnect interference'))
    bundle = dict(file=payload.name, bytes=payload.stat().st_size, sha256=sha(payload), records=len(texts), compression='xz/LZMA2 preset9,64MiB dictionary')
    parts = []
    with payload.open('rb') as f:
        i = 0
        while True:
            b = f.read(384 * 1024)
            if not b:
                break
            p = out / f'TEXT_RECORDS.part-{i:04d}.xz'
            p.write_bytes(b)
            parts.append(dict(file=p.name, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()))
            i += 1
    bundle['ordered_parts'] = parts
    save(out / 'BUNDLE.json', bundle)
    inherited = read(w / 'INHERITED_ACCOUNTING.json')
    xs = [json.loads(x) for x in (w / 'ledger.jsonl').read_text().splitlines()]
    reserved = [x for x in xs if x['event'] == 'RESERVE']
    req = inherited['requests'] + sum((x['requests'] for x in reserved))
    rows = inherited['rows'] + sum((x['rows'] for x in reserved))
    save(out / 'COSTS.json', dict(cumulative_Q32_requests=req, request_ceiling=512, cumulative_Q32_reserved_rows=rows, row_ceiling=2000000, old_Q32_diagnostics_included=json.loads(sanitize(json.dumps(inherited))), prior_8B_ledger_unchanged=True, native_failures=sum((x['event'] == 'FAILED' for x in xs)), raw_binary_files=len(binary), raw_binary_bytes=sum((x['bytes'] for x in binary)), archive_wall_s=time.monotonic() - started, scope='Reservations include failures, no refunds; projection rows are labeled distinctly; no invented GPU kernel-time/energy total'))
    try:
        stats = analysis(w)
        save(out / 'ANALYSIS.json', stats)
    except BaseException as e:
        save(out / 'ANALYSIS_FAILURE.json', dict(error=str(e), no_performance_claim=True))
    with lzma.open(payload, 'rt') as f:
        count = 0
        for line in f:
            x = json.loads(line)
            item = texts[count]
            assert x['path'] == item['path'] and hashlib.sha256(x['text'].encode()).hexdigest() == item['public_sha256']
            count += 1
    assert count == len(texts)
    save(out / 'LOCAL_READBACK.json', dict(passed=True, text_records=count, native_requests=0, public_remote_readback='PENDING_UPLOAD', scope='Full sanitized text byte replay; private binary hashes are not independent numerical verification'))
    save(out / 'EXPORT_COMPLETE.json', dict(passed=True, bytes=bundle['bytes'], parts=len(parts), raw_binary_bytes=sum((x['bytes'] for x in binary)), scope='No model weights, native payloads, allocation UUID or unrelated company information published'))
    print('Q32_TERMINAL_EXPORT_COMPLETE', json.dumps(bundle), flush=True)
if __name__ == '__main__':
    main()
