"""Resume verified draft assets and upload at most five ready immutable shards.

No native work. Readiness uses the supplied packer's next-shard post-readback
barrier; all pins must agree with the final index. Existing assets are adopted
only when GitHub's uploaded state, size and SHA256 digest match local bytes and
the preceding uploader's durable success receipts. Never clobber or silently retry.
"""
import argparse,concurrent.futures,datetime,hashlib,json,os,pathlib,re,subprocess,time

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()

def main(local,out,previous,tag,release_id):
    local,out,previous=map(pathlib.Path,(local,out,previous));assert not out.exists(),'fresh upload directory'
    out.mkdir(parents=True);(out/'commands').mkdir();env=dict(os.environ,GODEBUG='http2client=0')
    start=time.monotonic();deadline=start+21600;repo='leecdiang/HeteroSpec'
    def save(name,obj):
        with (out/name).open('x',encoding='utf-8') as f:json.dump(obj,f,indent=2);f.write('\n')
    def journal(name,obj):
        with (out/name).open('a',encoding='utf-8') as f:f.write(json.dumps(obj)+'\n');f.flush();os.fsync(f.fileno())
    query=subprocess.run(['gh','api',f'repos/{repo}/releases/{release_id}'],capture_output=True,text=True,encoding='utf-8',env=env,timeout=120)
    (out/'INITIAL_REMOTE.log').write_text(query.stderr,encoding='utf-8');assert query.returncode==0,'Remote metadata failed'
    remote=json.loads(query.stdout);save('INITIAL_REMOTE.json',remote)
    assert remote['draft'] and remote['tag_name']==tag,'Only the intended unpublished draft may be resumed'
    prior=[json.loads(x) for x in (previous/'UPLOADED_PARTS.jsonl').read_text().splitlines() if x]
    assert all(re.fullmatch(r'evidence-\d{3}\.zip',x['name']) for x in prior),'Unexpected prior asset'
    assert len({x['name'] for x in prior})==len(prior),'Duplicate prior success'
    assets={x['name']:x for x in remote['assets']};assert set(assets)=={x['name'] for x in prior},'Unaccounted remote assets'
    completed={}
    for pin in prior:
        p=local/pin['name'];asset=assets[p.name]
        assert p.stat().st_size==pin['bytes']==asset['size'] and sha(p)==pin['sha256']
        assert asset['state']=='uploaded' and asset['digest']=='sha256:'+pin['sha256'],'Remote adoption identity mismatch'
        completed[p.name]=pin;journal('UPLOADED_PARTS.jsonl',pin)
    save('ADOPTED.json',{'previous_directory':str(previous),'parts':prior,'verification':'Local bytes and prior successful receipts match GitHub uploaded size/SHA256 digest. Fresh remote all-member readback remains required.'})
    def transfer(p):
        pin={'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)}
        args=['gh','release','upload',tag,'--repo',repo,str(p)]
        begin=time.monotonic();remaining=deadline-begin
        if remaining<=0:return dict(pin,exit_code=-2,error='six-hour deadline before transfer',seconds=0)
        with (out/'commands'/(p.name+'.log')).open('xb') as f:
            process=subprocess.Popen(args,env=env,stdout=f,stderr=subprocess.STDOUT)
            try:code=process.wait(timeout=min(7200,remaining))
            except subprocess.TimeoutExpired:process.kill();process.wait();code=-1
        return dict(pin,argv=args,pid=process.pid,exit_code=code,seconds=time.monotonic()-begin,utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    errors=[];active={};report=None
    def settle(event):
        journal('COMMANDS.jsonl',event)
        if event['exit_code']!=0:errors.append(event);return
        pin={k:event[k] for k in ('name','bytes','sha256')};completed[pin['name']]=pin;journal('UPLOADED_PARTS.jsonl',pin)
        print('UPLOADED',pin['name'],len(completed),flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        while True:
            manifest=local/'RAW_ACCESS.json'
            if report is None and manifest.exists():
                try:report=json.loads(manifest.read_text(encoding='utf-8'))
                except json.JSONDecodeError:report=None
                if report is not None:assert report['status']=='LOCAL_ARCHIVE_READBACK_PASS'
            if time.monotonic()>=deadline and not errors:errors.append({'error':'finite six-hour transport deadline reached'})
            busy=set(active.values())
            candidates=([local/x['name'] for x in report['parts']] if report else
                [p for p in sorted(local.glob('evidence-*.zip')) if re.fullmatch(r'evidence-\d{3}\.zip',p.name) and (local/f'evidence-{int(p.stem.split("-")[-1])+1:03d}.zip').exists()])
            if not errors:
                for p in candidates:
                    if len(active)==5:break
                    if p.name in completed or p.name in busy:continue
                    active[pool.submit(transfer,p)]=p.name;busy.add(p.name)
            if active:
                done,_=concurrent.futures.wait(active,timeout=5,return_when=concurrent.futures.FIRST_COMPLETED)
                for future in done:
                    name=active.pop(future)
                    try:settle(future.result())
                    except Exception as exc:
                        event={'name':name,'exit_code':-3,'error':repr(exc)};journal('COMMANDS.jsonl',event);errors.append(event)
            elif errors:
                save('FAILURE.json',{'errors':errors,'completed_parts':list(completed.values()),'native_requests_added':0})
                raise RuntimeError('Upload failed; all active transfers settled, remote assets and receipts retained. No automatic retry.')
            elif report and len(completed)==len(report['parts']):
                assert [completed[x['name']] for x in report['parts']]==report['parts'],'Final archive index disagrees with transferred pins'
                event=transfer(manifest);journal('COMMANDS.jsonl',event)
                assert event['exit_code']==0,'Index upload failed; receipt retained'
                save('UPLOAD.json',{'status':'UPLOAD_COMPLETE_NOT_YET_VERIFIED','tag':tag,'release_id':release_id,'parts':report['parts'],
                    'raw_index_sha256':event['sha256'],'seconds':time.monotonic()-start,'native_requests_added':0,'script_sha256':sha(pathlib.Path(__file__)),
                    'method':'At most five concurrent uploads to the intended unpublished draft. Prior assets adopted only after receipt/local/server SHA256 verification. Supplied packer next-shard barrier and final full-index equality. No clobber, silent retry or published release; fresh remote every-member verification still required.'})
                print('UPLOAD_COMPLETE',len(completed),flush=True);return
            else:time.sleep(5)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('local');p.add_argument('out');p.add_argument('previous');p.add_argument('tag');p.add_argument('release_id',type=int);a=p.parse_args();main(a.local,a.out,a.previous,a.tag,a.release_id)
