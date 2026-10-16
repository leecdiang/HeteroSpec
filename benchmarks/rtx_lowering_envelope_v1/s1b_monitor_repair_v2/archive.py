"""Lossless split ZIP stream. Two archive sets only; no assembled third copy."""
import io,hashlib,json,zipfile,bisect
from pathlib import Path,PurePosixPath
from common import V,save,load,sha
ESSENTIAL=['F0.json','PLAN.json','CPU_EXPECTED.json','CAS_INDEX.json','ABI_EXPORTS.json','common.py','audit.py','identity.py','admission.py','readiness_policy.py','bounded.py','lifecycle.py','transport_lifecycle.py','run_s1b.py','offline_s1b.py','archive.py','evidence_s1b.py','native_cost.cpp','graph_base.h','hs113_graph.h','core_gate.h','s1b_gate.h','timing_loop.h','s1b_clean.exe','s1b_trace.exe','BUDGET.json','AMENDMENT.md','PROTOCOL.md','AUTHENTICATED_F0.json','REMOTE_F0_BYTES.json','strict_lifecycle.py','monitor_contract.py','monitor_worker.py','monitor_audit.py','identified_state.py','exact_binding.py','CENSUS_EXACT_AUTHENTICATED.json']
ESSENTIAL += ['cpu_job.py','resource_guard.py'] # Actual sampler resource checks and Job structures.
class SplitWriter(io.RawIOBase):
    def __init__(self,root,cap):self.root=Path(root);self.root.mkdir(exist_ok=False);self.cap=cap;self.pos=0;self.files=[];self.f=None;self.total_hash=hashlib.sha256()
    def writable(self):return True
    def seekable(self):return False
    def tell(self):return self.pos
    def write(self,data):
        original=len(data);self.total_hash.update(data)
        while data:
            if self.f is None or self.f.tell()==self.cap:
                if self.f:self.f.close()
                p=self.root/f'raw-{len(self.files):03d}.zip.part';self.files.append(p);self.f=p.open('xb')
            n=min(len(data),self.cap-self.f.tell());self.f.write(data[:n]);data=data[n:];self.pos+=n
        return original
    def finish(self):
        if self.f:self.f.close();self.f=None
        return dict(bytes=self.pos,sha256=self.total_hash.hexdigest(),parts=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in self.files])
class PartsReader(io.RawIOBase):
    def __init__(self,root,parts):
        self.paths=[Path(root)/p['name'] for p in parts];self.offset=[0];self.pos=0
        for p,r in zip(self.paths,parts):assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];self.offset.append(self.offset[-1]+r['bytes'])
    def readable(self):return True
    def seekable(self):return True
    def tell(self):return self.pos
    def seek(self,offset,whence=0):
        dest=offset if whence==0 else self.pos+offset if whence==1 else self.offset[-1]+offset
        assert 0<=dest<=self.offset[-1];self.pos=dest;return dest
    def read(self,n=-1):
        n=self.offset[-1]-self.pos if n<0 else min(n,self.offset[-1]-self.pos);out=bytearray()
        while n:
            i=bisect.bisect_right(self.offset,self.pos)-1;take=min(n,self.offset[i+1]-self.pos)
            with self.paths[i].open('rb') as f:f.seek(self.pos-self.offset[i]);data=f.read(take)
            assert len(data)==take;out.extend(data);self.pos+=take;n-=take
        return bytes(out)
def package(root,out,frozen=V,cap=40*1024**2):
    root=Path(root);members=[(p,'raw/'+p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file()]
    members += [(Path(frozen)/name,'frozen/'+name) for name in ESSENTIAL]
    assert sum(p.stat().st_size for p,n in members if n.startswith('frozen/'))<=16*1024**2
    manifest={name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p,name in members}
    writer=SplitWriter(out,cap)
    with zipfile.ZipFile(writer,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p,n in members:assert not p.is_symlink();z.write(p,n)
        z.writestr('MANIFEST.json',json.dumps(manifest,separators=(',',':'))+'\n')
    descriptor=writer.finish();descriptor['members']=len(manifest);f=load(Path(frozen)/'F0.json');descriptor.update(run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(Path(frozen)/'F0.json'));save(Path(out)/'ARCHIVE.json',descriptor);return descriptor
def restore(parts_root,descriptor,out,limit):
    out=Path(out);assert not out.exists();reader=PartsReader(parts_root,descriptor['parts']);h=hashlib.sha256()
    while True:
        b=reader.read(1024*1024)
        if not b:break
        h.update(b)
    assert h.hexdigest()==descriptor['sha256'];reader.seek(0)
    with zipfile.ZipFile(reader) as z:
        names=z.namelist();assert len(names)==len(set(names)) and len(names)<40000 and sum(p.file_size for p in z.infolist())<limit
        manifest=json.loads(z.read('MANIFEST.json'));assert set(names)==set(manifest)|{'MANIFEST.json'}
        out.mkdir(parents=True)
        for name in names:
            rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in name and ':' not in name
            data=z.read(name)
            if name!='MANIFEST.json':assert len(data)==manifest[name]['bytes'] and hashlib.sha256(data).hexdigest()==manifest[name]['sha256']
            p=out/name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(data)
    return dict(members_verified=len(manifest),archive_sha256=descriptor['sha256'])
