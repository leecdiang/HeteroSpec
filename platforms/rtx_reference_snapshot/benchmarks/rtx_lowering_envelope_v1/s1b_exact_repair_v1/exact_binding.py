"""Exact-byte admission. Census JSON is NEVER parsed or normalized here."""
import hashlib, json
from pathlib import Path

def digest(data):
    return hashlib.sha256(data).hexdigest()

def exact_file(pin):
    p = Path(pin['path'])
    if not p.is_absolute() or not p.is_file():
        raise ValueError('missing absolute execution-bound artifact')
    data = p.read_bytes()
    if len(data) != pin['bytes'] or digest(data) != pin['sha256']:
        raise ValueError('execution-bound exact bytes mismatch')
    return data

def admit(freeze, approval, f0_path):
    # Hash the F0 bytes too. The caller consumes the returned Census bytes,
    # rather than re-opening a path after a separate semantic/hash check.
    f0_bytes = Path(f0_path).read_bytes()
    if digest(f0_bytes) != approval['F0_sha256']:
        raise ValueError('exact F0 mismatch')
    exact_freeze = json.loads(f0_bytes)
    if freeze != exact_freeze:
        raise ValueError('caller freeze differs from exact F0 content')
    if approval['registration_id'] != freeze['registration_id']:
        raise ValueError('registration mismatch')
    c = freeze['execution_bound_census']
    d = freeze['execution_bound_decision']
    if approval['census_sha256'] != c['sha256']:
        raise ValueError('authorized Census hash differs from consumed artifact')
    if approval['decision_sha256'] != d['sha256']:
        raise ValueError('authorized Decision hash differs from consumed artifact')
    return exact_file(c), exact_file(d)
