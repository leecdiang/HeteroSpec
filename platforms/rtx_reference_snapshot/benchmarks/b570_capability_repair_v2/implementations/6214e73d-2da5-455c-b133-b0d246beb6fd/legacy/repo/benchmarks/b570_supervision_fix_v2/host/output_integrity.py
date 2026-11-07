"""Reconcile successful producer bytes with the controller's parsed records."""
import hashlib
from evidence_io import strict_json


def positive_output(stdout, stderr, ack, records, pid, source_hash, counts):
    if not stdout.endswith(b'\n') or not ack.endswith(b'\n'):
        return False
    lines=stdout.splitlines(keepends=True)
    parsed=[strict_json(line) for line in lines]
    if parsed != records or [r.get('event') for r in parsed] != ['READY','WORKING']+['FRAME']*4+['COMPLETE']:
        return False
    if parsed[0].get('pid')!=pid or parsed[1].get('pid')!=pid or parsed[0].get('source_sha256')!=source_hash or parsed[-1].get('frames')!=4:
        return False
    if any(r.get('index')!=i or r.get('payload')!='x'*128 for i,r in enumerate(parsed[2:6])):
        return False
    expected=[dict(index=i,bytes=len(line),sha256=hashlib.sha256(line).hexdigest()) for i,line in enumerate(lines[2:6])]
    return ([strict_json(line) for line in ack.splitlines()]==expected
            and stderr==b'CPU_STDERR_FRAME\n'*4
            and counts.get('stdout')==len(stdout) and counts.get('stderr')==len(stderr))


def capture_files(reader, paths):
    """Absent failed-run outputs are reportable; present files remain authenticated."""
    captured={};missing=[]
    for name,path in paths.items():
        if not path.is_file():missing.append(path.relative_to(reader.root).as_posix());continue
        # Do not catch authentication failures or races after the existence check.
        captured[name]=reader.bytes(path)
    return captured,missing
