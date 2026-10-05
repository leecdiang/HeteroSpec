"""Durable state, freeze identity and native launch guards."""
import time, uuid
from prepare import *
from execution import identity, canonical, digest

STAGES=['PREPARE','G0','FREEZE','PREDICTING','PREDICTION_SEAL','REMOTE_READBACK','N0','BASELINE_RECHECK','N1','INDEPENDENT_VERIFY','ARCHIVE_VERIFY','DELIVERY']

def lock(root=OUT):
    p=root/'LOCK.json';root.mkdir(parents=True,exist_ok=True)
    if p.exists():
        x=read(p);actual=identity(x['pid'])
        if actual is not None and actual==x['creation_identity']:raise RuntimeError('second active controller rejected')
        p.rename(root/('LOCK.stale-'+uuid.uuid4().hex+'.json'))
    own=identity(os.getpid());assert own is not None
    with p.open('x',encoding='utf-8') as f:json.dump({'pid':os.getpid(),'creation_identity':own,'utc':utc()},f);f.flush();os.fsync(f.fileno())

def events(root=OUT):
    p=root/'LEDGER.jsonl'
    rows=[json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()] if p.exists() else []
    previous='0'*64
    for index,row in enumerate(rows):
        x=dict(row);h=x.pop('hash');assert x['sequence']==index and x['previous_hash']==previous and digest(canonical(x))==h;previous=h
    return rows

def event(kind,root=OUT,**kw):
    rows=events(root);previous=rows[-1]['hash'] if rows else '0'*64
    x={'sequence':len(rows),'previous_hash':previous,'event':kind,'utc':utc(),'monotonic_ns':time.monotonic_ns(),**kw};x['hash']=digest(canonical(x))
    with (root/'LEDGER.jsonl').open('ab') as f:f.write(canonical(x)+b'\n');f.flush();os.fsync(f.fileno())
    return x

def stage(name):
    assert name in STAGES
    rows=events();seen=[r['stage'] for r in rows if r['event']=='STAGE']
    if seen and seen[-1]==name:return
    expected=STAGES[len(seen)]
    if name!=expected:raise RuntimeError('out-of-order stage '+name+' expected '+expected)
    event('STAGE',stage=name)

def inventory():
    files={}
    for p in HERE.rglob('*'):
        if p.is_file() and p.suffix in ['.py','.cpp','.h']:files[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    for p in (OUT/'pinned-source').rglob('*'):
        if p.is_file():files[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    for d in [OUT/'native-build/bin',OUT/'worker-bin']:
        for p in d.glob('*'):
            if p.suffix in ['.exe','.dll']:files[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    for name in ['PROTOCOL.json','COHORT.json','QUEUE.json','ASSET_ENVIRONMENT.json','LOADED_MODULE_IDENTITY.json','HISTORICAL_EXPECTED.json']:
        files[str((DOC/name).relative_to(ROOT)).replace('\\','/')]=sha(DOC/name)
    for p in (OUT/'inputs').rglob('*'):
        if p.is_file():files[str(p.relative_to(ROOT)).replace('\\','/')]=sha(p)
    return files

def check_freeze(root=ROOT,doc=DOC,full=False):
    x=read(doc/'FREEZE.json')
    for name,h in x['files'].items():
        p=root/name
        # Large immutable binaries and complete upstream are guarded by metadata per
        # unit; byte checks also run at prediction and native boundaries.
        if not full and name.startswith('work/') and name not in x['critical_files']:
            stat=p.stat();assert {'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}==x['metadata'][name],name
        else:assert sha(p)==h,name
    for role,v in read(doc/'ASSET_ENVIRONMENT.json')['files'].items():
        p=Path(v['path']);s=p.stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns'],role
        if full:assert sha(p)==v['sha256'],role
    if (doc/'LOADED_MODULE_IDENTITY.json').exists():
        for name,v in read(doc/'LOADED_MODULE_IDENTITY.json')['modules'].items():
            p=Path(name);s=p.stat();assert s.st_size==v['bytes'] and s.st_mtime_ns==v['mtime_ns'],name
            if full:assert sha(p)==v['sha256'],name

def verify_seal(root=ROOT,doc=DOC,out=OUT,full=False):
    check_freeze(root,doc)
    seal=read(out/'PREDICTION_SEAL.json');assert seal['freeze_sha256']==sha(doc/'FREEZE.json')
    queue=read(doc/'QUEUE.json');expected={q['id'] for q in queue if q['condition'] in ['H0','H1']}
    assert set(seal['predictions'])==expected and len(expected)==258
    for key,item in seal['predictions'].items():
        p=root/item['result'];assert sha(p)==item['sha256'];row=read(p);assert row['valid'] and row['unit_id']==key
        for f,h in row['files'].items():
            q=p.parent/f
            if full or not item.get('metadata') or q.name=='tape.jsonl':assert sha(q)==h
            else:
                stat=q.stat();assert {'bytes':stat.st_size,'mtime_ns':stat.st_mtime_ns}==item['metadata'][f]
        assert row['ids']==item['ids'] and row['endpoint']==item['endpoint']
    rows=events(out);seals=[r for r in rows if r['event']=='PREDICTION_SEALED'];assert len(seals)==1 and seals[0]['seal_sha256']==sha(out/'PREDICTION_SEAL.json')
    ends=[r for r in rows if r['event']=='UNIT_VALID' and r.get('condition') in ['R','H0','H1']]
    assert len(ends)==387 and max(r['sequence'] for r in ends)<seals[0]['sequence']
    for r in rows:
        if r['event']=='NATIVE_FORMAL_START':assert r['sequence']>seals[0]['sequence']
    return seal

def native_guard(condition,root=ROOT,doc=DOC,out=OUT):
    verify_seal(root,doc,out)
    state=read(out/'STATUS.json');assert state['stage']==condition and condition in ['N0','N1']
    mode=read(out/'SEAL_MODE.json');assert mode['mode'] in ['REMOTE_BEFORE_NATIVE','LOCAL_SEAL_ONLY']
    if mode['mode']=='REMOTE_BEFORE_NATIVE':assert mode['readback_pass'] and mode['seal_sha256']==sha(out/'PREDICTION_SEAL.json')
    if condition=='N1':assert read(doc/'BASELINE_RECHECK.json')['status']=='PASS'

def committed(indices,ids,stops,count):
    if indices!=list(range(1,len(ids)+1)) or count!=len(ids) or not ids or len(ids)>128:raise ValueError('invalid committed stream')
    if any(type(i)!=int or i<0 or i>=151936 for i in ids):raise ValueError('invalid committed ID')
    terminal=ids[-1] in EOG
    expected=(['limit','EOS'] if terminal else ['limit']) if len(ids)==128 else ['EOS']
    if stops!=expected or any(i in EOG for i in ids[:-1]) or len(ids)<128 and not terminal:raise ValueError('invalid EOG/cap boundary')
    return {'ids':ids,'endpoint':'EOS' if terminal else 'limit','stop_markers':stops}
