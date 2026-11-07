"""Upload immutable locally verified shards to a private draft while pack continues.

The supplied pack() creates shard N+1 only after closing, reopening, checking every
member and hashing shard N. Therefore existence of the next shard is the readiness
barrier; the final RAW_ACCESS index is the barrier for the final shard. The complete
index must subsequently match every upload receipt. Remote all-member verification
is a separate mandatory step, using remote_delivery.py verify.
"""
import datetime,hashlib,json,os,pathlib,subprocess,time

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main(local,out,tag):
    local,out=pathlib.Path(local),pathlib.Path(out)
    assert not out.exists(),'fresh transport directory'
    out.mkdir(parents=True);env=dict(os.environ,GODEBUG='http2client=0')
    start=time.monotonic();uploaded=[];index=0
    def upload(p):
        pin={'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}
        args=['gh','release','upload',tag,'--repo','leecdiang/HeteroSpec',str(p)]
        begin=time.monotonic()
        with (out/'COMMANDS.log').open('ab') as f:
            process=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT)
            try:code=process.wait(timeout=7200)
            except subprocess.TimeoutExpired:process.kill();process.wait();code=-1
        event=dict(pin,argv=args,pid=process.pid,exit_code=code,seconds=time.monotonic()-begin,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        with (out/'COMMANDS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
        assert code==0,'Upload failed; remote assets and all receipts retained. No clobber or silent retry.'
        with (out/'UPLOADED_PARTS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(pin)+'\n');f.flush();os.fsync(f.fileno())
        print('UPLOADED',p.name,pin['bytes'],flush=True)
        return pin
    while True:
        assert time.monotonic()-start<21600,'finite six-hour transport ceiling reached'
        manifest=local/'RAW_ACCESS.json'
        if manifest.exists():
            # pack writes the JSON once at the end. Wait for a valid complete file;
            # its final part list and hashes, not just file existence, are decisive.
            try:report=json.loads(manifest.read_text(encoding='utf-8'))
            except json.JSONDecodeError:time.sleep(1);continue
            assert report['status']=='LOCAL_ARCHIVE_READBACK_PASS'
            for pin in report['parts']:
                if pin['name'] in {x['name'] for x in uploaded}:continue
                p=local/pin['name'];assert p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256']
                uploaded.append(upload(p))
            assert uploaded==report['parts'],'Final local index does not match uploaded immutable shards'
            index_pin=upload(manifest)
            receipt={'status':'UPLOAD_COMPLETE_NOT_YET_VERIFIED','tag':tag,'seconds':time.monotonic()-start,
                'raw_index_sha256':index_pin['sha256'],'parts':uploaded,'native_requests_added':0,
                'script_sha256':sha(pathlib.Path(__file__)),
                'method':'Private draft upload overlapped archive creation. Next-shard creation is the supplied pack() post-readback barrier; final index size/SHA pins match every upload receipt. No overwrite, clobber, retry or public release. Fresh remote download and every-member readback still required.'}
            with (out/'UPLOAD.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2);f.write('\n')
            return
        p=local/f'evidence-{index:03d}.zip';next_part=local/f'evidence-{index+1:03d}.zip'
        if p.exists() and next_part.exists():uploaded.append(upload(p));index+=1
        else:time.sleep(5)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('local');parser.add_argument('out');parser.add_argument('tag');args=parser.parse_args();main(args.local,args.out,args.tag)
