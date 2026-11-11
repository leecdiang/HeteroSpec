"""Authenticated bounded artifact readback using existing GitHub CLI credentials."""
import argparse, subprocess, time
from common import *
def main():
    p=argparse.ArgumentParser();p.add_argument('--commit',required=True);p.add_argument('--dest',type=pathlib.Path,required=True);a=p.parse_args()
    index=load(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json');rows=[];failures=[]
    a.dest.mkdir(parents=True,exist_ok=True)
    files=index['parts']+[{'path':'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json','sha256':sha(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json'),'bytes':(ROOT/'artifacts/rtx_target_only_bridge_v1/ARCHIVE.json').stat().st_size}, {'path':'artifacts/rtx_target_only_bridge_v1/MANIFEST.json','sha256':sha(ROOT/'artifacts/rtx_target_only_bridge_v1/MANIFEST.json'),'bytes':(ROOT/'artifacts/rtx_target_only_bridge_v1/MANIFEST.json').stat().st_size}]
    for b in files:
        target=a.dest/b['path'];target.parent.mkdir(parents=True,exist_ok=True)
        for attempt in [1,2,3]:
            tmp=target.with_name(target.name+f'.attempt-{attempt}');err=tmp.with_name(tmp.name+'.stderr.log')
            cmd=['gh','api','-H','Accept: application/vnd.github.raw+json',f"repos/leecdiang/HeteroSpec/contents/{b['path']}?ref={a.commit}"]
            with tmp.open('wb') as out,err.open('wb') as stderr:result=subprocess.run(cmd,stdout=out,stderr=stderr,timeout=240)
            if result.returncode==0 and tmp.stat().st_size==b['bytes'] and sha(tmp)==b['sha256']:
                tmp.replace(target);rows.append({**b,'attempt':attempt});break
            failures.append({'path':b['path'],'attempt':attempt,'exit_code':result.returncode,'received_bytes':tmp.stat().st_size,'expected_sha256':b['sha256'],'received_sha256':sha(tmp),'stdout':str(tmp),'stderr':str(err)})
            save(DOC/'READBACK_FAILURES.json',failures)
            if attempt==3:raise RuntimeError('readback failed '+b['path'])
            time.sleep(5)
    save(DOC/'REMOTE_READBACK.json',{'status':'PASS','commit':a.commit,'files':rows,'failures':failures,'utc':now(),'scope':'all new raw evidence parts/index/manifest downloaded by authenticated Contents API at exact commit; hashes/lengths checked; clean restore is separate'})
    print(json.dumps({'status':'PASS','commit':a.commit,'files':len(rows),'failures':len(failures)}),flush=True)
if __name__=='__main__':main()
