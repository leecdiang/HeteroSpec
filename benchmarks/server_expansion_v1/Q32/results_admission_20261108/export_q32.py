"""Export bounded diagnostic evidence; omit weights, binaries and HTTP headers."""
from pathlib import Path
import hashlib,json,re,sys,datetime
ROOT=Path(sys.argv[1]).resolve();OUT=Path(sys.argv[2]).resolve()
assert not OUT.exists();OUT.mkdir(parents=True)
def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def scrub(s):
    s=s.replace(str(ROOT),'$WORKSPACE').replace(str(Path.home()),'$HOME')
    s=re.sub(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}','$ALLOCATED_GPU',s)
    assert not re.search(r'https?://[^\s"<>]*[?&](?:token|Signature|signature|Expires|Policy|X-Amz-|Credential)',s)
    assert not re.search(r'gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|(?<![0-9])192\.168\.[0-9]+\.[0-9]+',s)
    return s
status=read(ROOT/'q32-diagnostic-audit-01/STATUS.json')
assert status['status'] in ('COMPLETE','FAILED_OR_SKIPPED_RETAINED')
records=[]
def narrow(x):
    if isinstance(x,dict):
        return {k:('USER_AUTHORIZED_ALLOCATION' if k=='allocation_id' else narrow(v)) for k,v in x.items()
                if k not in ('available_RAM_bytes','disk_free_bytes')}
    if isinstance(x,list):return [narrow(v) for v in x]
    return x
def copy(p,key):
    b=p.read_bytes();s=b.decode('utf8')
    if p.suffix=='.json':s=json.dumps(narrow(json.loads(s)),indent=2)+'\n'
    elif p.suffix=='.jsonl':s=''.join(json.dumps(narrow(json.loads(line)))+'\n' for line in s.splitlines() if line)
    derived=scrub(s).encode('utf8')
    target=OUT/key;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(derived)
    records.append(dict(path=key,bytes=len(derived),sha256=digest(derived),raw_bytes=len(b),raw_sha256=digest(b),redacted=b!=derived))
for folder in ('q32-diagnostic-source-01','q32-diagnostic-audit-01','q32-diagnostic-supervisor-01','q32-diagnostic-launch-01','q32-diagnostic-build-01','q32-diagnostic-run-01'):
    for p in sorted((ROOT/folder).rglob('*')):
        if not p.is_file():continue
        if p.name=='config.private.json' or p.name in ('admit','admit.o','admit.map','admit.d'):continue
        if p.suffix not in ('.json','.jsonl','.py','.cpp','.log') and p.name!='LICENSE':continue
        if p.stat().st_size>16*1024**2:raise RuntimeError('Unexpected oversized diagnostic text; inspect before export')
        copy(p,str(p.relative_to(ROOT)))
for name in ('SOURCE_FREEZE.private.json','EARLY_WINDOW_CLOSED.json','STATUS.json'):
    p=ROOT/'q32-download-audit-01'/name
    if p.exists():copy(p,'acquisition/'+name)
for p in sorted((ROOT/'q32-download-audit-01').glob('post*.json')):
    copy(p,'acquisition/'+p.name)
for p in (ROOT/'q32-download-audit-01').glob('assemble*.json'):copy(p,'acquisition/'+p.name)
for p in (ROOT/'q32-models-01/Qwen32B-VERIFIED.json',ROOT/'q32-source-01/Q32/models.json',ROOT/'q32-source-01/Q32/transport_modelscope.json',ROOT/'q32-models-01/licenses/SOURCE.json'):
    if p.exists():copy(p,'acquisition/'+p.name)
# Full network attempts and private signed redirect headers stay on the host.
# Commitment index proves retention; no header text or signed URL is copied.
private=[]
for base in (ROOT/'q32-models-01/Qwen32B-parts',ROOT/'q32-download-audit-01'):
    for p in sorted(base.rglob('*')):
        if p.is_file() and (p.suffix=='.log' or '.headers' in p.name):
            b=p.read_bytes();private.append(dict(path=str(p.relative_to(ROOT)),bytes=len(b),sha256=digest(b)))
def save(name,x):
    b=(json.dumps(x,indent=2)+'\n').encode();(OUT/name).write_bytes(b)
    return dict(path=name,bytes=len(b),sha256=digest(b))
records.append(save('PRIVATE_TRANSPORT_RECORD_INDEX.json',dict(records=private,contents='RETAINED_PRIVATE_NOT_REDISTRIBUTED',reason='Signed headers and irrelevant transport details excluded')))
save('TEXT_INDEX.json',dict(schema='heterospec.q32.diagnostic-export.v1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=records,
    full_records=True,redaction='Actual work-root/home/allocated UUID replaced; unrelated free RAM/disk inventory omitted; allocation-id placeholder. Original private bytes retained with hashes.',
    excluded=['model weights','full vocabulary','compiled numerical binaries','link maps','private config','network header/body logs'],
    scope='Allocation/short-forward diagnostics only; no numerical equivalence, formal performance or speculative-Q4 qualification'))
for row in records:
    assert digest((OUT/row['path']).read_bytes())==row['sha256']
save('LOCAL_READBACK.json',dict(passed=True,files=len(records),text_index_sha256=digest((OUT/'TEXT_INDEX.json').read_bytes()),all_exported_bytes_read_back=True))
print(json.dumps(dict(out=str(OUT),files=len(records),status=status['status'])))
