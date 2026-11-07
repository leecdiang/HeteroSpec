from host import *
import zipfile
def main():
    delivery=Path('F:/rtx172-delivery');delivery.mkdir(exist_ok=True);out=delivery/'frozen-runtime.zip';index={}
    with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        def add(p,name):index[name]=dict(sha256=sha(p),bytes=p.stat().st_size);z.write(p,name)
        for p in sorted((ROOT/'candidate07').glob('*.dll')):
            assert sha(p)==sha(ROOT/'oracle02'/p.name);add(p,'modules/'+p.name)
        for role,label in [('candidate','candidate07'),('oracle','oracle02')]:
            add(ROOT/label/'worker.exe',role+'/worker.exe');add(ROOT/label/'binding.json',role+'/binding.json');add(ROOT/label/'compiled-source.cpp',role+'/compiled-source.cpp')
            for arg in read(ROOT/label/'binding.json')['commands'][1]:
                p=Path(arg)
                if p.suffix=='.a' and p.is_file():add(p,'libraries/'+role+'/'+p.name)
        for p in Path('E:/tpds167/build01').glob('configure-*.json'):add(p,'historical-core-commands/'+p.name)
        z.writestr('index.json',json.dumps(index,sort_keys=True))
    with zipfile.ZipFile(out) as z:assert z.testzip() is None
    put(ROOT/'RUNTIME_KIT.json',dict(sha256=sha(out),bytes=out.stat().st_size,files=index,compiler='ziglang0.16.0; Windows original host bindings',verification='archive CRC; independent restored download still required',model_included=False))
    print(out,out.stat().st_size)
if __name__=='__main__':main()
