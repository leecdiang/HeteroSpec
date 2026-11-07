"""Fresh remote download and every-member readback, bounded to five shards on disk."""
import argparse,concurrent.futures,datetime,hashlib,json,os,pathlib,re,shutil,subprocess,time,zipfile

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main(local,out,tag):
    local,out=pathlib.Path(local),pathlib.Path(out);assert not out.exists(),'fresh remote directory'
    out.mkdir(parents=True);downloads=out/'downloads';downloads.mkdir();(out/'commands').mkdir();(out/'part_receipts').mkdir()
    start=time.monotonic();deadline=start+min(21600,(datetime.datetime.fromisoformat(json.loads((out.parent/'TRANSPORT_RESOURCE_POLICY02.json').read_text())['overall_deadline_utc'])-datetime.datetime.now(datetime.timezone.utc)).total_seconds());env=dict(os.environ,GODEBUG='http2client=0')
    def save(p,x):
        with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    def journal(name,x):
        with (out/name).open('a',encoding='utf-8') as f:f.write(json.dumps(x)+'\n');f.flush();os.fsync(f.fileno())
    def attempt_download(name,directory,attempt):
        assert time.monotonic()<deadline,'finite readback deadline'
        args=['gh','release','download',tag,'--repo','leecdiang/HeteroSpec','--dir',str(directory),'--pattern',name]
        begin=time.monotonic()
        with (out/'commands'/(name+f'.attempt{attempt}.log')).open('xb') as f:
            process=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT)
            try:code=process.wait(timeout=min(7200,deadline-time.monotonic()))
            except subprocess.TimeoutExpired:process.kill();process.wait();code=-1
        event={'argv':args,'pid':process.pid,'exit_code':code,'seconds':time.monotonic()-begin,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        save(out/'commands'/(name+f'.attempt{attempt}.json'),event)
        return event
    def download(name,directory):
        for attempt in range(1,4):
            event=attempt_download(name,directory,attempt)
            if event['exit_code']==0:
                save(out/'commands'/(name+'.json'),event)
                return event
            log=(out/'commands'/(name+f'.attempt{attempt}.log')).read_text(encoding='utf-8',errors='replace')
            failed=directory/name
            if failed.exists():
                target=out/'failed_partials'/f'{name}.attempt{attempt}'
                target.parent.mkdir(exist_ok=True);assert not target.exists() and failed.resolve().parent==directory.resolve()
                failed.rename(target)
                with (local/name).open('rb') as src,target.open('rb') as cut:
                    for block in iter(lambda:cut.read(4194304),b''):assert src.read(len(block))==block
                save(out/'commands'/(name+f'.partial{attempt}.json'),{'prefix_bytes':target.stat().st_size,'prefix_sha256':sha(target),'original':name})
            assert attempt<3 and any(x in log.lower() for x in ('eof','timeout','connection reset','release not found')),log
            time.sleep(5*attempt)
    download('RAW_ACCESS.json',out);index=out/'RAW_ACCESS.json'
    assert sha(index)==sha(local/'RAW_ACCESS.json'),'Fresh remote index differs from immutable local index'
    report=json.loads(index.read_text(encoding='utf-8'));parts=report['parts']
    assert len({p['name'] for p in parts})==len(parts) and all(re.fullmatch(r'evidence-\d{3}\.zip',p['name']) for p in parts)
    assert shutil.disk_usage(out).free>=5*max(p['bytes'] for p in parts)+20*1024**3,'five-shard disk reserve'
    members={p['name']:{} for p in parts}
    for e in report['files']:
        assert e['path'] not in members[e['part']],'Duplicate member in index'
        members[e['part']][e['path']]=e
    def verify(pin):
        event=download(pin['name'],downloads);p=downloads/pin['name']
        assert p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'Remote archive identity mismatch'
        expected=members[pin['name']]
        with zipfile.ZipFile(p) as z:
            assert len(z.namelist())==len(expected) and set(z.namelist())==set(expected),'Remote member inventory mismatch'
            for name,e in expected.items():
                assert time.monotonic()<deadline,'finite readback deadline'
                h=hashlib.sha256();size=0
                with z.open(name) as f:
                    for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
                assert size==e['bytes'] and h.hexdigest()==e['sha256'],'Remote member mismatch: '+name
        result=dict(pin,verified_members=len(expected),download_seconds=event['seconds'],verified_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(out/'part_receipts'/(pin['name']+'.json'),result)
        # Delete only this independently downloaded, fully verified duplicate, after
        # its durable receipt. Original raw/local archives and failed partials remain.
        assert not p.is_symlink() and p.resolve().parent==downloads.resolve() and p.name==pin['name'],'temporary path confinement'
        p.unlink();return result
    prior={}
    previous=out.parent/'remote01'
    for folder in [previous,out.parent/'remote02']:
        assert sha(folder/'RAW_ACCESS.json')==sha(index)
        logged={x['name']:x for x in map(json.loads,(folder/'VERIFIED_PARTS.jsonl').read_text(encoding='utf-8').splitlines())}
        for pin in parts:
            if pin['name'] not in logged:continue
            item=json.loads((folder/'part_receipts'/(pin['name']+'.json')).read_text(encoding='utf-8'))
            assert pin['name'] not in prior and item==logged[pin['name']] and all(item[k]==v for k,v in pin.items()) and item['verified_members']==len(members[pin['name']])
            assert json.loads((folder/'commands'/(pin['name']+'.json')).read_text(encoding='utf-8'))['exit_code']==0
            prior[pin['name']]=item
    assert len(prior)==168
    save(out/'ADOPTED.json',{'prior_receipts':prior,'fresh_index_sha256':sha(index)})
    active={};verified=dict(prior);errors=[];todo=iter(p for p in parts if p['name'] not in prior);exhausted=False
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        while True:
            if time.monotonic()>=deadline and not errors:errors.append({'error':'finite six-hour readback deadline'})
            while not errors and not exhausted and len(active)<5:
                pin=next(todo,None)
                if pin is None:exhausted=True;break
                active[pool.submit(verify,pin)]=pin['name']
            if not active:break
            done,_=concurrent.futures.wait(active,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                name=active.pop(future)
                try:
                    result=future.result();verified[name]=result;journal('VERIFIED_PARTS.jsonl',result)
                    print('REMOTE_VERIFIED',name,len(verified),len(parts),flush=True)
                except Exception as exc:
                    event={'name':name,'error':repr(exc)};errors.append(event);journal('FAILURES.jsonl',event)
    if errors:
        save(out/'FAILURE.json',{'errors':errors,'verified_shards':len(verified),'native_requests_added':0})
        raise RuntimeError('Remote verification failed; all active transfers settled, partials and receipts retained. No automatic retry.')
    assert set(verified)=={p['name'] for p in parts},'Incomplete remote readback'
    count=sum(x['verified_members'] for x in verified.values());assert count==len(report['files'])
    save(out/'REMOTE_READBACK.json',{'status':'REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS','tag':tag,
        'release_url':'https://github.com/leecdiang/HeteroSpec/releases/tag/'+tag,'raw_index_sha256':sha(index),
        'parts':parts,'file_count':count,'part_count':len(parts),'native_requests_added':0,'seconds':time.monotonic()-start,
        'verification_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(pathlib.Path(__file__)),
        'method':'Authenticated fresh GitHub downloads, at most five simultaneous shards. Archive size/SHA256, exact member inventory, every decompressed member size/SHA256 checked against fresh remote index identical to immutable local index. Per-part receipts fsynced before deleting only verified temporary duplicates. Original raw/local archives, unsuccessful downloads and remote assets retained. Same-host transport verification, not third-party scientific replication.'})
    shutil.copyfile(out/'REMOTE_READBACK.json',previous/'REMOTE_READBACK.json') if not (previous/'REMOTE_READBACK.json').exists() else (_ for _ in ()).throw(RuntimeError('existing aggregate'))
    print('REMOTE_READBACK_COMPLETE',len(parts),count,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('local');p.add_argument('out');p.add_argument('tag');a=p.parse_args();main(a.local,a.out,a.tag)
