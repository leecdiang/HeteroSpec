"""Lossless partitioning and full-member readback. Upload is a separate host step."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import zipfile
from common import need, read, sha, write


def pack(root, out, limit=512*1024**2):
    root, out = Path(root).resolve(), Path(out).resolve()
    need(root.is_dir() and not out.exists() and not out.is_relative_to(root), 'fresh separate archive directory')
    need(limit > 0, 'positive shard size')
    files = sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() not in ('.gguf', '.dll', '.exe', '.obj', '.lib', '.pdb'))
    need(all(not p.is_symlink() for p in files), 'archive symlink')
    out.mkdir(parents=True);parts = [];group = [];total = 0
    def flush():
        nonlocal group, total
        if not group: return
        p = out / f'part-{len(parts):04d}.zip';members = []
        with zipfile.ZipFile(p, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as z:
            for f in group:
                rel = f.relative_to(root).as_posix();pin = {'path': rel, 'bytes': f.stat().st_size, 'sha256': sha(f)}
                z.write(f, rel);members.append(pin)
        item = {'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p), 'members': members}
        verify_part(out, item);parts.append(item);group = [];total = 0
    for f in files:
        if group and total + f.stat().st_size > limit: flush()
        group.append(f);total += f.stat().st_size
    flush();index = {'status': 'LOCAL_READBACK_COMPLETE', 'parts': parts, 'file_count': len(files),
                    'remote_readback_complete': False, 'binary_models_and_runtime_excluded': True}
    write(out / 'INDEX.json', index);return index


def verify_part(root, item):
    p = Path(root) / item['path'];need(p.stat().st_size == item['bytes'] and sha(p) == item['sha256'], 'archive identity')
    with zipfile.ZipFile(p) as z:
        names = z.namelist();expected = [m['path'] for m in item['members']]
        need(len(names) == len(set(names)) and set(names) == set(expected), 'archive member inventory')
        for m in item['members']:
            need(not Path(m['path']).is_absolute() and '..' not in Path(m['path']).parts, 'unsafe archive path')
            h = hashlib.sha256();size = 0
            with z.open(m['path']) as f:
                while chunk := f.read(1024*1024): h.update(chunk);size += len(chunk)
            need(size == m['bytes'] and h.hexdigest() == m['sha256'], 'decompressed member identity')


def verify(root):
    index = read(Path(root) / 'INDEX.json')
    for p in index['parts']: verify_part(root, p)
    return {'parts': len(index['parts']), 'members': sum(len(p['members']) for p in index['parts']), 'status': 'ALL_MEMBERS_VERIFIED'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);sub = p.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('pack');a.add_argument('--root', required=True);a.add_argument('--out', required=True)
    a = sub.add_parser('verify');a.add_argument('--root', required=True)
    a = p.parse_args();print(pack(a.root, a.out)['status'] if a.cmd == 'pack' else verify(a.root))
