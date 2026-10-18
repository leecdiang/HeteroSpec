"""CPU-only archive production, exact Git staging/tree checks and remote restore."""
import hashlib, json, subprocess, zipfile
from pathlib import Path, PurePosixPath

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(data, f, separators=(',', ':'))
        f.write('\n')

def safe_name(name):
    p = PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
        raise ValueError('unsafe archive member')

def package_existing(source_archive, out):
    """Rebuild manifest and ZIP from ALL original members, preserving each byte."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(source_archive) as src:
        old_manifest = json.loads(src.read('MANIFEST.json'))
        if set(src.namelist()) != set(old_manifest) | {'MANIFEST.json'}:
            raise ValueError('original archive incomplete')
        members = {}
        with zipfile.ZipFile(out/'raw-000.zip.part', 'x', zipfile.ZIP_DEFLATED) as dst:
            for name in sorted(old_manifest):
                safe_name(name)
                data = src.read(name)
                if len(data) != old_manifest[name]['bytes'] or sha(data) != old_manifest[name]['sha256']:
                    raise ValueError('original member changed')
                members[name] = dict(bytes=len(data), sha256=sha(data))
                dst.writestr(name, data)
            dst.writestr('MANIFEST.json', json.dumps(members, separators=(',', ':'))+'\n')
    part = out/'raw-000.zip.part'
    manifest = dict(schema=1, members=members, member_count=len(members),
                    member_bytes=sum(x['bytes'] for x in members.values()),
                    archive_bytes=part.stat().st_size, archive_sha256=sha(part.read_bytes()),
                    parts=[dict(name=part.name, bytes=part.stat().st_size, sha256=sha(part.read_bytes()))],
                    original_archive_sha256=sha(Path(source_archive).read_bytes()),
                    member_bytes_changed=False)
    write_json(out/'ARCHIVE_MANIFEST.json', manifest)
    return manifest

def validate_archive(parts_root, manifest, restore=None):
    root = Path(parts_root)
    if len(manifest['parts']) != 1:
        raise ValueError('unexpected part count')
    part = manifest['parts'][0]
    safe_name(part['name'])
    blob = (root/part['name']).read_bytes()
    if len(blob) != part['bytes'] or sha(blob) != part['sha256'] or sha(blob) != manifest['archive_sha256']:
        raise ValueError('archive exact bytes mismatch')
    if len(blob) != manifest['archive_bytes']:
        raise ValueError('archive byte count mismatch')
    target = Path(restore) if restore else None
    if target and target.exists():
        raise ValueError('fresh root already exists; never overwrite')
    with zipfile.ZipFile(root/part['name']) as z:
        names = z.namelist()
        declared = manifest['members']
        if len(names) != len(set(names)) or set(names) != set(declared) | {'MANIFEST.json'}:
            raise ValueError('archive completeness mismatch')
        if json.loads(z.read('MANIFEST.json')) != declared:
            raise ValueError('embedded manifest mismatch')
        if len(declared) != manifest['member_count'] or sum(x['bytes'] for x in declared.values()) != manifest['member_bytes']:
            raise ValueError('manifest count/bytes mismatch')
        # Verify every member before creating any restored output or VERIFIED.
        for n, row in declared.items():
            safe_name(n)
            data = z.read(n)
            if len(data) != row['bytes'] or sha(data) != row['sha256']:
                raise ValueError('member exact bytes mismatch')
        if target:
            target.mkdir(parents=True)
            for n in names:
                p = target/n
                p.parent.mkdir(parents=True, exist_ok=True)
                with p.open('xb') as f:
                    f.write(z.read(n))
            actual = {p.relative_to(target).as_posix():dict(bytes=p.stat().st_size, sha256=sha(p.read_bytes()))
                      for p in target.rglob('*') if p.is_file() and p.relative_to(target).as_posix() != 'MANIFEST.json'}
            if actual != declared:
                raise ValueError('fresh enumeration mismatch')
    return dict(members_verified=len(declared), member_bytes=manifest['member_bytes'],
                archive_sha256=sha(blob), all_members_exact=True)

def stage_exact(repo, files):
    repo = Path(repo).resolve()
    rows = []
    for p in files:
        p = Path(p).resolve()
        rel = p.relative_to(repo).as_posix()
        data = p.read_bytes()
        ignore = subprocess.run(['git', 'check-ignore', '--no-index', '-v', rel], cwd=repo, capture_output=True)
        rows.append(dict(path=rel, bytes=len(data), sha256=sha(data), ignore_report=ignore.stdout.decode(errors='replace')))
    subprocess.run(['git', 'add', '--sparse', '--force', '--', *[x['path'] for x in rows]], cwd=repo, check=True)
    for row in rows:
        subprocess.run(['git', 'ls-files', '--error-unmatch', '--', row['path']], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        data = subprocess.check_output(['git', 'show', ':'+row['path']], cwd=repo)
        if len(data) != row['bytes'] or sha(data) != row['sha256']:
            raise ValueError('staged archive bytes mismatch')
    return rows

def tree_exact(repo, commit, rows):
    for row in rows:
        data = subprocess.check_output(['git', 'show', commit+':'+row['path']], cwd=repo)
        if sha(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('committed archive bytes mismatch')
    return True
