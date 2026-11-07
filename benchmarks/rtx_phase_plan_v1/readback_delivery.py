"""Authenticated bounded-cache readback of selected actual GPU evidence.

This verifies transport and recomputes saved vector/active-KV comparisons. It
does not execute a model or qualify a newly compiled runtime.
"""
from deliver_host import *
import bisect,re,datetime
from native_metadata import fields

class RemoteParts(io.RawIOBase):
    def __init__(self,index,cache):
        self.rows=index['parts'];self.cache=cache;cache.mkdir();self.position=0;self.starts=[0];self.loaded=[];self.downloads=[]
        for r in self.rows:
            assert re.fullmatch(r'raw-evidence\.zip\.part\d{3}',r['name'])
            self.starts.append(self.starts[-1]+r['bytes'])
    def seekable(self):return True
    def readable(self):return True
    def tell(self):return self.position
    def seek(self,n,whence=0):
        self.position=n if whence==0 else self.position+n if whence==1 else self.starts[-1]+n
        assert self.position>=0;return self.position
    def part(self,i):
        row=self.rows[i];p=self.cache/row['name']
        if i in self.loaded:self.loaded.remove(i);self.loaded.append(i);return p
        if len(self.loaded)>=2:
            old=self.cache/self.rows[self.loaded.pop(0)]['name'];assert old.resolve().parent==self.cache.resolve();old.unlink()
        assert shutil.disk_usage(self.cache).free-row['bytes']>=20*1024**3
        began=time.monotonic();subprocess.run([GH,'release','download',TAG,'--repo',REPO,'--pattern',row['name'],'--dir',str(self.cache)],check=True)
        assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
        self.downloads.append(dict(part=row['name'],bytes=row['bytes'],sha256=row['sha256'],wall_s=time.monotonic()-began));self.loaded.append(i)
        return p
    def read(self,n=-1):
        n=min(n if n>=0 else self.starts[-1],self.starts[-1]-self.position);out=[]
        while n>0:
            i=bisect.bisect_right(self.starts,self.position)-1;offset=self.position-self.starts[i];take=min(n,self.rows[i]['bytes']-offset)
            with self.part(i).open('rb') as f:f.seek(offset);raw=f.read(take)
            assert len(raw)==take;out.append(raw);self.position+=take;n-=take
        return b''.join(out)

def main():
    assert not Path('D:/HeteroSpec-PC/RTX_EXPERIMENT.lock').exists()
    assert (ROOT/'GPU_STOP.json').exists()
    began=time.monotonic();dest=Path('D:/rtx188-readback');dest.mkdir(exist_ok=False)
    published=json.loads((ROOT/'ARTIFACT_DELIVERY_PUBLISHED.json').read_bytes())
    subprocess.run([GH,'release','download',TAG,'--repo',REPO,'--pattern','raw-evidence.zip.parts.json','--dir',str(dest)],check=True)
    index=dest/'raw-evidence.zip.parts.json';assert sha(index)==published['index_asset']['sha256']
    reader=RemoteParts(json.loads(index.read_bytes()),dest/'cache');restored={};records=[]
    prefixes=[ROOT/'runs/Qwen-matrix-8-R',ROOT/'runs/Qwen-exact-version-matrix-8-SIMPLE',ROOT/'runs/Qwen-exact-version-matrix-8-LOCAL']
    wanted=[str(p/'native/h767-q4/captures/771'/name).casefold() for p in prefixes for name in ('frontier.f32','sequence.bin')]
    with zipfile.ZipFile(reader) as archive:
        manifest=json.loads(archive.read('FILES.json'));rows={str(Path(r['path'])).casefold():r for r in manifest['files']}
        for number,key in enumerate(wanted):
            row=rows[key];p=dest/'restored'/str(number)/Path(row['path']).name;p.parent.mkdir(parents=True,exist_ok=True)
            assert shutil.disk_usage(dest).free-row['bytes']>=20*1024**3
            if row['sha256'] in restored:os.link(restored[row['sha256']],p)
            else:
                h=hashlib.sha256();size=0
                with p.open('xb') as f:
                    for chunk in row['chunks']:
                        raw=zlib.decompress(archive.read('chunks/'+chunk[:2]+'/'+chunk));assert hashlib.sha256(raw).hexdigest()==chunk;h.update(raw);size+=len(raw);f.write(raw)
                assert size==row['bytes'] and h.hexdigest()==row['sha256'];restored[row['sha256']]=p
            records.append(dict(original=row['path'],restored=str(p),sha256=sha(p),bytes=p.stat().st_size))
    from develop import profile
    from active_kv import parse
    native=fields(ROOT/'runs/Qwen-matrix-8-R/native/result.json',['model_structure']);spec=profile(native,'Qwen')
    vectors=[Path(r['restored']).read_bytes() for r in records if r['original'].endswith('frontier.f32')]
    states=[parse(Path(r['restored']).read_bytes(),list(range(771)),spec)[0] for r in records if r['original'].endswith('sequence.bin')]
    assert len(vectors)==len(states)==3 and vectors[0]==vectors[1]==vectors[2] and states[0]==states[1]==states[2]
    put(ROOT/'ARTIFACT_READBACK.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),index_sha256=sha(index),files=records,downloaded_parts=reader.downloads,all_downloaded_part_chunk_file_hashes_verified=True,full_requested_frontier_equal=True,complete_active_KV_771_positions_all_layers_equal=True,new_GPU_requests=0,scope='Selected retained-boundary actual-GPU state/vector readback, not full-bundle download or external native replication.',wall_s=time.monotonic()-began,GPU_work_remained_stopped=True))
    print('Authenticated selected GPU vectors and active states restored and recomputed',len(records),'files',flush=True)

if __name__=='__main__':main()
