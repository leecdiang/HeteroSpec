"""Publish only existing, independently recomputed CPU closure; no scientific run."""
import argparse,base64,concurrent.futures,hashlib,json,subprocess,sys,time,urllib.request,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parents[1]))
from common import V,load,save,sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=float,required=True);ap.add_argument('--ledger',type=Path,required=True);a=ap.parse_args();start=time.monotonic();limit=start+a.seconds
    f=load(V/'F0.json');assert load(OUT/'FRESH_RECOMPUTE_VERIFIED.json')['status']=='VERIFIED'
    assert load(OUT/'RAW_REMOTE_AUTHENTICATED.json')['authenticated_remote_bytes']
    token=subprocess.run([f['gh']['path'],'auth','token','--hostname','github.com'],capture_output=True,check=True,timeout=3).stdout.decode().strip();assert token
    parent=load(OUT/'RAW_REMOTE_AUTHENTICATED.json')['commit'];rel='benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2/delivery/block0_r2/'
    def request(path,method='GET',payload=None,raw=False):
        left=limit-time.monotonic();assert left>1,'CPU delivery budget reserve reached'
        data=None if payload is None else json.dumps(payload,separators=(',',':')).encode()
        req=urllib.request.Request('https://api.github.com/repos/leecdiang/HeteroSpec'+path,data=data,headers={'Authorization':'Bearer '+token,'User-Agent':'HeteroSpec-CPU-closure','Accept':'application/vnd.github.raw+json' if raw else 'application/vnd.github+json','Accept-Encoding':'identity'},method=method)
        with urllib.request.urlopen(req,timeout=min(5,left)) as response:body=response.read()
        return body if raw else json.loads(body)
    assert request('/git/ref/heads/'+f['branch'])['object']['sha']==parent,'remote changed;no force'
    import build_result
    build_result.build()
    rows={}
    with zipfile.ZipFile(OUT/'CPU_CLOSURE_RECEIPTS.zip','x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OUT/'cpu_ledger').rglob('*')):
            if p.is_file():
                name=p.relative_to(OUT).as_posix();row=dict(bytes=p.stat().st_size,sha256=sha(p),included=p.stat().st_size<=256*1024);rows[name]=row
                if row['included']:z.write(p,name)
    save(OUT/'CPU_CLOSURE_RECEIPTS_MANIFEST.json',dict(entries=rows,zip_sha256=sha(OUT/'CPU_CLOSURE_RECEIPTS.zip'),large_redundant_transport_encodings_retained_locally=True,scientific_archive_all_242_members_remote=True,current_terminal_receipt_separate=True))
    names=['publish_final_cpu.py','finish_cpu_closure.py','build_result.py','cpu_delivery.py','RAW_REMOTE_AUTHENTICATED.json','FRESH_ENUMERATION.json','FRESH_ANALYSIS.json','FRESH_FORENSIC.json','FRESH_RECOMPUTE_VERIFIED.json','RESULT.json','RESULT.md','COORDINATES.csv','CPU_CLOSURE_RECEIPTS.zip','CPU_CLOSURE_RECEIPTS_MANIFEST.json']
    files=[OUT/n for n in names]
    save(OUT/'CLOSURE_FILES_MANIFEST.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files});files.append(OUT/'CLOSURE_FILES_MANIFEST.json')
    base=request('/git/commits/'+parent)['tree']['sha']
    def upload(p):
        data=p.read_bytes();r=request('/git/blobs','POST',dict(content=base64.b64encode(data).decode(),encoding='base64'));assert r['sha']==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        return dict(path=rel+p.name,mode='100644',type='blob',sha=r['sha'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:entries=list(pool.map(upload,files))
    tree=request('/git/trees','POST',dict(base_tree=base,tree=entries))['sha']
    commit=request('/git/commits','POST',dict(message='PR118: independently restore stopped Block0 r2;withhold all timing estimates',tree=tree,parents=[parent]))['sha']
    assert request('/git/ref/heads/'+f['branch'])['object']['sha']==parent,'remote changed;no force'
    request('/git/refs/heads/'+f['branch'],'PATCH',dict(sha=commit,force=False))
    save(OUT/'RESULT_PUBLICATION.json',dict(commit=commit,parent=parent,tree=tree,force=False))
    def check(p):
        data=request('/contents/'+rel+p.name+'?ref='+commit,raw=True);assert data==p.read_bytes();return p.name
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:checked=list(pool.map(check,files))
    pr=request('/pulls/118');assert pr['draft'] and pr['head']['sha']==commit
    save(OUT/'RESULT_REMOTE_VERIFIED.json',dict(status='VERIFIED',commit=commit,PR118_Draft=True,exact_remote_closure_files=checked,archive_commit=parent,archive_sha256=load(OUT/'raw_api/ARCHIVE.json')['sha256'],F0_sha256=sha(V/'F0.json'),elapsed_CPU_helper_seconds=time.monotonic()-start,GPU_queries=0,graph_calls=0,local_git_ref_not_rewritten=True))
    print(json.dumps(dict(status='VERIFIED',commit=commit,archive_members=242,GPU_queries=0,graph_calls=0)))
if __name__=='__main__':main()
