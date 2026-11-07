"""Verify committed historical projections without rewriting their provenance."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
EVID = HERE.parent / 'evidence'
baseline = json.loads((EVID / 'NARRATIVE_V02_BASELINE.json').read_text())
checked = []
for path, expected in baseline['protected_sha256'].items():
    if path.startswith('paper/mlsys2027/figures/') or path.endswith('references.bib'):
        continue  # Later figure locks / bibliography-prefix check run in make check.
    assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
    checked.append(path)
print(f'Frozen hardware assets/source locks PASS: {len(checked)} files; no regeneration.')
