"""Binary-safe readback from the same authorized API; credentials stay in memory."""
import argparse, shutil, time, urllib.request
from common import *
def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--dest',type=pathlib.Path,required=True);a=p.parse_args()
    token=subprocess.check_output(['gh','auth','token'],stderr=subprocess.PIPE,text=True).strip()
    assert token
    index=load(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json');files=index['parts'].copy()
    for name in ['ARCHIVE.json','MANIFEST.json']:
        rel='artifacts/rtx_target_only_bridge_v1/'+name;q=ROOT/rel;files.append({'path':rel,'sha256':sha(q),'bytes':q.stat().st_size})
    failures=load(DOC/'READBACK_BINARY_FAILURES.json') if (DOC/'READBACK_BINARY_FAILURES.json').exists() else [];rows=[]
    for b in files:
        target=a.dest/b['path'];target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.stat().st_size==b['bytes'] and sha(target)==b['sha256']:
            rows.append({**b,'reused_valid_remote_download':True});continue
        for attempt in [1,2,3]:
            tmp=target.with_name(target.name+f'.binary-attempt-{attempt}');url=f"https://api.github.com/repos/leecdiang/HeteroSpec/contents/{b['path']}?ref={a.commit}"
            request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github.raw','Accept-Encoding':'identity','User-Agent':'HeteroSpec-authorized-artifact-readback'})
            try:
                with urllib.request.urlopen(request,timeout=120) as response,tmp.open('wb') as f:
                    header={'status':response.status,'content_type':response.headers.get('Content-Type'),'content_length':response.headers.get('Content-Length'),'etag':response.headers.get('ETag')}
                    shutil.copyfileobj(response,f,8*1024*1024)
                assert tmp.stat().st_size==b['bytes'] and sha(tmp)==b['sha256'],'remote bytes do not match supplied part'
                tmp.replace(target);rows.append({**b,'attempt':attempt,'http':header});print(json.dumps({'downloaded':len(rows),'planned':len(files),'path':b['path'],'bytes':b['bytes']}),flush=True);break
            except Exception as exc:
                failures.append({'path':b['path'],'attempt':attempt,'error':repr(exc),'received_bytes':tmp.stat().st_size if tmp.exists() else 0,'received_sha256':sha(tmp) if tmp.exists() else None,'utc':now()});save(DOC/'READBACK_BINARY_FAILURES.json',failures)
                if attempt==3:raise
                time.sleep(5)
    save(DOC/'REMOTE_READBACK.json',{'status':'PASS','commit':a.commit,'files':rows,'binary_failures':failures,'prior_cli_failures':load(DOC/'READBACK_FAILURES.json'),'utc':now(),'scope':'all remote new parts/index/manifest downloaded from the same authorized Contents API with raw bytes, checked by length/hash; credentials never written','recovery':'gh api raw+json output produced transform: short source buffer and only2bytes; binary-safe API reader replaces transport, no scientific execution changes'})
    print(json.dumps({'status':'PASS','files':len(rows),'commit':a.commit}),flush=True)
if __name__=='__main__':main()
