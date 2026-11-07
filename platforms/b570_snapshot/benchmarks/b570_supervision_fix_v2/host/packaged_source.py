"""Exact packaged source set; reject import shadows and bytecode before execution."""
from pathlib import Path
import hashlib


def verify(root, bound):
    root = Path(root)
    actual = set()
    for p in root.rglob('*'):
        if p.is_symlink():
            raise ValueError('packaged source alias')
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if '__pycache__' in p.parts or p.suffix in ('.pyc', '.pyo'):
                raise ValueError('unreviewed bytecode')
            if rel.startswith('host/') or p.parent == root and p.suffix in ('.py', '.pyd', '.so'):
                actual.add(rel)
    expected = {name for name in bound if name.startswith('host/') or '/' not in name and Path(name).suffix in ('.py', '.pyd', '.so')}
    if actual != expected:
        raise ValueError('packaged importable source set differs from reviewed set')
    result = {}
    for name, digest in bound.items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
            raise ValueError('frozen source path escape')
        result[name] = hashlib.sha256((root/p).read_bytes()).hexdigest()
        if result[name] != digest:
            raise ValueError('unreviewed packaged source '+name)
    return result
