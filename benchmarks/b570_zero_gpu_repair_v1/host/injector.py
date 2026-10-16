"""Real sacrificial filesystem mutation, with independent operation interval."""
import json,os,sys,time,hashlib
from pathlib import Path
cfg=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'));p=Path(cfg['target']).resolve();root=Path(cfg['fixture_root']).resolve()
assert root in p.parents and 'b570-zero-gpu-repair' in str(root).lower()
before=p.read_bytes();s=p.stat();begin=time.perf_counter_ns();token=cfg['token'].encode()
with p.open('wb') as f:f.write(token);f.flush();os.fsync(f.fileno())
end=time.perf_counter_ns();after=p.read_bytes();s2=p.stat()
row=dict(event='FILESYSTEM_INJECTION',pid=os.getpid(),fault_id=cfg['fault_id'],target=str(p),trigger=cfg['trigger'],begin_ns=begin,end_ns=end,before_hex=before.hex(),after_hex=after.hex(),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(after).hexdigest(),before_file_id=s.st_ino,after_file_id=s2.st_ino,after_mtime_ns=s2.st_mtime_ns,volume=s2.st_dev,bytes=s2.st_size,operation='WriteFile+flush+close+readback')
with Path(cfg['receipt']).open('x',encoding='utf-8') as f:json.dump(row,f,sort_keys=True,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
print(json.dumps(row))
