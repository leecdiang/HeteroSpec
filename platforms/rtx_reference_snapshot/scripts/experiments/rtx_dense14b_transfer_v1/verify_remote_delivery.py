"""Download the independent release copy and verify every archive/member hash."""
import datetime, hashlib, json, os, subprocess, sys, time, zipfile
from pathlib import Path
from common import read, save, file_hash

def verify(local,out,tag):
    local=Path(local);out=Path(out);assert not out.exists();out.mkdir(parents=True)
    env=dict(os.environ);env['GODEBUG']='http2client=0';start=time.monotonic()
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
    commands=[]
    def download(names):
        argv=['gh','release','download',tag,'--repo','leecdiang/HeteroSpec','--dir',str(out)]
        for name in names:argv+=['--pattern',name]
        began=time.monotonic()
        with (out.parent/'REMOTE_DOWNLOAD.log').open('ab') as log:
            p=subprocess.Popen(argv,stdout=log,stderr=subprocess.STDOUT,env=env);code=p.wait()
        commands.append({'argv':argv,'pid':p.pid,'exit_code':code,'seconds':time.monotonic()-began})
        save(out.parent/'REMOTE_DOWNLOAD_RECEIPT.json',{'commands':commands,'seconds':time.monotonic()-start,'utc_start':utc,'utc_latest':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_requests_added':0})
        assert code==0,'remote download failed; retain partial files and receipt'
    download(['RAW_ACCESS.json','COUNTEREXAMPLE_DECISIONS.zip'])
    assert file_hash(out/'RAW_ACCESS.json')==file_hash(local/'RAW_ACCESS.json'),'remote index changed'
    manifest=read(out/'RAW_ACCESS.json');verified=[];files=0
    for part in manifest['parts']:
        while True:
            assets=json.loads(subprocess.check_output(['gh','release','view',tag,'--repo','leecdiang/HeteroSpec','--json','assets'],env=env))['assets']
            if any(a['name']==part['name'] and a['state']=='uploaded' for a in assets):break
            receipt=out.parent/'UPLOAD_HTTP1_RECEIPT.json'
            if receipt.exists():assert read(receipt)['exit_code']==0,'upload failed; retain downloaded prefix'
            time.sleep(10)
        download([part['name']])
        path=out/part['name'];assert path.stat().st_size==part['bytes'] and file_hash(path)==part['sha256'],part['name']
        entries={x['path']:x for x in manifest['files'] if x['part']==part['name']}
        with zipfile.ZipFile(path) as z:
            assert len(z.namelist())==len(entries) and set(z.namelist())==set(entries),'archive inventory differs'
            for name,pin in entries.items():
                digest=hashlib.sha256();size=0
                with z.open(name) as f:
                    while chunk:=f.read(1024*1024):digest.update(chunk);size+=len(chunk)
                assert size==pin['bytes'] and digest.hexdigest()==pin['sha256'],name
                files+=1
        verified.append(part);print('Remote verified',part['name'],len(entries),'members',flush=True)
    witness=out/'COUNTEREXAMPLE_DECISIONS.zip';local_witness=local.parent/witness.name
    assert file_hash(witness)==file_hash(local_witness),'review pack hash'
    with zipfile.ZipFile(witness) as z:assert z.testzip() is None
    result={'status':'REMOTE_DOWNLOAD_AND_ALL_MEMBERS_READBACK_PASS','tag':tag,'release_url':'https://github.com/leecdiang/HeteroSpec/releases/tag/'+tag,
      'raw_index_sha256':file_hash(out/'RAW_ACCESS.json'),'parts':verified,'file_count':files,'part_count':len(verified),
      'witness':{'name':witness.name,'bytes':witness.stat().st_size,'sha256':file_hash(witness)},
      'native_requests_added':0,'verification_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'method':'Authenticated GitHub download into a fresh directory; every remote ZIP byte hash and every decompressed member checked against the immutable original index. Same physical host, no local-file substitution; not a third-party scientific replication.',
      'script_sha256':file_hash(__file__)}
    save(out.parent/'REMOTE_READBACK.json',result);return result

if __name__=='__main__':
    x=verify(sys.argv[1],sys.argv[2],sys.argv[3]);print(x['status'],x['file_count'])
