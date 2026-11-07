"""CPU-only retrieval and exact offline replay of the sealed RTX V4 capsules.

The original source, arrays, protocol, manifests and failure states are read-only.
No model, runtime or device is required or downloaded. Transport receipts and
derived review files are written under a separate output directory.
"""
import argparse, base64, collections, gzip, hashlib, itertools, json, math, os
import pathlib, random, shutil, subprocess, sys, tarfile, time, urllib.request

REPO='leecdiang/HeteroSpec'
HEAD='8f30449d51bca1fe4907c392c5c65d5cc0fbcd3f'
STUDY='benchmarks/rtx_trajectory_cost_v4/'
ARCHIVES=[
 'A_ENGINEERING_ARCHIVE.json','A_ENGINEERING_ANONYMOUS_ARCHIVE.json',
 'B_ENGINEERING_ARCHIVE.json','B_ENGINEERING_ANONYMOUS_ARCHIVE.json',
 'A_PRE_LIVE_ARCHIVE.json','A_COMPLETE_ARCHIVE.json',
 'A_COMPLETE_ANONYMOUS_ARCHIVE.json','B_COMPLETE_ARCHIVE.json',
 'B_COMPLETE_ANONYMOUS_ARCHIVE.json']

def sha(p):
    with pathlib.Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def blob_id(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
def save(p,v):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,ensure_ascii=True)+'\n',encoding='utf-8')
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
def require(ok,msg):
    if not ok:raise ValueError(msg)

class Retrieval:
    def __init__(self,out):
        self.out=out;self.receipts=[];self.token=os.environ['GH_TOKEN']
        tree=json.loads(self.get('/git/trees/'+HEAD+'?recursive=1'))
        require(not tree.get('truncated'),'remote tree incomplete')
        self.tree={v['path']:v for v in tree['tree'] if v['type']=='blob'}
    def get(self,suffix,raw=False):
        url='https://api.github.com/repos/'+REPO+suffix
        req=urllib.request.Request(url,headers={
          'Authorization':'Bearer '+self.token,
          'Accept':'application/vnd.github.raw+json' if raw else 'application/vnd.github+json',
          'X-GitHub-Api-Version':'2022-11-28','User-Agent':'RTX-V4-read-only-closeout'})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req,timeout=120) as r:
                    data=r.read();ctype=r.headers.get('Content-Type','')
                if raw and 'json' in ctype:
                    v=json.loads(data)
                    if isinstance(v,dict) and v.get('encoding')=='base64':data=base64.b64decode(v['content'])
                return data
            except Exception as e:
                self.receipts.append({'url_suffix':suffix,'attempt':attempt+1,'transport_error_type':type(e).__name__})
                if attempt==2:raise
                time.sleep(2*(attempt+1))
    def file(self,path,dest,expected=None):
        entry=self.tree[path];dest=pathlib.Path(dest);dest.parent.mkdir(parents=True,exist_ok=True)
        data=self.get('/git/blobs/'+entry['sha'],raw=True)
        require(len(data)==entry['size'] and blob_id(data)==entry['sha'],'Git blob mismatch '+path)
        dest.write_bytes(data)
        if expected:require(len(data)==expected['bytes'] and sha(dest)==expected['sha256'],'sealed part mismatch '+path)
        self.receipts.append({'path':path,'head':HEAD,'git_blob':entry['sha'],'bytes':len(data),'sha256':sha(dest)})
        save(self.out/'REMOTE_RETRIEVAL.json',{'head':HEAD,'files':self.receipts})
        return dest

def safe_extract(archive,dest):
    # Python's data filter rejects outside paths and unsafe link destinations.
    # Only files, directories, and ordinary internal hardlinks are expected.
    plain=archive.with_suffix('.transport.tar')
    with gzip.open(archive,'rb') as inp,plain.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
    with tarfile.open(plain,'r:') as tf:
        for m in tf.getmembers():
            require(m.isfile() or m.isdir() or m.islnk(),'unsupported tar member '+m.name)
            require(not pathlib.PurePosixPath(m.name).is_absolute() and '..' not in pathlib.PurePosixPath(m.name).parts,'unsafe tar path')
        tf.extractall(dest,filter='data')
    plain.unlink()

def verify(root,out,label):
    source=root/'frozen_source/scripts/platform/rtx_trajectory_cost_v4/offline.py'
    command=[sys.executable,'-B',str(source),str(root)]
    r=subprocess.run(command,capture_output=True,timeout=900,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    (out/(label+'.stdout.json')).write_bytes(r.stdout)
    (out/(label+'.stderr.log')).write_bytes(r.stderr)
    require(r.returncode==0,'frozen offline verifier failed '+label+'; see retained stderr')
    result=json.loads(r.stdout);require(result['status']=='PASS','offline status '+label)
    return result

def copy_phase(root,out,name):
    dest=out/'raw'/name;shutil.copytree(root/'work'/name,dest)
    metadata=out/'raw'/'metadata'
    if not metadata.exists():shutil.copytree(root/'metadata',metadata)
    inventory=read(root/'MANIFEST.json')['files']
    files={}
    for p in dest.rglob('*'):
        if not p.is_file():continue
        original='work/'+name+'/'+p.relative_to(dest).as_posix();sealed=inventory[original]
        require(p.stat().st_size==sealed['bytes'] and sha(p)==sealed['sha256'],'review copy changes raw bytes')
        files['raw/'+name+'/'+p.relative_to(dest).as_posix()]={'original_member':original,**sealed}
    save(out/(name+'.RAW_MEMBER_CORRESPONDENCE.json'),files)

def independent_native(rows,root):
    # Reparse all native committed IDs and QPC lines directly. Does not import
    # the producer's parser, analysis module or frozen verifier implementation.
    import re
    lookup={};eog={128247,151643,151645,151662,151663,151664}
    for r in rows:
        d=root/r['path'];rec=read(d/'record.json');require(all(r.get(k)==v for k,v in rec.items()),'phase/run record identity')
        for n,v in rec['files'].items():require((d/n).stat().st_size==v['bytes'] and sha(d/n)==v['sha256'],'per-run hash')
        text=(d/'native.log').read_bytes().replace(b'\r\n',b'\n').decode('latin-1');ids=[]
        for line in text.splitlines():
            if 'process_toke:' not in line or 'n_gen =' not in line or 'next token:' not in line:continue
            n=int(line.split('n_gen =',1)[1].split(',',1)[0]);remaining=int(line.split('n_remaining =',1)[1].split(',',1)[0]);token=int(line.split('next token:',1)[1].strip().split(' ',1)[0])
            require(n==len(ids)+1 and remaining==128-n,'native committed continuity');ids.append(token)
        require(ids==r['generated_ids']==read(d/'generated_ids.json'),'native full-array reconstruction')
        require(1<=len(ids)<=128 and not any(t in eog for t in ids[:-1]),'inclusive first EOG')
        stops=re.findall(r'process_toke:.*stopped by (EOS|limit)',text)
        expected=['limit','EOS'] if len(ids)==128 and ids[-1] in eog else ['limit'] if len(ids)==128 else ['EOS']
        require(stops==expected and (len(ids)==128 or ids[-1] in eog),'native endpoint observations')
        require(re.findall(r'slot print_timing: id\s+0 \| task \d+ \|\s+eval time\s*=\s*[\d.]+ ms /\s*(\d+) tokens',text)==[str(len(ids))],'native output count')
        if r['implementation']=='TIMER':
            matches=re.findall(rb'HS_TIMER start_qpc=(\d+) end_qpc=(\d+) frequency=(\d+) start_steady_ns=(\d+) end_steady_ns=(\d+) count=(\d+) terminal_id=(\d+)',(d/'stderr.log').read_bytes())
            require(len(matches)==1,'one QPC interval')
            st,en,freq,sn,ens,count,terminal=map(int,matches[0]);ms=1000*(en-st)/freq
            require(en>st and ens>sn and freq>0 and count==len(ids) and terminal==ids[-1],'timer exact endpoint')
            require(abs(ms-(ens-sn)/1e6)<=max(.020,.001*ms),'clock cross-check')
            require(ms==r['timer']['milliseconds'],'declared ms vs raw QPC')
        lookup[r['task_id'],r['repetition'],r['canonical_condition']]=r
    return lookup

def derived_review(out):
    root=out/'raw';meta=root/'metadata';p=read(meta/'JOINT_PROTOCOL.json');tasks=p['A']['task_ids']
    live=read(root/'A-live/records.json');b=read(root/'B-formal/records.json')
    # Copies keep original work/... paths. Expose them as ordinary directory
    # names only for this independent read-only parser, outside sealed capsules.
    work=root/'work';work.mkdir();os.symlink('../A-live',work/'A-live');os.symlink('../B-formal',work/'B-formal')
    al=independent_native(live['runs'],root);bl=independent_native(b['runs'],root)
    sealed=read(meta/'A_trajectory/RESERVED_PREDICTIONS.json');cs=p['A']['conditions'];A={}
    for c in cs[:4]:
        pairs=[{'task_id':s['task_id'],'repetition':s['repetition'],'exact':s['conditions'][c]['generated_ids']==al[s['task_id'],s['repetition'],cs[4]]['generated_ids']} for s in sealed['rows']]
        A[c]={'exact_pairs':sum(x['exact'] for x in pairs),'total_pairs':57,'wholly_exact_prompts':sum(all(x['exact'] for x in pairs if x['task_id']==t) for t in tasks),'mismatch_prompts':sorted({x['task_id'] for x in pairs if not x['exact']})}
    bc=p['B']['conditions'];med={t:{c:sorted(bl[t,r,c]['timer']['milliseconds'] for r in [1,2,3])[1] for c in bc} for t in tasks}
    rng=random.Random(2026100204);stream=[[rng.randrange(len(tasks)) for _ in tasks] for _ in range(10000)]
    def gm(v):return math.exp(math.fsum(math.log(x) for x in v)/len(v))
    def quantile(v,p):
        v=sorted(v);k=(len(v)-1)*p;lo=math.floor(k);hi=math.ceil(k)
        return v[lo]*(hi-k)+v[hi]*(k-lo) if lo!=hi else v[lo]
    B={}
    for c in bc[1:]:
        exact=sum(bl[t,r,bc[0]]['generated_ids']==bl[t,r,c]['generated_ids'] for t in tasks for r in [1,2,3]);ok=exact==57
        ratios=[med[t][bc[0]]/med[t][c] for t in tasks];draws=[gm([ratios[i] for i in ix]) for ix in stream] if ok else []
        B[c]={'exact_pairs':exact,'total_pairs':57,'status':'QUALIFIED' if ok else 'BLOCKED','speedup':gm(ratios) if ok else None,'CI':[quantile(draws,.025),quantile(draws,.975)] if ok else None,'candidate_faster_prompts':sum(x>1 for x in ratios) if ok else None}
    reported=read(meta/'B_matched_cost/REPORT.json')
    require(med==reported['prompt_median_ms'],'raw medians vs report')
    for c,v in B.items():
        for k,x in v.items():
            y=reported['paths'][c][k]
            if isinstance(x,float):require(math.isclose(x,y,rel_tol=1e-12),'point estimate differs')
            elif k=='CI' and x is not None:require(all(math.isclose(a,b,rel_tol=1e-12) for a,b in zip(x,y)),'bootstrap differs')
            else:require(x==y,'raw gate differs '+c+'/'+k)
    require([A[c]['exact_pairs'] for c in cs[:4]]==[51,51,57,57],'A full-array counts')
    require(len(al)==57 and len(bl)==171,'complete native schedule')
    result={'status':'PASS','source_head':HEAD,'A_native_runs':57,'B_native_runs':171,'A':A,'B':B,'distinct_prompts':19,'GPU_required':False,'new_model_forwards':0,'observer_and_latency_scope':'frozen instrumented post-prefill path; no necessity/minimality/population claim','fan_policy':'author instructed not to treat adjustment as an obstacle; original amendment remains disclosed'}
    save(out/'INDEPENDENT_RAW_RECOMPUTATION.json',result)
    # Preserve the two original manifests byte-for-byte as readable text.
    # Full native logs remain in the original Git capsules; this compact
    # delivery supplements them and does not replace or relabel raw evidence.
    for name in ['A-live','B-formal']:
        shutil.copyfile(root/name/'records.json',out/(name+'.ORIGINAL_RECORDS.json'))
    save(out/'FORMAL_CAPTURE_RECONSTRUCTION.json',{
      'source_head':HEAD,'derived_not_original':True,
      'A':[{'task_id':r['task_id'],'repetition':r['repetition'],'condition':r['canonical_condition'],'generated_ids':r['generated_ids'],'native_log_sha256':r['files']['native.log']['sha256']} for r in live['runs']],
      'B':[{'task_id':r['task_id'],'repetition':r['repetition'],'condition':r['canonical_condition'],'generated_ids':r['generated_ids'],'timer':r['timer'],'native_log_sha256':r['files']['native.log']['sha256'],'stderr_log_sha256':r['files']['stderr.log']['sha256']} for r in b['runs']]})
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='audit-output');ap.add_argument('--scratch',default='audit-scratch');a=ap.parse_args()
    out=pathlib.Path(a.output).resolve();scratch=pathlib.Path(a.scratch).resolve();out.mkdir(exist_ok=False);scratch.mkdir(exist_ok=False)
    retrieve=Retrieval(out);completed=[]
    try:
        for name in ARCHIVES:
            label=name.removesuffix('.json');print('START',label,flush=True)
            descriptor=read(retrieve.file(STUDY+name,out/'indexes'/name))
            idx=read(retrieve.file(descriptor['path'],out/'indexes'/(label+'.parts.json')))
            require(idx['sha256']==descriptor['sha256'] and idx['bytes']==descriptor['bytes'],'descriptor/index identity')
            stage=scratch/label;stage.mkdir();archive=stage/'archive.tar.gz'
            with archive.open('xb') as merged:
                for i,part in enumerate(idx['parts'],1):
                    require(part['ordinal']==i,'part ordering')
                    q=retrieve.file(part['path'],stage/('part'+str(i)),part)
                    with q.open('rb') as f:shutil.copyfileobj(f,merged,1024*1024)
                    q.unlink()
            require(archive.stat().st_size==idx['bytes'] and sha(archive)==idx['sha256'],'full archive hash')
            evidence=stage/'evidence';evidence.mkdir();safe_extract(archive,evidence);archive.unlink()
            require(sha(evidence/'MANIFEST.json')==idx['manifest_sha256'],'sealed manifest hash')
            result=verify(evidence,out,label)
            if name in ['A_COMPLETE_ARCHIVE.json','B_COMPLETE_ARCHIVE.json']:copy_phase(evidence,out,'A-live' if name.startswith('A') else 'B-formal')
            completed.append({'label':label,'archive_sha256':idx['sha256'],'archive_bytes':idx['bytes'],'file_count':idx['file_count'],'offline_result':result,'actual_retrieved_and_extracted':True})
            save(out/'ARCHIVE_REPLAY.json',{'source_head':HEAD,'archives':completed})
            shutil.rmtree(stage);print('PASS',label,flush=True)
        recomputed=derived_review(out)
        save(out/'CLOSEOUT.json',{'status':'PASS','source_head':HEAD,'archives_verified':len(completed),'all_nine_capsules_replayed':len(completed)==9,'independent_raw_recomputation':recomputed,'new_model_forwards':0,'original_files_modified':0,'run_id':os.environ.get('GITHUB_RUN_ID'),'workflow_head':os.environ.get('GITHUB_SHA')})
        print('RTX_CLOSEOUT_PASS',json.dumps(recomputed),flush=True)
    except Exception as e:
        save(out/'CLOSEOUT_FAILURE.json',{'status':'FAILED_PRESERVED','type':type(e).__name__,'message':str(e),'completed_archives':len(completed),'new_model_forwards':0});raise
    finally:save(out/'REMOTE_RETRIEVAL.json',{'head':HEAD,'files':retrieve.receipts})

if __name__=='__main__':main()
