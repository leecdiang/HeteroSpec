"""Portable, read-only verification of this E0 evidence directory."""
import collections
import csv
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
manifest=read(root/'EVIDENCE_SHA256.json')
for item in manifest['files']:
    p=(root/item['path']).resolve()
    assert p.is_relative_to(root) and p.is_file(),item['path']
    assert p.stat().st_size==item['bytes'],item['path']
    with p.open('rb') as f:
        assert hashlib.file_digest(f,'sha256').hexdigest()==item['sha256'],item['path']
assert read(root/'VALIDATION.json')['status']=='PASS'
assert read(root/'E0_DISPOSITION.json')['scientific_screen']=='NOT_EVALUATED'
assert read(root/'PROCESS_RECEIPTS.json')['native_process_starts']==0
with (root/'ALL_SLOTS.csv').open(encoding='utf-8',newline='') as f:
    slots=list(csv.DictReader(f))
assert len(slots)==164
assert all('NOT_STARTED' in s['status'] or 'UNSTARTED' in s['status'] for s in slots)
counts=collections.Counter(s['gate'] for s in slots)
assert counts==dict(E1=12,E2=128,E3=24)
print(json.dumps(dict(status='PASS',verified_files=len(manifest['files']),native_starts=0,
                      slot_counts=dict(counts),scope='Archived E0 evidence only; no new model validation')))
