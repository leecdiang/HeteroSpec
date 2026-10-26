"""CPU-only restore, byte audit and relocation of the PR147 delivery kit.

No subcommand starts a native executable or performs inference.
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import zipfile

P = pathlib.Path


def filesystem_path(p):
    """Use Windows extended paths for deep archived source filenames."""
    p = P(p).resolve()
    if os.name != 'nt' or str(p).startswith('\\\\?\\'):
        return p
    s = str(p)
    return P('\\\\?\\UNC\\' + s[2:] if s.startswith('\\\\') else '\\\\?\\' + s)


def read(p):
    return json.loads(filesystem_path(p).read_bytes())


def sha(p):
    with filesystem_path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(p, value):
    with P(p).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2)
        f.write('\n')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def inside(root, name):
    # Reject both Windows and POSIX archive escape syntax on every host.
    p = pathlib.PurePosixPath(name)
    require(bool(name) and '\\' not in name and ':' not in name and
            not p.is_absolute() and '..' not in p.parts, 'unsafe member: ' + name)
    dest = (root / name).resolve()
    require(dest.is_relative_to(root.resolve()), 'escaped destination: ' + name)
    return dest


def check(p, item):
    p = filesystem_path(p)
    require(p.is_file() and p.stat().st_size == item['bytes'], 'size: ' + str(p))
    require(sha(p) == item['sha256'], 'SHA256: ' + str(p))


def extract(archive, dest, manifest_name='MEMBERS.json'):
    require(not dest.exists(), 'output must be new: ' + str(dest))
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'duplicate ZIP members')
        manifest = json.loads(z.read(manifest_name))
        if manifest_name == 'INDEX.json':
            manifest = manifest['files']
        require(set(names) == set(manifest) | {manifest_name}, 'unindexed ZIP member')
        for name in names:
            inside(dest, name)
        dest.mkdir(parents=True)
        for name, item in manifest.items():
            p = filesystem_path(inside(dest, name))
            require(z.getinfo(name).file_size == item['bytes'], 'ZIP size: ' + name)
            p.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as src, p.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            check(p, item)
        (dest / manifest_name).write_bytes(z.read(manifest_name))
    return manifest


def verify(root):
    manifest = read(root / 'MEMBERS.json')
    for name, item in manifest.items():
        check(inside(root, name), item)
    return len(manifest)


def vectors(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob('*.f32')}


def audit(root):
    count = verify(root)
    sel = read(root / 'selection.json')
    records = [read(root / 'qualification-v2' / (slot + '.json')) for slot in sel['slots']]
    r, pq, qb = records
    require([x['arm'] for x in records] == ['R', 'PQ', 'QB'], 'request arms')
    require(all(x['input_id'] == 'GSM8K/test/443' for x in records), 'input identity')
    require(all(x['capture'] for x in records), 'full capture required')
    old = read(root / 'HISTORICAL_R_ENDPOINTS.json')['endpoints'][r['input_id']]
    endpoint = ('ids', 'eog', 'length', 'terminal_id', 'stop_reason')
    require(all(all(x[k] == r[k] for k in endpoint) for x in records), 'R/PQ/QB endpoints')
    require(r['ids'] == old['ids'] and r['eog'] == old['eog_flags'] and
            all(r[k] == old[k] for k in ('length', 'terminal_id', 'stop_reason')), 'historical E2 endpoint')
    history = read(root / 'HISTORICAL_R_ENDPOINTS.json')
    require(sha(root / 'history/E2_s0_Qwen_b00.json') == history['source_sha256'], 'historical source binding')
    for k in ('cycles', 'target_final_kv', 'draft_final_kv'):
        require(pq[k] == qb[k], 'complete speculative state: ' + k)
    vv = [vectors(root / 'qualification-v2' / x['folder']) for x in records]
    require([len(x) for x in vv] == [128, 288, 288], 'missing full vocabulary vectors')
    require(vv[1] == vv[2], 'PQ/QB full vectors including rejected rows')
    for x in records:
        for p in (root / 'qualification-v2' / x['folder']).rglob('*.f32'):
            require(p.stat().st_size == 151936 * 4, 'truncated vocabulary: ' + str(p))
    for x in (pq, qb):
        prefix = 'hs_attn_query_batch-' if x['arm'] == 'QB' else 'hs_attention_q-'
        g = [v for v in x['geometry'] if v['name'].startswith(prefix)]
        require({int(v['name'].rsplit('-', 1)[1]) for v in g} == set(range(36)), 'target layers')
        require(all(v['ne'][1:3] == [1, 32] and v['ne'][3] == (4 if x['arm'] == 'QB' else 1)
                    and '5070' in v['device'] for v in g), 'recorded layout/placement')
    fixture = root / 'stage-fixture'
    for name, h in read(root / 'STAGE_ORIGIN.json')['registry'].items():
        require(sha(fixture / name) == h, 'historical fixture registry: ' + name)
    for s in ('QK', 'softmax', 'AV'):
        require((fixture / ('native_' + s + '.bin')).read_bytes() ==
                (root / 'stage-expected/MQ-r0' / (s + '.bin')).read_bytes(), 'MQ own path')
        require((root / 'stage-expected/PQ-r0' / (s + '.bin')).read_bytes() ==
                (root / 'stage-expected/QB-r0' / (s + '.bin')).read_bytes(), 'PQ/QB stage identity')
    receipts = read(root / 'STAGE_RESULT.json')
    require(receipts['status'] == 'PASS' and len(receipts['rows']) == 12 and
            all(all(x['stage_matches'].values()) for x in receipts['rows']), 'recorded stage replay')
    smoke = read(root / 'request-smoke/RESULT.json')
    require(smoke['status'] == 'PASS' and len(smoke['rows']) == 6, 'recorded HTTP smoke')
    for response in (root / 'request-smoke').glob('*/RESPONSE.json'):
        x = read(response)
        require(x['tokens'] == old['ids'] and x['tokens_predicted'] == old['length'] and
                x['stop_type'] == 'limit' and not x['truncated'] and old['stop_reason'] == 'CAP', 'HTTP endpoint/stop')
    q = read(root / 'qualification-v2-QUALIFICATION.json')
    require(q['status'] == 'PASS' and all(x['passed'] for x in q['checks']) and
            all(x['passed'] for x in q['historical_endpoint_checks']), 'archived qualification receipt')
    for name in ('INDEPENDENT_AUDIT.json', 'FINAL_VALIDATION.json'):
        require(read(root / 'recorded-results' / name)['status'] == 'PASS', 'archived audit: ' + name)
    formal_requests = 0
    with zipfile.ZipFile(root / 'recorded-results/NATIVE_RECORDS.zip') as z:
        members = json.loads(z.read('MEMBERS.json'))
        require(set(z.namelist()) == set(members) | {'MEMBERS.json'}, 'compact members')
        for name, item in members.items():
            data = z.read(name)
            require(len(data) == item['bytes'] and hashlib.sha256(data).hexdigest() == item['sha256'], 'compact bytes: ' + name)
            if name.startswith('sessions/') and name.endswith('/result.json'):
                session = json.loads(data)
                require(session['status'] == 'COMPLETE' and len(session['requests']) == 156, 'formal session')
                formal_requests += len(session['requests'])
    require(formal_requests == 936, 'formal request count')
    return dict(status='PASS', members=count, natural_input=r['input_id'], full_requests=3,
                vector_files=sum(map(len, vv)), pq_qb_equal_vectors=len(vv[1]),
                historical_http_requests=6, recorded_stage_replays=12,
                archived_qualification_checks=len(q['checks']), native_processes_started=0,
                compact_formal_requests=formal_requests,
                limit='CPU validation of preserved evidence; not a new GPU replay or independent machine reproduction')


def restore(index, out):
    spec = read(index)
    require(not out.exists(), 'restore output must be new')
    # Verify every part before creating output; concatenate outside extraction root.
    for item in spec['parts']:
        check(inside(index.parent, item['path']), item)
    out.mkdir(parents=True)
    archive = out / 'RTX_NATIVE_DELIVERY.zip'
    with archive.open('xb') as dst:
        for item in spec['parts']:
            with (index.parent / item['path']).open('rb') as src:
                shutil.copyfileobj(src, dst)
    check(archive, spec['archive'])
    extract(archive, out / 'kit')
    result = audit(out / 'kit')
    result['archive'] = spec['archive']
    save(out / 'CPU_AUDIT.json', result)
    return result


def dependencies(kit, downloads, out):
    spec = read(kit / 'DEPENDENCIES.json')
    require(not out.exists(), 'DLL output must be new')
    for a in spec['runtime_archives']:
        check(downloads / a['name'], a)
    out.mkdir(parents=True)
    found = {}
    for a in spec['runtime_archives']:
        with zipfile.ZipFile(downloads / a['name']) as z:
            for name, h in spec['numerical_dlls'].items():
                if name not in z.namelist():
                    continue
                require(name not in found, 'duplicate DLL provider')
                p = out / name
                with z.open(name) as src, p.open('xb') as dst:
                    shutil.copyfileobj(src, dst)
                require(sha(p) == h, 'exact historical DLL: ' + name)
                found[name] = h
    require(found == spec['numerical_dlls'], 'missing historical DLL')
    result = dict(status='PASS', exact_dlls=len(found), providers=spec['runtime_archives'], native_processes_started=0)
    save(out / 'DEPENDENCY_VERIFICATION.json', result)
    return result


def prepare(kit, out, dll_dir, target, draft):
    audit(kit)
    deps = read(kit / 'DEPENDENCIES.json')
    for name, h in deps['numerical_dlls'].items():
        require(sha(dll_dir / name) == h, 'DLL: ' + name)
    for label, p in [('target', target), ('draft', draft)]:
        check(p, deps['models'][label])
    check(kit / 'sources/SOURCE_RUNTIME.zip', deps['source_archive'])
    require(not out.exists(), 'runtime output must be new')
    out.mkdir(parents=True)
    extract(kit / 'sources/SOURCE_RUNTIME.zip', out / 'original', 'INDEX.json')
    for name in deps['numerical_dlls']:
        shutil.copyfile(dll_dir / name, out / 'original/native/bin' / name)
    for name in ('stage-fixture', 'stage-expected'):
        shutil.copytree(kit / name, out / name)
    for name in ('PANEL.json', 'STAGE_ORIGIN.json', 'HISTORICAL_R_ENDPOINTS.json'):
        shutil.copyfile(kit / name, out / name)
    contract = read(kit / 'MODEL_CONTRACT.json')
    for label, p in [('target', target), ('draft', draft)]:
        contract['families']['Qwen']['models'][label]['path'] = str(p.resolve())
    save(out / 'MODEL_CONTRACT.json', contract)
    slots = [read(kit / 'qualification-v2' / (s + '.json'))['slot'] for s in read(kit / 'selection.json')['slots']]
    save(out / 'DELIVERY_SLOTS.json', slots)
    result = dict(status='PASS_FILE_IDENTITY_ONLY', numerical_dlls=deps['numerical_dlls'],
                  models=contract['families']['Qwen']['models'], native_processes_started=0,
                  source='PR147 original Qwen source capsule; no metadata4 substitution')
    save(out / 'RECOVERY.json', result)
    return result


def audit_request(kit, actual):
    """Optional CPU comparison after a separately requested native replay."""
    audit(kit)
    result = read(actual / 'result.json')
    slots = read(kit / 'selection.json')['slots']
    require(result['status'] == 'COMPLETE' and len(result['requests']) == len(slots), 'complete replay required')
    require({r['slot']['slot_id'] for r in result['requests']} == set(slots), 'replay slot set')
    for slot in slots:
        reference = read(kit / 'qualification-v2' / (slot + '.json'))
        current = read(actual / (slot + '.json'))
        for key in ('slot', 'input_id', 'arm', 'k', 'lifecycle', 'capture', 'ids', 'eog', 'length',
                    'terminal_id', 'stop_reason', 'cycles', 'target_final_kv', 'draft_final_kv'):
            require(current[key] == reference[key], slot + ': ' + key)
        expected = vectors(kit / 'qualification-v2' / slot)
        require(vectors(actual / slot) == expected, slot + ': complete reference vectors')
    return dict(status='PASS', full_requests=len(slots), vector_files=704, native_processes_started=0,
                comparison='Full reference endpoints, stop state, speculative state and all vocabulary vectors; timings ignored')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest='command', required=True)
    p = sub.add_parser('restore'); p.add_argument('index', type=P); p.add_argument('out', type=P)
    p = sub.add_parser('audit'); p.add_argument('kit', type=P)
    p = sub.add_parser('audit-request'); p.add_argument('kit', type=P); p.add_argument('actual', type=P)
    p = sub.add_parser('dependencies'); p.add_argument('kit', type=P); p.add_argument('downloads', type=P); p.add_argument('out', type=P)
    p = sub.add_parser('prepare'); p.add_argument('kit', type=P); p.add_argument('out', type=P)
    for flag in ('dll-dir', 'target', 'draft'):
        p.add_argument('--' + flag, type=P, required=True)
    a = ap.parse_args()
    if a.command == 'restore': result = restore(a.index.resolve(), a.out.resolve())
    elif a.command == 'audit': result = audit(a.kit.resolve())
    elif a.command == 'audit-request': result = audit_request(a.kit.resolve(), a.actual.resolve())
    elif a.command == 'dependencies': result = dependencies(a.kit.resolve(), a.downloads.resolve(), a.out.resolve())
    else: result = prepare(a.kit.resolve(), a.out.resolve(), a.dll_dir.resolve(), a.target.resolve(), a.draft.resolve())
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
