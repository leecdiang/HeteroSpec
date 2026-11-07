"""Authenticated archive transport; fixed identity encoding, no scientific replay."""
import argparse
import json
from pathlib import Path
import subprocess
from prepare import ROOT,save,sha

def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--destination',required=True);a=p.parse_args()
    out=Path(a.destination);out.mkdir(exist_ok=False);results=[]
    for rel in ('raw_archive/RAW_CPU.zip','RAW_ARCHIVE_MANIFEST.json'):
        path=out/Path(rel).name
        with path.open('xb') as f:
            x=subprocess.run(['gh','api','repos/leecdiang/HeteroSpec/contents/benchmarks/rtx_reference_packing_v1/'+rel+'?ref='+a.commit,
                 '-H','Accept: application/vnd.github.raw','-H','Accept-Encoding: identity'],stdout=f,stderr=subprocess.PIPE)
        (out/(path.name+'.stderr.log')).write_bytes(x.stderr)
        assert x.returncode==0,(x.returncode,x.stderr)
        assert path.read_bytes()==(ROOT/rel).read_bytes()
        results.append(dict(path=rel,bytes=path.stat().st_size,sha256=sha(path)))
    save(ROOT/'AUTHENTICATED_ARCHIVE_READBACK.json',dict(commit=a.commit,files=results,authenticated_remote_bytes=True,encoding='identity',download_directory=str(out)))
    print(json.dumps(dict(commit=a.commit,files=results)))
if __name__=='__main__':main()
