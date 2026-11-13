"""Small, explicit utilities; no model execution or network at import."""
from __future__ import annotations
import hashlib, json, os, subprocess, time
from pathlib import Path

def need(ok, message):
    if not ok:
        raise RuntimeError(message)

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def save(path, data):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x', encoding='utf-8') as f:
        json.dump(data, f, indent=2, allow_nan=False); f.write('\n')

def inventory(root):
    root = Path(root).resolve(); result = {}
    for p in sorted(root.rglob('*')):
        if '.git' in p.relative_to(root).parts:
            continue
        need(not p.is_symlink(), 'Unexpected source symlink: ' + str(p))
        if p.is_file():
            result[p.relative_to(root).as_posix()] = sha(p)
    return result

def verify_tree(root, files):
    need(inventory(root) == files, 'Source file set/content changed; keep old receipt and stage a new version')

def command(argv, out, *, cwd=None, timeout=3600, env=None):
    out = Path(out); out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic(); code = None
    try:
        with (out / 'stdout.log').open('xb') as f:
            r = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                               stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        code = r.returncode
        need(code == 0, 'Command failed; retained log: ' + str(out))
    finally:
        save(out / 'command.json', {'argv': list(map(str, argv)), 'cwd': str(Path(cwd or '.').resolve()),
             'returncode': code, 'wall_s': time.monotonic()-start, 'status':'COMPLETE' if code == 0 else 'FAILED'})

def tree_id(files):
    return hashlib.sha256(json.dumps(files, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
