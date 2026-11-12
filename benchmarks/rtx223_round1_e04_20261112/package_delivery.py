"""Export new e04 sources/receipts and explicitly bound build products."""
import argparse
import hashlib
import json
import os
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PARENT = ROOT.parent / 'rtx223-round1-resume-20261112-e03'
TEXT = {'.py', '.md', '.json', '.jsonl', '.log', '.txt', '.cu', '.cuh', '.hpp', '.h', '.cpp', '.c', '.inc', '.inl', '.def', '.rsp', '.res', '.d', '.map', '.patch', '.ps1', '.cmake', '.bat', '.cmd'}
PRUNE = {'.git', '__pycache__', 'private', 'toolchain', 'toolchain-v1', 'toolchain-v2', 'temp', 'tmp', 'keep', 'intermediates', 'generated', 'bin', 'objects', 'compiler_copy', 'cache', 'global-cache', 'local-cache'}
EXCLUDED_SIDECARS = {'delivery/DELIVERY_MANIFEST.json', 'delivery/ZIP_VERIFIED.json', 'delivery/GITHUB_PUBLICATION.json'}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def published(path, data, text):
    rel = path.relative_to(ROOT)
    return (text and len(data) <= 512 * 1024 and 'raw' not in rel.parts
            and path.suffix.lower() not in {'.log', '.d', '.map', '.res', '.jsonl'})

def selected():
    original = json.loads((PARENT / 'runtime/SOURCE_PREPARED.json').read_bytes())['old_source_sha256']
    output = []
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = sorted(d for d in dirs if d not in PRUNE and not d.startswith('reconstruction'))
        directory_parts = Path(directory).relative_to(ROOT).parts
        if len(directory_parts) >= 4 and directory_parts[:2] == ('e04', 'frontend') and directory_parts[-1] == 'deps':
            dirs[:] = [d for d in dirs if d not in {'headers', 'link'}]
        for name in sorted(files):
            path = Path(directory) / name
            rel = path.relative_to(ROOT).as_posix()
            if rel in EXCLUDED_SIDECARS:
                continue
            if path.suffix.lower() == '.res' and 'compiler-subcommands' not in path.parts:
                continue
            if path.suffix.lower() not in TEXT and name not in {'.gitignore', '.gitattributes', 'LICENSE', 'UPSTREAM_LICENSE'}:
                continue
            data = path.read_bytes()
            if rel.startswith('runtime/source-v'):
                member = '/'.join(Path(rel).parts[2:])
                if original.get(member) == sha(data):
                    continue
            try:
                data.decode('utf8')
                text = True
            except UnicodeDecodeError:
                text = False
            output.append((path, data, text))
    return sorted(output, key=lambda item: item[0].relative_to(ROOT).as_posix())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--payload', type=Path, required=True)
    args = parser.parse_args()
    if args.zip.exists():
        raise FileExistsError(args.zip)
    files = selected()
    artifacts = json.loads((ROOT / 'e04/BINARY_ALLOWLIST.json').read_bytes())['files']
    binary_files = []
    for item in artifacts:
        rel = Path(item['path'])
        if rel.is_absolute() or rel.drive or '..' in rel.parts:
            raise ValueError('Unsafe artifact path')
        path = (ROOT / rel).resolve(strict=True)
        if not path.is_relative_to(ROOT):
            raise ValueError('Artifact escapes e04')
        data = path.read_bytes()
        if sha(data) != item['sha256']:
            raise ValueError('Artifact identity mismatch')
        binary_files.append((path, data, False))
    manifest = {
        'schema': 'heterospec.e04.delivery.v1',
        'epoch': 'rtx223-round1-resume-20261112-e04', 'decision': 'INCONCLUSIVE',
        'parent_head': '7a4f2ca75923066c6eaac02a5e9ae885a846d688',
        'files': [{'path': p.relative_to(ROOT).as_posix(), 'bytes': len(data), 'sha256': sha(data),
                   'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest(),
                   'published_in_Git': published(p, data, text),
                   'UTF8': text} for p, data, text in files],
        'zip_only_explicit_artifacts': artifacts,
        'exclusions': ['private evidence/helper payloads', 'copied proprietary toolchains/SDK inputs',
                       'unchanged pinned original core members', 'model weights and numerical captures',
                       'unlisted objects/executables/static libraries', 'reproducible retained compiler intermediates; their inventories are bound in build receipts'],
        'native_usage': {'requests': 0, 'rows': 0, 'launches': 0, 'seconds': 0, 'capture_bytes': 0},
        'CPU_preparation_bytes_are_not_GPU_capture_bytes': True,
        'self_included': False}
    dest = ROOT / 'delivery/DELIVERY_MANIFEST.json'
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf8')
    manifest_data = dest.read_bytes()
    archive = files + [(dest, manifest_data, True)] + binary_files
    with zipfile.ZipFile(args.zip, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path, data, _ in archive:
            bundle.writestr(path.relative_to(ROOT).as_posix(), data)
    with zipfile.ZipFile(args.zip) as bundle:
        if bundle.namelist() != [p.relative_to(ROOT).as_posix() for p, _, _ in archive]:
            raise ValueError('Archive inventory differs')
        for path, data, _ in archive:
            if bundle.read(path.relative_to(ROOT).as_posix()) != data:
                raise ValueError('Archive bytes differ')
    public_files = [(p, data) for p, data, text in files if published(p, data, text)] + [(dest, manifest_data)]
    payload = [{'path': p.relative_to(ROOT).as_posix(), 'mode': '100644', 'type': 'blob', 'content': data.decode('utf8')}
               for p, data in public_files]
    args.payload.parent.mkdir(parents=True, exist_ok=True)
    args.payload.write_text(json.dumps(payload, ensure_ascii=True), encoding='utf8')
    receipt = {'zip': str(args.zip.resolve()), 'bytes': args.zip.stat().st_size,
               'sha256': sha(args.zip.read_bytes()), 'files': len(archive), 'Git_files': len(public_files),
               'every_entry_rehashed': True, 'payload_bytes': args.payload.stat().st_size,
               'private_and_toolchain_bytes_included': False}
    (ROOT / 'delivery/ZIP_VERIFIED.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
    print(json.dumps(receipt))

if __name__ == '__main__':
    main()
