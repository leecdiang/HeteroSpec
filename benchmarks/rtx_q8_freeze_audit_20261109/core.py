"""Independent offline audit primitives. No original executors/validators imported."""
from pathlib import Path
import collections,datetime,hashlib,json,sqlite3,struct,subprocess,time
import numpy as np

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/'evidence'
ORIGINAL=REPO.parent/'q8rtx211/benchmarks/rtx_q8_transfer_20261109'
RECORDS=ORIGINAL/'results_20261109'
WORK=Path('D:/rtx211-q8-20261109')
ARCHIVE=REPO.parent/'q8rtx211-evidence-20261109'
PIN='ba5b4c8e01d50d4bfaab1ac3908f798347be063a'
R_SHA='73113940c38b24093a73d5bfefb46852af66b703c4923379fdd972cba603e249'

def digest(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(name,value):
    p=OUT/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(value,f,indent=2,ensure_ascii=False)
def git(*args):return subprocess.check_output(['git','-C',str(REPO),*args])
def stamp(v):return datetime.datetime.fromtimestamp(v,datetime.timezone.utc).astimezone(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
def ledger():
    c=sqlite3.connect((WORK/'ledger.sqlite').as_uri()+'?mode=ro',uri=True);c.row_factory=sqlite3.Row
    rows=[dict(x) for x in c.execute('SELECT * FROM attempts ORDER BY started')];c.close();return rows

class Reader:
    def __init__(self):
        index=read(ARCHIVE/'ARCHIVE_INDEX.json');self.index={x['path']:x for x in index['files']}
        self.seen={};self.vector_cache={};self.state_cache={};self.bytes=0;self.errors=[]
    def raw(self,p):
        p=Path(p).resolve();b=p.read_bytes();h=digest(b)
        if p.is_relative_to(WORK.resolve()):name='work/'+p.relative_to(WORK.resolve()).as_posix()
        elif p.is_relative_to(RECORDS.resolve()):name='records/'+p.relative_to(RECORDS.resolve()).as_posix()
        else:name=None
        if name:
            assert name in self.index,('Not in pre-existing full archive',name)
            e=self.index[name];assert len(b)==e['bytes'] and h==e['sha256'],('Archive commitment mismatch',name)
        self.bytes+=len(b);self.seen[str(p)]=dict(bytes=len(b),sha256=h,archive_path=name)
        return b,h
    def vector(self,p):
        key=str(Path(p).resolve())
        if key not in self.vector_cache:
            b,h=self.raw(p);assert len(b)==151936*4,('Full vocabulary size',p,len(b))
            a=np.frombuffer(b,dtype='<f4');assert bool(np.isfinite(a).all()),('Nonfinite vector',p)
            self.vector_cache[key]=dict(sha256=h,greedy=int(np.argmax(a)),dimensions=len(a))
        return self.vector_cache[key]
    def state(self,p,n):
        key=(str(Path(p).resolve()),n)
        if key in self.state_cache:return self.state_cache[key]
        raw,h=self.raw(p);b=memoryview(raw);offset=0
        def scalar(fmt):
            nonlocal offset
            size=struct.calcsize('<'+fmt);assert offset+size<=len(b),'Truncated state header'
            out=struct.unpack_from('<'+fmt,b,offset)[0];offset+=size;return out
        def payload(size):
            nonlocal offset
            assert 0<=size<=len(b)-offset,'Truncated state tensor'
            v=b[offset:offset+size];offset+=size;return v
        assert scalar('I')==0xaf143cd8 and scalar('i')==0
        assert scalar('I')==1 and scalar('I')==n and 0<n<=1024
        for i in range(n):assert (scalar('i'),scalar('I'),scalar('i'))==(i,1,0),'Non-dense sequence mapping'
        trans=scalar('I');assert trans in (0,1) and scalar('I')==36
        # A different canonical byte order than the old validator: complete
        # K layers then complete token-major V layers. No old parser imported.
        active=hashlib.sha256();active.update(struct.pack('<III',n,36,1024))
        for i in range(36):
            assert scalar('i')==1 and scalar('Q')==2048,'K type/row width'
            active.update(payload(n*2048))
        for i in range(36):
            assert scalar('i')==1,'V type'
            if trans:
                assert (scalar('I'),scalar('I'))==(2,1024),'V transposed layout'
                a=np.frombuffer(payload(n*2048),dtype='<u2').reshape(1024,n).T.copy()
                active.update(a.tobytes())
            else:
                assert scalar('Q')==2048;active.update(payload(n*2048))
        assert offset==len(b),'Unregistered trailing state bytes'
        result=dict(active_sha256=active.hexdigest(),active_bytes=n*36*4096,raw_sha256=h,positions=n,transposed_V=bool(trans))
        self.state_cache[key]=result;return result

def inventory():
    started=time.monotonic();attempts=ledger();paths=sorted(RECORDS.rglob('JOB_MANIFEST*.json'))+sorted((RECORDS/'oracle-manifests').glob('*.json'))
    manifests=[];members=collections.defaultdict(list)
    for p in paths:
        rel=p.relative_to(ORIGINAL.parent.parent).as_posix()
        history=git('log','--reverse','--format=%H %aI','--',rel).decode().splitlines()
        m=read(p);first=history[0].split(' ',1) if history else [None,None]
        # Verify original file has the pinned Git content modulo checkout EOL.
        committed=git('show',PIN+':'+rel).replace(b'\r\n',b'\n');assert committed==p.read_bytes().replace(b'\r\n',b'\n')
        manifests.append(dict(path=rel,first_commit=first[0],commit_time=first[1],self_reported_utc=m.get('utc'),jobs=len(m['jobs']),requests=sum(x['requests'] for x in m['jobs'])))
        for j in m['jobs']:members[j['id']].append(dict(path=rel,commit=first[0],time=first[1],job=j))
    details=[]
    for a in attempts:
        folder=WORK/'runs'/a['id'];native=folder/'native';job=read(folder/'JOB.json');assert any(x['job']==job for x in members[a['id']]),('Unmatched executed job',a['id'])
        outputs=list(native.rglob('*.f32'))+list(native.rglob('receipt.json'))
        first=min(outputs,key=lambda p:p.stat().st_mtime_ns) if outputs else None
        details.append(dict(**a,start_bjt=stamp(a['started']),end_bjt=stamp(a['ended']),first_output_file=str(first) if first else None,
            first_output_bjt=stamp(first.stat().st_mtime) if first else None,first_output_basis='Original filesystem mtime; not an independent external timestamp',
            manifest=members[a['id']][0]['path'],freeze_commit=members[a['id']][0]['commit'],freeze_commit_time=members[a['id']][0]['time'],
            executable_sha256=job['exe_sha256'],expected_error=job.get('expect_error')))
    state=dict(pin=PIN,new_GPU_requests=0,attempts=details,manifests=manifests,
        timing_provenance='Git author times and local remote-ref reflog are local records; native ledger is durable recorded wall time; capture filesystem mtime is local. None alone is cryptographic external proof of historical publication time.',
        remote_reflog=git('reflog','show','--date=iso-strict','origin/codex/rtx-q8-results-20261109').decode(),wall_seconds=time.monotonic()-started)
    put('TIMELINE.json',state)
    print(json.dumps(dict(attempts=len(details),manifests=len(manifests),first=details[0]['start_bjt'],last=details[-1]['end_bjt'])),flush=True)

if __name__=='__main__':inventory()
