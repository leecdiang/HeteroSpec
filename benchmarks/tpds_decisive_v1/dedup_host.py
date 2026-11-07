"""Verified same-volume evidence deduplication; logical files stay present."""
from build_host import sha,put,ROOT
from pathlib import Path
import os,time
def main():
    pool=Path('D:/rtx184-cas');pool.mkdir(exist_ok=True);rows=[]
    for base in [Path('D:/rtx184-qualification'),Path('D:/rtx184-runs')]:
        for p in sorted(base.rglob('*')):
            if not p.is_file() or not (p.suffix in ('.bin','.f32') or 'cas' in p.parts):continue
            h=sha(p);dest=pool/h[:2]/h;dest.parent.mkdir(exist_ok=True)
            if dest.exists():
                assert sha(dest)==h
                if os.path.samefile(p,dest):continue
                temp=p.with_name(p.name+'.dedup');assert not temp.exists();os.link(dest,temp);os.replace(temp,p)
            else:os.link(p,dest)
            rows.append(dict(path=str(p),sha256=h,bytes=p.stat().st_size))
    put(ROOT/('EVIDENCE_DEDUP-'+str(time.time_ns())+'.json'),dict(method='SHA256 verified same-volume hardlinks; all paths retained',files=rows));print('deduplicated',len(rows),'paths',flush=True)
if __name__=='__main__':main()
