"""CPU-only review of a fixed B570 delivery; read-only GitHub permissions."""
import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.request
from datetime import datetime, timezone

REPO = 'leecdiang/HeteroSpec'
HEAD = '196ed563b36d0e16a3cdb667b6996a4afd98da1d'
TREE = '5b6244891a5fe15d6dcc48cf76c775999dff08cb'
ARCHIVE = '29ff8282a2751342c834d5a81c27c76daedab611205889a5a7c6ee8ec4ee45d8'
ROOT = Path('audit-scratch').resolve()
OUTPUT = Path('audit-output').resolve()
DOC = 'benchmarks/b570_prefill_diagnostic_v1'
ART = 'artifacts/b570_prefill_diagnostic_v1'
CODE = 'scripts/platform/b570_prefill_diagnostic_v1'

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save(name, data):
    (OUTPUT / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def get(endpoint):
    request = urllib.request.Request('https://api.github.com/repos/' + REPO + '/' + endpoint,
        headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                 'Accept': 'application/vnd.github+json', 'User-Agent': 'HeteroSpec-read-only-evidence-audit'})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)

def blob(entry, path):
    data = get('git/blobs/' + entry['sha'])
    assert data['encoding'] == 'base64' and data['sha'] == entry['sha']
    raw = base64.b64decode(data['content'])
    assert len(raw) == entry['size']
    assert hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == entry['sha']
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)

def main():
    OUTPUT.mkdir(exist_ok=True)
    ROOT.mkdir(exist_ok=False)
    listing = get('git/trees/' + TREE + '?recursive=1')
    assert not listing['truncated'] and listing['sha'] == TREE
    entries = {e['path']: e for e in listing['tree'] if e['type'] == 'blob'}
    checkout = ROOT / 'remote'
    for name in [ART + '/ARCHIVE.json', ART + '/REMOTE_MANIFEST.json', DOC + '/FREEZE.json']:
        blob(entries[name], checkout / name)
    index = read(checkout / ART / 'ARCHIVE.json')
    assert index['archive_sha256'] == ARCHIVE and index['manifest_files'] == 4073
    freeze = read(checkout / DOC / 'FREEZE.json')
    for number, part in enumerate(index['parts'], 1):
        name = ART + '/' + part['path']
        path = checkout / name
        blob(entries[name], path)
        assert path.stat().st_size == part['bytes'] and sha(path) == part['sha256']
        print(json.dumps({'phase': 'part_verified', 'part': number, 'total': len(index['parts'])}), flush=True)
    archive = ROOT / 'evidence.tar.gz'
    with archive.open('wb') as dest:
        for part in index['parts']:
            with (checkout / ART / part['path']).open('rb') as source:
                shutil.copyfileobj(source, dest, 8 * 1024 * 1024)
    assert archive.stat().st_size == index['archive_bytes'] and sha(archive) == ARCHIVE
    cas = ROOT / 'cas'
    cas.mkdir()
    with tarfile.open(archive, 'r:gz') as source:
        source.extractall(cas, filter='data')
    assert sha(cas / 'MANIFEST.json') == index['manifest_sha256']
    manifest = read(cas / 'MANIFEST.json')
    assert len(manifest['files']) == 4073
    expected_sources = {CODE + '/' + name.replace('\\', '/').split('/' + CODE + '/', 1)[1]: value
                        for name, value in freeze['sources'].items()}
    for name, expected in expected_sources.items():
        assert manifest['files'][name]['sha256'] == expected
        blob(entries[name], checkout / name)
        assert sha(checkout / name) == expected
    restored = ROOT / 'restored'
    restored.mkdir()
    for name, item in manifest['files'].items():
        relative = Path(name)
        assert not relative.is_absolute() and '..' not in relative.parts and ':' not in name
        source = cas / 'blobs' / item['sha256'][:2] / item['sha256']
        target = restored / relative
        assert source.stat().st_size == item['bytes'] and sha(source) == item['sha256']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        assert sha(target) == item['sha256']
    print(json.dumps({'phase': '4073_files_restored_and_hashed'}), flush=True)
    for name, expected in expected_sources.items():
        assert sha(restored / name) == expected
    reports = OUTPUT / 'recomputed'
    reports.mkdir()
    for p in (restored / DOC).glob('*'):
        if p.is_file():
            shutil.copyfile(p, reports / p.name)
    spec = importlib.util.spec_from_file_location('fixed_raw_verifier', restored / CODE / 'independent_verify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DOC = reports
    module.main()
    actual = read(reports / 'SUMMARY.json')
    published = read(restored / DOC / 'SUMMARY.json')
    for key in ['planned', 'valid', 'failed_units', 'attempts', 'task_units', 'repeat_stable_tasks',
                'comparisons', 'diagnostic_reference_recovery', 'controls_reference_regressions']:
        assert actual[key] == published[key], key
    # Export full native/target captures and attempts for a separate local parser.
    # Large KV bytes were verified above, but are kept in the original capsule.
    selected = {name for name in manifest['files'] if name.startswith(CODE + '/') or name.startswith(DOC + '/')}
    selected.update(name for name in manifest['files'] if name.startswith(ART + '/') and (
        '/formal/' in name or '/g0/' in name or '/evaluation/' in name or '/inputs/' in name or
        name.endswith(('/RUN_LEDGER.jsonl', '/T1_SEAL.json', '/QUEUE.json', '/STATE.json', '/INPUTS.json')))
        and not name.endswith(('.kv', '.f32')))
    with tarfile.open(OUTPUT / 'raw-review-subset.tar.gz', 'w:gz') as export:
        for name in sorted(selected):
            export.add(restored / name, arcname=name, recursive=False)
    assert (OUTPUT / 'raw-review-subset.tar.gz').stat().st_size < 28 * 1024 * 1024
    save('REVIEW_RETRIEVAL_RECEIPT.json', {
        'status': 'PASS', 'reviewed_head': HEAD, 'reviewed_tree': TREE,
        'archive_sha256': ARCHIVE, 'archive_bytes': index['archive_bytes'], 'parts': len(index['parts']),
        'restored_files': len(manifest['files']), 'all_file_hashes': 'PASS', 'frozen_sources': 'PASS',
        'raw_verifier': read(reports / 'INDEPENDENT_VERIFICATION.json'),
        'summary_fields_recomputed_equal': True, 'subset_files': len(selected),
        'subset_sha256': sha(OUTPUT / 'raw-review-subset.tar.gz'),
        'subset_bytes': (OUTPUT / 'raw-review-subset.tar.gz').stat().st_size,
        'no_model_inference': True, 'original_evidence_modified': False,
        'limitations': ['Omitted model/runtime bytes remain unauthenticated',
                        'Local chronology is not an independent absolute timestamp'],
        'utc': datetime.now(timezone.utc).isoformat()})
    print(json.dumps({'phase': 'PASS', 'raw_units': 360}), flush=True)

if __name__ == '__main__':
    main()
