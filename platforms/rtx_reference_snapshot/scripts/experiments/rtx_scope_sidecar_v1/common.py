"""Sidecar utilities; never edit or import new files into the frozen source directory."""
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
import shutil
import subprocess
import sys
import uuid

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'scripts/experiments/rtx_scope_transfer_v1'))
import study as s
import host

DESIGN = s.DESIGN
MAIN = REPO / 'work/scope-transfer-bundle-v1'
EVIDENCE = DESIGN / 'sidecar_execution'

def now():
    return datetime.now(timezone.utc)

def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    temp.write_bytes((json.dumps(value, indent=2, ensure_ascii=True)+'\n').encode())
    temp.replace(path)

def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def pin(root, path):
    path = Path(path)
    return {'path': path.resolve().relative_to(Path(root).resolve()).as_posix(),
            'bytes': path.stat().st_size, 'sha256': sha(path)}

def main_pins():
    names = ('EXECUTION_IDENTITY.json','FREEZE_COMMIT.json','REQUESTS.jsonl','ATTEMPTS.json',
             'Qwen-QUALIFICATION.json','SmolLM2-QUALIFICATION.json','REFERENCES.json')
    return {name: pin(MAIN, MAIN/name) for name in names}

def idle_window(seconds):
    """No sidecar when today's formal queue is incomplete or next date is near."""
    binding = host.validate_freeze(MAIN)
    attempts = s.read(MAIN/'ATTEMPTS.json')
    s.need(all(a['cleanup_verified'] and a['status']=='COMPLETE' for a in attempts), 'unreconciled main attempt')
    today = now().astimezone(s.LOCAL_TZ).date().isoformat()
    completed = {a['unit_id'] for a in attempts}
    for day, date in enumerate(binding['calendar_dates']):
        if date <= today:
            expected = {r['unit_id'] for r in s.lines(DESIGN/'SLOTS.jsonl') if r['date_slot']==day}
            s.need(expected <= completed, 'formal collection has priority: incomplete eligible date')
    future = [datetime.fromisoformat(d).replace(tzinfo=s.LOCAL_TZ) for d in binding['calendar_dates'] if d>today]
    if future:
        s.need((min(future)-now()).total_seconds() > seconds+1800, 'insufficient gap before formal date')
    s.need(not subprocess.check_output(['tasklist','/FI','IMAGENAME eq rtx-scope-transfer.exe','/FO','CSV','/NH'],text=True).lower().count('rtx-scope-transfer.exe'), 'native worker already active')
    return min(future).astimezone(timezone.utc)-timedelta(seconds=1800) if future else now()+timedelta(hours=8)

@contextmanager
def exclusive(label, seconds):
    """Use the existing formal admission lock, without changing any sealed file."""
    deadline = idle_window(seconds)
    lock = MAIN/'HOST.lock'
    owner = {'pid':os.getpid(),'utc':now().isoformat(),'unit':'sidecar/'+label,'owner':str(uuid.uuid4())}
    with lock.open('x',encoding='utf-8') as f:
        json.dump(owner,f)
    try:
        yield deadline
    finally:
        if lock.exists() and s.read(lock).get('owner')==owner['owner']:
            lock.unlink()

def check_room(path, minimum):
    s.need(shutil.disk_usage(path).free >= minimum, 'insufficient disk headroom')

def source_pins():
    return {p.relative_to(REPO).as_posix():sha(p) for p in Path(__file__).parent.glob('*.py')}

def validate_binding(bundle):
    frozen = s.read(bundle/'FREEZE.json')
    for rel, digest in frozen['sources'].items():
        s.need(sha(REPO/rel)==digest, 'sidecar source differs: '+rel)
        content=subprocess.check_output(['git','show',frozen['commit']+':'+rel],cwd=REPO)
        s.need(hashlib.sha256(content).hexdigest()==digest,'uncommitted sidecar source')
    for name, rel in frozen['files'].items():
        content=subprocess.check_output(['git','show',frozen['commit']+':'+rel],cwd=REPO)
        s.need(content==(bundle/name).read_bytes(),'sidecar binding differs: '+name)
    host.validate_freeze(MAIN)
    return s.read(bundle/'EXECUTION_IDENTITY.json')
