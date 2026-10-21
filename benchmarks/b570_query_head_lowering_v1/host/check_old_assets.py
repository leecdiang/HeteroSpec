"""Stream-hash fixed original runtime/model files; never loads model/backend."""
import argparse, hashlib, pathlib
from common import ROOT, load, save, sha, modules

def streamsha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        for part in iter(lambda:f.read(8*1024**2),b''):h.update(part)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--old',type=pathlib.Path,required=True);a=p.parse_args();before=modules();runtime=load(a.old/'p0/RUNTIME.json');rows=[]
    def visit(x):
        if isinstance(x,dict):
            if isinstance(x.get('path'),str) and 'sha256' in x and pathlib.Path(x['path']).is_file():
                actual=streamsha(x['path']);assert actual==x['sha256'],x['path'];rows.append(dict(path=x['path'],bytes=pathlib.Path(x['path']).stat().st_size,sha256=actual))
            for value in x.values():visit(value)
        elif isinstance(x,list):
            for value in x:visit(value)
    visit(runtime)
    assert sha(a.old/'p0/F0_EXECUTION.json')=='29cf422ef631edfa45ba55b56947926e1977070b8957dbc362e4e5581401d6e8'
    save(ROOT/'host/OLD_ASSET_RECHECK.json',dict(files=rows,F0_unchanged=True,model_processes=0,model_requests=0,GPU_starts=0,
         scope='Local-byte identity only; model-byte hashing is not model loading or checkpoint ancestry certification.',modules_before=before,modules_after=modules()))
    print(dict(unchanged_files=len(rows),model_files=sum(x['path'].endswith('.gguf') for x in rows),GPU_starts=0))

if __name__=='__main__':main()
