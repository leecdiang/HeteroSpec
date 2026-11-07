"""Download every small delivery asset anew, verify hashes and all metadata members."""
import argparse,datetime,hashlib,json,os,pathlib,subprocess,time,zipfile
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(local,out,tag):
    local,out=pathlib.Path(local),pathlib.Path(out);assert not out.exists();out.mkdir(parents=True)
    index=read(local/'DELIVERY_ASSETS.json');pins=index['assets']+[{'name':'DELIVERY_ASSETS.json','bytes':(local/'DELIVERY_ASSETS.json').stat().st_size,'sha256':sha(local/'DELIVERY_ASSETS.json')}]
    env=dict(os.environ,GODEBUG='http2client=0');commands=[];begin=time.monotonic()
    for pin in pins:
        args=['gh','release','download',tag,'--repo','leecdiang/HeteroSpec','--dir',str(out),'--pattern',pin['name']]
        t=time.monotonic()
        with (out/(pin['name']+'.log')).open('xb') as f:
            p=subprocess.run(args,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=600)
        event={'argv':args,'exit_code':p.returncode,'seconds':time.monotonic()-t};commands.append(event)
        with (out/'COMMANDS.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(event)+'\n')
        assert p.returncode==0,'Metadata download failed; receipt and partial retained'
        artifact=out/pin['name'];assert artifact.stat().st_size==pin['bytes'] and sha(artifact)==pin['sha256'],'Metadata asset identity mismatch'
    entries=read(out/'METADATA_MEMBERS.json')
    with zipfile.ZipFile(out/'TRANSPORT_METADATA.zip') as z:
        assert len(z.namelist())==len(entries) and set(z.namelist())=={x['path'] for x in entries}
        for e in entries:
            data=z.read(e['path']);assert len(data)==e['bytes'] and hashlib.sha256(data).hexdigest()==e['sha256'],'Metadata member mismatch'
    result={'status':'DELIVERY_METADATA_FRESH_REMOTE_READBACK_PASS','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'tag':tag,
        'assets':pins,'metadata_members':len(entries),'seconds':time.monotonic()-begin,'native_requests_added':0,
        'method':'Fresh authenticated remote downloads, exact asset size/SHA256 and every transport ZIP member size/SHA256. No local copy substituted.'}
    with (out/'DELIVERY_METADATA_READBACK.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2);f.write('\n')
    print('DELIVERY_METADATA_REMOTE_PASS',len(pins),len(entries))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('local');p.add_argument('out');p.add_argument('tag');a=p.parse_args();main(a.local,a.out,a.tag)
