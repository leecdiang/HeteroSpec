"""Small, self-contained reconstruction of the actual GPU boundary diagnosis."""
from build_host import *
from native_adapter import RUNS
from archive_host import STORE
from restore_delivered_host import restore
from active_kv import parse
import zlib,zipfile,tempfile

def main():
    out=Path('D:/rtx184-examples');out.mkdir(exist_ok=False);base=RUNS/'D-boundary-diagnostic-v1';prefix=str(base.resolve()).casefold();source=json.loads((STORE/'D-completed-main-and-priming.json').read_bytes());rows=[r for r in source['files'] if r['path'].casefold().startswith(prefix+'\\')];assert rows
    archive=out/'D-boundary-repro.zip';seen=set()
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
        def chunk(h,data):
            if h in seen:return
            assert hashlib.sha256(zlib.decompress(data)).hexdigest()==h;z.writestr('chunks/'+h[:2]+'/'+h,data);seen.add(h)
        for row in rows:
            for h in row['chunks']:chunk(h,(STORE/'chunks'/h[:2]/h).read_bytes())
        for p in base.rglob('*'):
            if not p.is_file():continue
            raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest();chunk(h,zlib.compress(raw,1));rows.append(dict(path=str(p.resolve()),bytes=len(raw),sha256=h,chunks=[h]))
        z.writestr('FILES.json',json.dumps(dict(files=rows)));z.writestr('PROFILE.json',(ROOT/'QWEN_PROFILE.json').read_bytes());z.writestr('DIAGNOSIS.json',(ROOT/'D-BOUNDARY-DIAGNOSIS.json').read_bytes())
    restored=out/'restored';restore(archive,str(base),restored);profile=json.loads((ROOT/'QWEN_PROFILE.json').read_bytes());comparison=[]
    for name in ('actual4','boundarycut1plus3'):
        vectors=[sha(restored/'native'/name/str(n)/'frontier.f32')==sha(restored/'native/0'/str(n)/'frontier.f32') for n in range(768,772)]
        a,_=parse((restored/'native'/name/'771/sequence.bin').read_bytes(),list(range(771)),profile);b,_=parse((restored/'native/0/771/sequence.bin').read_bytes(),list(range(771)),profile)
        comparison.append(dict(name=name,vectors_equal=vectors,active_kv_equal=a==b))
    assert comparison[0]['vectors_equal']==[False]*4 and not comparison[0]['active_kv_equal'];assert comparison[1]['vectors_equal']==[True]*4 and comparison[1]['active_kv_equal']
    put(ROOT/'D-DELIVERABLE-RECONSTRUCTION.json',dict(archive=str(archive),archive_sha256=sha(archive),bytes=archive.stat().st_size,files=len(rows),unique_chunks=len(seen),from_actual_GPU_captures=True,CPU_reconstruction_only=True,comparison=comparison))
    print('Actual diagnostic restored and independently recomputed',archive.stat().st_size,flush=True)

if __name__=='__main__':main()
