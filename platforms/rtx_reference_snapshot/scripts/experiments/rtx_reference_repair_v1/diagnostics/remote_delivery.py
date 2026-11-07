"""Upload immutable evidence, or fetch a fresh remote copy and verify every member."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess,time,zipfile
REPO='leecdiang/HeteroSpec'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
    return h.hexdigest()
def need(ok,msg):
    if not ok:raise ValueError(msg)
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,indent=2);f.write('\n')
def main(mode,local,out,tag):
    local=pathlib.Path(local);out=pathlib.Path(out);need(not out.exists(),'fresh delivery directory');out.mkdir(parents=True)
    env=dict(os.environ,GODEBUG='http2client=0');start=time.monotonic();commands=[];manifest=read(local/'RAW_ACCESS.json')
    def command(argv):
        t=time.monotonic()
        with (out/'COMMANDS.log').open('ab') as f:
            p=subprocess.Popen(argv,env=env,stdout=f,stderr=subprocess.STDOUT)
            try:code=p.wait(timeout=7200)
            except subprocess.TimeoutExpired:p.kill();p.wait();code=-1
        event={'argv':argv,'pid':p.pid,'exit_code':code,'seconds':time.monotonic()-t,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()};commands.append(event)
        with (out/'COMMANDS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
        need(code==0,'remote command failed; partials and receipts retained')
    if mode=='upload':
        files=[local/'RAW_ACCESS.json']+[local/p['name'] for p in manifest['parts']]
        for pin in manifest['parts']:
            p=local/pin['name'];need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'local archive drift')
        for i in range(0,len(files),5):
            command(['gh','release','upload',tag,'--repo',REPO]+[str(p) for p in files[i:i+5]])
            print('UPLOADED',min(i+5,len(files)),len(files),flush=True)
        save(out/'UPLOAD.json',{'status':'UPLOAD_COMPLETE_NOT_YET_VERIFIED','tag':tag,'commands':commands,'seconds':time.monotonic()-start,'raw_index_sha256':sha(local/'RAW_ACCESS.json')})
        return
    command(['gh','release','download',tag,'--repo',REPO,'--dir',str(out),'--pattern','RAW_ACCESS.json'])
    need(sha(out/'RAW_ACCESS.json')==sha(local/'RAW_ACCESS.json'),'remote index mismatch');remote=read(out/'RAW_ACCESS.json');verified=[];members=0
    for pin in remote['parts']:
        command(['gh','release','download',tag,'--repo',REPO,'--dir',str(out),'--pattern',pin['name']])
        p=out/pin['name'];need(p.stat().st_size==pin['bytes'] and sha(p)==pin['sha256'],'remote part mismatch');entries={e['path']:e for e in remote['files'] if e['part']==pin['name']}
        with zipfile.ZipFile(p) as z:
            need(len(z.namelist())==len(entries) and set(z.namelist())==set(entries),'remote inventory mismatch')
            for name,e in entries.items():
                h=hashlib.sha256();size=0
                with z.open(name) as f:
                    for b in iter(lambda:f.read(1024*1024),b''):h.update(b);size+=len(b)
                need(size==e['bytes'] and h.hexdigest()==e['sha256'],'remote member mismatch: '+name);members+=1
        verified.append(pin)
        with (out/'VERIFIED_PARTS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(dict(pin,verified_members=len(entries)))+'\n');f.flush();os.fsync(f.fileno())
        # Bound disk usage to one fresh remote shard. Original raw/archives and
        # unsuccessful downloads are retained; only this verified duplicate is removed.
        need(p.resolve().parent==out.resolve() and p.name==pin['name'],'remote temporary path confinement')
        p.unlink();print('REMOTE_VERIFIED',pin['name'],members,flush=True)
    save(out/'REMOTE_READBACK.json',{'status':'REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS','tag':tag,'release_url':'https://github.com/'+REPO+'/releases/tag/'+tag,'raw_index_sha256':sha(out/'RAW_ACCESS.json'),'parts':verified,'file_count':members,'part_count':len(verified),'native_requests_added':0,'seconds':time.monotonic()-start,'verification_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(pathlib.Path(__file__)),'method':'Authenticated GitHub download into a new directory, archive and every decompressed member SHA-256 verified. Verified temporary remote shards removed after durable receipts to bound disk; originals, failed downloads and remote assets retained. No local evidence substituted. Same-host delivery verification, not third-party scientific replication.'})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['upload','verify']);p.add_argument('local');p.add_argument('out');p.add_argument('tag');a=p.parse_args();main(a.mode,a.local,a.out,a.tag)
