"""Bounded exact ranges from the pinned official publisher; never loads a GPU.

Transport epochs/failed parts are retained. Only a complete exact-size/SHA object
is linked into the final destination. Redirect headers remain private.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, os, re, shutil, subprocess, sys, time
sys.path.insert(0,str(Path(__file__).parents[1]/'shared'))
from experiment import read,save,require,sha

def acquire(spec,out,workers=8):
    out=Path(out).resolve();out.parent.mkdir(parents=True,exist_ok=True)
    size=spec['bytes'];require(spec['url'].startswith('https://huggingface.co/Qwen/'),'Pinned official publisher only')
    if out.exists():require(out.stat().st_size==size and sha(out)==spec['sha256'],'Existing object mismatch');return
    require(1<=workers<=8,'At most eight network workers')
    require(shutil.disk_usage(out.parent).free>=size+20*1024**3,'Keep20GiB after transfer')
    parts=out.parent/'range-epoch-02';parts.mkdir(exist_ok=True);chunk=128*1024**2;count=(size+chunk-1)//chunk
    def fetch(i):
        start=i*chunk;end=min(size,start+chunk)-1;wanted=end-start+1;dest=parts/f'part-{i:05d}'
        if dest.exists():require(dest.stat().st_size==wanted,'Completed range size changed');return dest
        for attempt in range(6):
            tmp=parts/f'part-{i:05d}-attempt-{attempt:02d}.body.private';head=tmp.with_suffix('.headers.private');receipt=tmp.with_suffix('.json')
            require(not tmp.exists() and not receipt.exists(),'Preserve failed acquisition attempt; use a new epoch')
            url=spec['url']+f'?download=true&d14range={i}&attempt={attempt}'
            began=time.monotonic();r=subprocess.run(['curl','-4','-fsSL','--connect-timeout','15','--max-time','180','--max-filesize',str(wanted),
                '--range',f'{start}-{end}','--dump-header',str(head),'--output',str(tmp),'--write-out','%{http_code} %{size_download} %{time_total}',url],capture_output=True,text=True)
            text=head.read_text() if head.exists() else '';ranges=re.findall(r'(?im)^content-range:\s*bytes (\d+)-(\d+)/(\d+)\s*$',text)
            good=r.returncode==0 and ranges and tuple(map(int,ranges[-1]))==(start,end,size) and tmp.stat().st_size==wanted
            save(receipt,dict(part=i,attempt=attempt,start=start,end=end,expected_total=size,returncode=r.returncode,wall_s=time.monotonic()-began,
                received_bytes=tmp.stat().st_size if tmp.exists() else 0,status='COMPLETE' if good else 'FAILED_RETAINED',canonical_url=spec['url']))
            if good:os.link(tmp,dest);print('COMPLETE_RANGE',i,count,wanted,flush=True);return dest
        raise RuntimeError('Bounded official range attempts exhausted: '+str(i))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:list(pool.map(fetch,range(count)))
    final=out.with_suffix(out.suffix+'.assembling');require(not final.exists(),'Preserve assembly epochs')
    with final.open('xb') as f:
        for i in range(count):
            with (parts/f'part-{i:05d}').open('rb') as src:shutil.copyfileobj(src,f,4*1024**2)
        f.flush();os.fsync(f.fileno())
    require(final.stat().st_size==size and sha(final)==spec['sha256'],'Full official model SHA mismatch; retain all parts')
    os.link(final,out)
    save(out.parent/'ACQUISITION.json',dict(status='EXACT_BYTES_VERIFIED',canonical_url=spec['url'],revision=spec['revision'],bytes=size,sha256=spec['sha256'],
        parts=count,network_workers=workers,GPU_requests=0,failed_parts_retained=True,signed_redirect_headers_public=False))
    print('EXACT_MODEL_VERIFIED',spec['sha256'],size,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('manifest',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--workers',type=int,default=8);a=p.parse_args();acquire(read(a.manifest)['target'],a.out,a.workers)
