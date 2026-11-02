"""Content-bound companion study helpers; no native execution on import."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import subprocess

STUDY = 'b570_llama_companion_v1'
BASE = '022babfabb3d1b6f4f2a2830dca04b2654d193f9'
RTX = 'aff1d029966a20adebfad6b664a36f32ed04bf9c'
HISTORY = '29511ed91eb9f3d9773cfdda53e3554b0f4ad08b'
UPSTREAM = '0cae43063cf15170e91a2ff4d034da0ecef4a1b2'
TARGET = '9da71c45c90a821809821244d4971e5e5dfad7eb091f0b8ff0546392393b6283'
DRAFT = '432f310a77f4650a88d0fd59ecdd7cebed8d684bafea53cbff0473542964f0c3'
VOCAB = 128256
DEVELOPMENT = ['CodeContests/valid/108', 'CodeContests/valid/43', 'GSM8K/test/496']


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def git_bytes(repo, ref, path, expected=None):
    data = subprocess.run(['git', '-C', str(repo), 'show', f'{ref}:{path}'],
                          check=True, capture_output=True, timeout=120).stdout
    need(expected is None or blob(data) == expected, 'Git blob mismatch: ' + path)
    return data


def confined(root, rel):
    root = Path(root).resolve()
    p = (root / rel).resolve()
    need(p != root and p.is_relative_to(root), 'unsafe relative path')
    return p


def input_check(x):
    ids = x['prompt_ids']
    need(isinstance(x['id'], str) and bool(x['id']), 'input ID')
    need(isinstance(ids, list) and len(ids) > 0, 'empty prompt')
    need(all(type(t) is int and 0 <= t < VOCAB for t in ids), 'input vocabulary')
    need(type(x['cap']) is int and x['cap'] == 128, 'fixed cap128')
    need(len(ids) + x['cap'] + 4 <= 1024, 'context extent')
    if 'prompt_ids_sha256' in x:
        need(x['prompt_ids_sha256'] == digest(ids), 'canonical token hash mismatch')
    return x


def endpoint(x):
    ids, flags = x['ids'], x['eog']
    need(isinstance(ids, list) and 0 < len(ids) <= 128, 'output length')
    need(len(ids) == len(flags) == x['length'], 'endpoint sizes')
    need(all(type(t) is int and 0 <= t < VOCAB for t in ids), 'output vocabulary')
    need(all(type(f) is bool for f in flags), 'EOG type')
    need(not any(flags[:-1]), 'continued after EOG')
    need(x['terminal_id'] == ids[-1], 'terminal token')
    need(x['stop_reason'] == ('EOG' if flags[-1] else 'CAP'), 'stop reason')
    need(flags[-1] or len(ids) == 128, 'nonterminal early stop')
    return {k: x[k] for k in ('ids', 'eog', 'length', 'terminal_id', 'stop_reason')}


def positive(x, name):
    need(type(x) in (int, float) and math.isfinite(x) and x > 0, name)
    return x
