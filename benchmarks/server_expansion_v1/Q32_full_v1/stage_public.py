"""Terminal-only public package preparation. Never starts native/GPU work."""
import argparse
import hashlib
import ipaddress
import json
import lzma
from pathlib import Path
import re
import shutil
import socket
import time


def read(p):
    return json.loads(p.read_text())


def digest(b):
    return hashlib.sha256(b).hexdigest()


def file_digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def save(p, x):
    p.write_text(json.dumps(x, indent=2, ensure_ascii=False) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--work', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    w = a.work
    while not (w / 'delivery-03/COMPLETE.json').exists():
        terminal = w / 'delivery-03.TERMINAL.json'
        if terminal.exists():
            raise RuntimeError('Delivery audit stopped; preserve artifacts, no public package')
        assert time.time() < 1794267900, 'Terminal package preparation deadline'
        time.sleep(5)
    audit = read(w / 'delivery-03/COMPLETE.json')
    assert audit['passed'] and audit['performance_complete']
    assert read(w / 'PANEL_CONTINUATION18_TERMINAL.json')['passed']
    start = time.monotonic()
    source = w / 'export-13'
    out = a.out
    out.mkdir()
    (out / 'archive').mkdir()
    (out / 'audit').mkdir()
    identity = [Path.home().name, socket.gethostname()]
    identity_patterns = [re.compile(r'(?<![A-Za-z0-9_])' + re.escape(x) +
                                    r'(?![A-Za-z0-9_])') for x in identity if len(x) >= 3]
    ips = re.compile(r'(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])')

    def redact_ip(match):
        try:
            ip = ipaddress.IPv4Address(match.group())
        except ipaddress.AddressValueError:
            return match.group()
        first, second, *_ = map(int, str(ip).split('.'))
        if first == 10 or (first == 192 and second == 168) or (first == 172 and 16 <= second <= 31):
            return '<private-network>'
        return match.group()

    def public(text):
        text = ips.sub(redact_ip, text)
        for pat in identity_patterns:
            text = pat.sub('<private-identity>', text)
        assert not re.search(r'/home/[A-Za-z0-9_.-]+|GPU-[a-fA-F0-9]{8}-', text)
        return text

    originals = []
    for folder, directory in [('archive', source), ('audit', w / 'delivery-03')]:
        for f in sorted(directory.glob('*.json')):
            if folder == 'archive' and f.name in ('BUNDLE.json', 'TEXT_INDEX.json'):
                continue
            raw = f.read_bytes()
            b = public(raw.decode('utf8')).encode('utf8')
            (out / folder / f.name).write_bytes(b)
            originals.append(dict(file=folder+'/'+f.name, source_bytes=len(raw),
                                  source_sha256=digest(raw), public_bytes=len(b),
                                  public_sha256=digest(b), changed=raw != b))
    bundle = read(source / 'BUNDLE.json')
    index = read(source / 'TEXT_INDEX.json')['files']
    new_index = []
    changes = 0
    with lzma.open(source / bundle['file'], 'rt', encoding='utf8') as f:
        for i, line in enumerate(f):
            record = json.loads(line)
            old = index[i]
            assert record['path'] == old['path']
            raw = record['text'].encode('utf8')
            assert len(raw) == old['public_bytes'] and digest(raw) == old['public_sha256']
            text = public(record['text']).encode('utf8')
            changes += raw != text
            new_index.append({**old, 'public_bytes':len(text), 'public_sha256':digest(text)})
    assert len(index) == len(new_index) == bundle['records']
    if changes:
        payload = out / 'archive/TEXT_RECORDS.jsonl.xz'
        with lzma.open(source / bundle['file'], 'rt', encoding='utf8') as f, lzma.open(payload, 'xb', preset=9) as dest:
            for line in f:
                record = json.loads(line)
                record['text'] = public(record['text'])
                dest.write((json.dumps(record, ensure_ascii=True, separators=(',',':'))+'\n').encode())
        parts = []
        with payload.open('rb') as f:
            i = 0
            while True:
                b = f.read(384*1024)
                if not b:
                    break
                name = f'TEXT_RECORDS.part-{i:04d}.xz'
                (out / 'archive' / name).write_bytes(b)
                parts.append(dict(file=name, bytes=len(b), sha256=digest(b)))
                i += 1
        new_bundle = {**bundle, 'bytes':payload.stat().st_size, 'sha256':file_digest(payload), 'ordered_parts':parts}
        save(out / 'archive/BUNDLE.json', new_bundle)
        save(out / 'archive/TEXT_INDEX.json', dict(files=new_index))
        # Keep the unsplit file locally; omit it from the public file manifest.
    else:
        for part in bundle['ordered_parts']:
            b = (source / part['file']).read_bytes()
            assert len(b) == part['bytes'] and digest(b) == part['sha256']
            (out / 'archive' / part['file']).write_bytes(b)
        shutil.copyfile(source / 'BUNDLE.json', out / 'archive/BUNDLE.json')
        shutil.copyfile(source / 'TEXT_INDEX.json', out / 'archive/TEXT_INDEX.json')
        new_bundle = bundle
    stats = read(out / 'archive/ANALYSIS.json')
    assert stats['complete'] and len(stats['rows']) == 96
    columns = ['round','position','arm','root','service_s','receipt_sha256']
    (out / 'MEASUREMENTS.csv').write_text(','.join(columns)+'\n'+''.join(','.join(str(x[k])for k in columns)+'\n'for x in stats['rows']))
    save(out / 'PUBLIC_TRANSFORM.json', dict(passed=True,
         source_bundle_sha256=bundle['sha256'], public_bundle_sha256=new_bundle['sha256'],
         additionally_redacted_text_records=changes, source_file_transformations=originals,
         scope='Private source records retained. Additional RFC1918/host/user redaction changes public hashes only; numerical data/statistics unchanged.',
         package_wall_s=time.monotonic()-start, native_requests_started=0))
    files = []
    for f in sorted(out.rglob('*')):
        if not f.is_file() or f.name == 'TEXT_RECORDS.jsonl.xz':
            continue
        if f.suffix in ('.json','.csv'):
            text = f.read_text()
            assert public(text) == text
        files.append(dict(file=str(f.relative_to(out)), bytes=f.stat().st_size, sha256=file_digest(f)))
    save(out / 'FILES.json', dict(files=files))
    save(w / 'PUBLIC_STAGE_COMPLETE.json', dict(passed=True, files=len(files)+1,
         manifest_sha256=file_digest(out/'FILES.json'), bytes=sum(x['bytes']for x in files),
         additionally_redacted_text_records=changes, native_requests_started=0,
         anonymous_remote_readback='PENDING_UPLOAD'))
    print(json.dumps(dict(passed=True,files=len(files)+1,bytes=sum(x['bytes']for x in files), additionally_redacted_text_records=changes)),flush=True)


if __name__ == '__main__':
    main()
