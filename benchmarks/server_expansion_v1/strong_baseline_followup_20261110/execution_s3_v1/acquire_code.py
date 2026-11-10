"""Bounded, resumable CPU data acquisition. No model or CUDA imports.

Prospective code universe: complete valid and test plus the first train shard
from one immutable CodeContests revision. No model output selects this universe.
All statements in those complete files must later enter the eligibility table.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import urllib.request

REVISION='802411c3010cb00d1b05bad57ca77365a3c699d6'
FILES=(
 ('data/valid-00000-of-00001-5e672c5751f060d3.parquet',51829044,'02e8c1ccedae716f1e43cc813fcb7823c3db666ea92638820aba80e8cef451ab'),
 ('data/test-00000-of-00001-9c49eeff30aacaa8.parquet',63077400,'aa426cbdb202bf8703b658bcb31fd1878ca7cfd33ca07d3b703dc94ca6a2b651'),
 ('data/train-00000-of-00039-e991a271dbfa9925.parquet',180227735,'950bfdefde1f274edf93963e7e23c93ab16034de344aa7b7c32d14145e8d5232'),
)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for x in iter(lambda:f.read(4*1024**2),b''):h.update(x)
    return h.hexdigest()


def run(output,seconds):
    output.mkdir(parents=True,exist_ok=True);started=time.monotonic();records=[]
    for name,length,digest in FILES:
        path=output/Path(name).name;part=path.with_suffix(path.suffix+'.partial')
        began=time.monotonic();url='https://huggingface.co/datasets/deepmind/code_contests/resolve/'+REVISION+'/'+name
        try:
            if path.exists():
                if path.stat().st_size!=length or sha(path)!=digest:raise ValueError('Existing complete data differs; preserve and stop')
                records.append(dict(path=name,status='EXISTING_BYTES_VERIFIED',bytes=length,sha256=digest));continue
            offset=part.stat().st_size if part.exists()else 0
            if offset>length:raise ValueError('Partial file exceeds fixed length')
            if offset<length:
                request=urllib.request.Request(url+'?download=true&hs_sb217_offset='+str(offset))
                if offset:request.add_header('Range','bytes='+str(offset)+'-')
                with urllib.request.urlopen(request,timeout=30)as response:
                    if offset and (response.status!=206 or not response.headers.get('Content-Range','').startswith('bytes '+str(offset)+'-')):
                        raise ValueError('Resume response does not match the requested fixed range')
                    with part.open('ab')as stream:
                        while offset<length:
                            if time.monotonic()-started>=seconds:raise TimeoutError('Bounded CPU acquisition deadline; retain partial file')
                            chunk=response.read(min(4*1024**2,length-offset))
                            if not chunk:raise ValueError('Fixed data transfer truncated')
                            stream.write(chunk);stream.flush();offset+=len(chunk)
            if part.stat().st_size!=length or sha(part)!=digest:raise ValueError('Complete SHA/byte mismatch; retain failure')
            part.rename(path)
            records.append(dict(path=name,status='COMPLETE',bytes=length,sha256=digest,url=url,caller_s=time.monotonic()-began))
        except Exception as error:
            records.append(dict(path=name,status='STOPPED_PARTIAL',error=str(error),
                                retained_partial_bytes=part.stat().st_size if part.exists()else 0,caller_s=time.monotonic()-began))
            break
    report=dict(scope='CPU data preparation only; no roots or GPU output selected',revision=REVISION,
                complete=len(records)==len(FILES)and all(x['status']in('COMPLETE','EXISTING_BYTES_VERIFIED')for x in records),
                model_requests=0,caller_s=time.monotonic()-started,files=records)
    receipt=output/('ACQUISITION-'+str(time.time_ns())+'.json')
    receipt.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--seconds',type=int,default=420)
    a=p.parse_args();run(a.out,a.seconds)
