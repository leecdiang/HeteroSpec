"""One bounded CPU-only remote restoration/closure. No experimental re-entry.

Parallel HTTPS byte transfers share this CPU process; no extra GPU/process probes.
Every transfer has a finite timeout, no retry, and the outer frozen Job watchdog
enforces the remaining cumulative delivery budget (including prior failures).
"""
import argparse,base64,concurrent.futures,hashlib,json,os,subprocess,sys,time,urllib.request,zipfile
from pathlib import Path
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT.parents[1]))
from common import V,load,save,sha

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=float,required=True);ap.add_argument('--ledger',type=Path,required=True);a=ap.parse_args()
    f=load(V/'F0.json');start=time.monotonic();limit=start+a.seconds
    assert sha(V/'F0.json')=='f2d6965646e1f53c5d8a8b974f0277efc2903ed022689374af3f178fbad8e587'
    assert load(Path(f['execution_root'])/'CLEAN0_ENDED.json')['status']=='INCOMPLETE_STOPPED'
    token=subprocess.run([f['gh']['path'],'auth','token','--hostname','github.com'],capture_output=True,check=True,timeout=3).stdout.decode().strip()
    assert token
    endpoint='https://api.github.com/repos/leecdiang/HeteroSpec'
    parent='bf370f4dfc7c463abc657d71c22f3aeade4cbe62'
    rel='benchmarks/rtx_lowering_envelope_v1/s1b_monitor_repair_v2/delivery/block0_r2/'
    def request(path,method='GET',payload=None,raw=False):
        remaining=limit-time.monotonic();assert remaining>1,'CPU closure remaining budget exhausted'
        headers={'Authorization':'Bearer '+token,'User-Agent':'HeteroSpec-CPU-closure','Accept':'application/vnd.github.raw+json' if raw else 'application/vnd.github+json','Accept-Encoding':'identity'}
        data=None if payload is None else json.dumps(payload,separators=(',',':')).encode()
        req=urllib.request.Request(endpoint+path,data=data,headers=headers,method=method)
        with urllib.request.urlopen(req,timeout=min(6,remaining)) as response:body=response.read()
        return body if raw else json.loads(body)
    assert request('/git/ref/heads/'+f['branch'])['object']['sha']==parent,'remote changed;no force'
    download=OUT/'download';download.mkdir(exist_ok=False)
    archive_dir=OUT/'raw_api';desc=load(archive_dir/'ARCHIVE.json')
    sources=[archive_dir/'ARCHIVE.json']+[archive_dir/r['name'] for r in desc['parts']]+[OUT/n for n in ['RESULT_RAW_MANIFEST.json','FORENSIC.json','ANALYSIS.json']]
    def download_one(source):
        name=source.relative_to(OUT).as_posix();data=request('/contents/'+rel+name+'?ref='+parent,raw=True)
        assert data==source.read_bytes(),'remote exact-byte mismatch: '+name
        target=download/source.name
        with target.open('xb') as file:file.write(data)
        return dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:verified=list(pool.map(download_one,sources))
    save(OUT/'RAW_REMOTE_AUTHENTICATED.json',dict(authenticated_remote_bytes=True,commit=parent,run_id=f['run_id'],execution_id=f['execution_id'],F0_sha256=sha(V/'F0.json'),archive_sha256=desc['sha256'],all_remote_files=verified,manifest_sha256=sha(OUT/'RESULT_RAW_MANIFEST.json'),no_normalization=True))
    import archive
    fresh=Path(f['fresh_restore_root']);result=archive.restore(download,desc,fresh,f['budget']['limits']['raw_bytes']+32*1024**2)
    manifest=load(OUT/'RESULT_RAW_MANIFEST.json')['members']
    actual={p.relative_to(fresh).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in fresh.rglob('*') if p.is_file() and p.name!='MANIFEST.json'}
    assert actual==manifest
    save(OUT/'FRESH_ENUMERATION.json',dict(status='PASS',fresh_root=str(fresh),members=len(actual),bytes=sum(r['bytes'] for r in actual.values()),all_members_exact=True,archive_result=result))
    def python(args,label):
        remaining=limit-time.monotonic();assert remaining>1
        cmd=[f['python']['path'],'-B',*map(str,args)];save(a.ledger/(label+'.COMMAND.json'),dict(command=cmd,CPU_only=True))
        process=subprocess.run(cmd,capture_output=True,timeout=remaining)
        (a.ledger/(label+'.stdout')).write_bytes(process.stdout);(a.ledger/(label+'.stderr')).write_bytes(process.stderr)
        assert process.returncode==0,label+' failed'
    python([fresh/'frozen/evidence_s1b.py','--action','analyze','--frozen',fresh/'frozen','--root',fresh/'raw','--out',OUT/'FRESH_ANALYSIS.json'],'frozen-analysis')
    python([fresh/'raw/CPU_SEAL_CONTEXT/forensic_block0.py','--root',fresh/'raw','--frozen',fresh/'frozen','--out',OUT/'FRESH_FORENSIC.json'],'forensic-replay')
    assert (OUT/'FRESH_ANALYSIS.json').read_bytes()==(OUT/'ANALYSIS.json').read_bytes()
    assert (OUT/'FRESH_FORENSIC.json').read_bytes()==(OUT/'FORENSIC.json').read_bytes()
    save(OUT/'FRESH_RECOMPUTE_VERIFIED.json',dict(status='VERIFIED',fresh_interpreter=True,all_frozen_analysis_bytes_equal=True,all_forensic_description_bytes_equal=True,archive_SHA256=desc['sha256'],remote_commit=parent,GPU_queries=0,graph_calls=0))
    import build_result
    build_result.build()
    # Preserve CPU errors and transport receipts independently of immutable raw.
    # Redundant large HTTP/Git encodings remain local and are inventoried by hash;
    # they are not scientific archive members and never replace raw evidence.
    entries={};record_zip=OUT/'CPU_CLOSURE_RECEIPTS.zip'
    with zipfile.ZipFile(record_zip,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OUT/'cpu_ledger').rglob('*')):
            if p.is_file():
                name=p.relative_to(OUT).as_posix();row=dict(bytes=p.stat().st_size,sha256=sha(p),included=p.stat().st_size<=256*1024);entries[name]=row
                if row['included']:z.write(p,name)
    save(OUT/'CPU_CLOSURE_RECEIPTS_MANIFEST.json',dict(entries=entries,zip_sha256=sha(record_zip),large_redundant_transport_encodings_retained_locally=True,scientific_archive_all_242_members_remote=True))
    names=['finish_cpu_closure.py','build_result.py','cpu_delivery.py','RAW_REMOTE_AUTHENTICATED.json','FRESH_ENUMERATION.json','FRESH_ANALYSIS.json','FRESH_FORENSIC.json','FRESH_RECOMPUTE_VERIFIED.json','RESULT.json','RESULT.md','COORDINATES.csv','CPU_CLOSURE_RECEIPTS.zip','CPU_CLOSURE_RECEIPTS_MANIFEST.json']
    files=[OUT/n for n in names]
    save(OUT/'CLOSURE_FILES_MANIFEST.json',{p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files})
    files.append(OUT/'CLOSURE_FILES_MANIFEST.json')
    base=request('/git/commits/'+parent)['tree']['sha']
    def upload(p):
        data=p.read_bytes();obj=request('/git/blobs','POST',dict(content=base64.b64encode(data).decode(),encoding='base64'))
        assert obj['sha']==hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        return dict(path=rel+p.name,mode='100644',type='blob',sha=obj['sha'])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:tree_entries=list(pool.map(upload,files))
    tree=request('/git/trees','POST',dict(base_tree=base,tree=tree_entries))['sha']
    commit=request('/git/commits','POST',dict(message='PR118: independently restore stopped Block0 r2;withhold all timing estimates',tree=tree,parents=[parent]))['sha']
    assert request('/git/ref/heads/'+f['branch'])['object']['sha']==parent,'remote changed;no force'
    request('/git/refs/heads/'+f['branch'],'PATCH',dict(sha=commit,force=False))
    # Read the actual published bytes, rather than accepting a successful POST.
    def check(p):
        remote=request('/contents/'+rel+p.name+'?ref='+commit,raw=True);assert remote==p.read_bytes();return p.name
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:checked=list(pool.map(check,files))
    pr=request('/pulls/118');assert pr['draft'] and pr['head']['sha']==commit
    save(OUT/'RESULT_REMOTE_VERIFIED.json',dict(status='VERIFIED',commit=commit,PR118_Draft=True,exact_remote_closure_files=checked,archive_commit=parent,archive_sha256=desc['sha256'],F0_sha256=sha(V/'F0.json'),elapsed_CPU_helper_seconds=time.monotonic()-start,GPU_queries=0,graph_calls=0,local_git_ref_not_rewritten=True))
    print(json.dumps(dict(status='VERIFIED',commit=commit,archive_members=len(actual),GPU_queries=0,graph_calls=0)))

if __name__=='__main__':main()
