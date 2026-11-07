"""Read selected RTX metadata from complete hash-verified published ZIP parts."""
from pathlib import Path
import concurrent.futures,json,sys,time,zipfile
from recover_exposure_index import session
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'b570_llama_companion_v1'))
from common import read,write,need,sha

def main(root):
    root=Path(root);index=read(root/'FULL_RAW_ACCESS.json');selected=read(root/'EXPOSURE_SELECTION.json');assets={a['name']:a for a in read(root/'RELEASE.json')['assets']};pins={p['name']:p for p in index['parts']};get=session()
    download=root/'download';download.mkdir(exist_ok=True);restored=root/'restored';restored.mkdir(exist_ok=True)
    def one(name):
        pin=pins[name];dest=download/name
        if not dest.exists():
            for attempt in range(8):
                partial=download/(name+'.attempt-'+str(attempt))
                if partial.exists():continue
                try:
                    with get(assets[name]['url']+'?b570='+str(time.time_ns()),'application/octet-stream') as response,partial.open('xb') as output:
                        while b:=response.read(4*1024**2):output.write(b)
                    need(partial.stat().st_size==pin['bytes'] and sha(partial)==pin['sha256'],'part identity');partial.rename(dest);break
                except Exception as exc:print('RETAINED_FAILURE',name,attempt,type(exc).__name__,flush=True)
        need(dest.exists() and sha(dest)==pin['sha256'],'verified part unavailable')
        count=0
        with zipfile.ZipFile(dest) as z:
            for f in selected:
                if f['part']!=name:continue
                p=restored/f['path'];need(p.resolve().is_relative_to(restored.resolve()),'safe member');p.parent.mkdir(parents=True,exist_ok=True)
                if not p.exists():p.write_bytes(z.read(f['path']))
                need(p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],'member identity');count+=1
        print('VERIFIED',name,count,flush=True);return {'part':name,'members':count,'sha256':sha(dest)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(one,sorted({x['part'] for x in selected})))
    write(root/'EXPOSURE_READBACK.json',{'status':'VERIFIED','members':len(selected),'parts':results,'selection_sha256':sha(root/'EXPOSURE_SELECTION.json'),'published_index_sha256':sha(root/'FULL_RAW_ACCESS.json')})

if __name__=='__main__':main(sys.argv[1])
