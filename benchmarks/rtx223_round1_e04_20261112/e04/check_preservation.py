"""Read/hash old evidence and copy the unchanged ledger for audit only."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    reports = []
    for name in ('rtx221-round1-20261112', 'rtx223-round1-resume-20261112-e02', 'rtx223-round1-resume-20261112-e03'):
        folder = BASE / name
        manifest = folder / 'delivery/DELIVERY_MANIFEST.json'
        rows = json.loads(manifest.read_bytes())['files']
        mismatch = [r['path'] for r in rows if not (folder / r['path']).is_file()
                    or sha(folder / r['path']) != r['sha256']]
        reports.append({'path': str(folder), 'files': len(rows),
                        'manifest_sha256': sha(manifest), 'mismatches': mismatch})
    old = json.loads((BASE / 'rtx223-round1-resume-20261112-e03/e03/dedup/DEDUP_E03_RESULT.json').read_bytes())['old_file_checks']
    ledgers = []
    for row in old:
        actual = sha(Path(row['path']))
        ledgers.append({'path': row['path'], 'sha256': actual, 'expected_sha256': row['sha256'],
                        'unchanged': actual == row['sha256']})
    binding = json.loads((HERE / 'BUDGET_CONTINUITY.json').read_bytes())
    canonical = Path(binding['canonical_ledger'])
    expected = json.loads((BASE / 'rtx223-round1-resume-20261112-e03/e03/ledger-evidence/SNAPSHOT.json').read_bytes())['source_sha256']
    before = sha(canonical)
    data = canonical.read_bytes()
    uri = canonical.resolve().as_uri() + '?mode=ro&immutable=1'
    with sqlite3.connect(uri, uri=True) as connection:
        tables = [r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        counts = {table: connection.execute('SELECT COUNT(*) FROM "' + table.replace('"', '""') + '"').fetchone()[0]
                  for table in tables}
    after = sha(canonical)
    ledgers.append({'path': str(canonical), 'sha256': after, 'expected_sha256': expected,
                    'unchanged': before == after == expected, 'readonly_table_counts': counts})
    passed = not any(r['mismatches'] for r in reports) and all(r['unchanged'] for r in ledgers)
    if not passed:
        raise ValueError('Old evidence changed; no overwrite or restoration attempted')
    dest = HERE / 'ledger-evidence'
    dest.mkdir(exist_ok=False)
    snapshot = dest / 'FAMILY_LEDGER_READONLY_SNAPSHOT.sqlite'
    snapshot.write_bytes(data)
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'passed': passed,
              'original_manifests': reports, 'ledgers': ledgers,
              'source_canonical_ledger': str(canonical), 'copy_sha256': sha(snapshot),
              'source_sha256': after, 'audit_copy_not_new_canonical_ledger': True,
              'source_ledger_writes': 0, 'new_native_allowance': False}
    (HERE / 'PRESERVATION_FINAL.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf8')
    print(json.dumps({'preserved': passed, 'original_files': sum(x['files'] for x in reports),
                      'family_sha256': after, 'readonly_table_counts': counts}))

if __name__ == '__main__':
    main()
