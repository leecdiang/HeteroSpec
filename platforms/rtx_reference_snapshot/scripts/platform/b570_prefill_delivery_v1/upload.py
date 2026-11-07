"""Bounded sequential Git upload with durable receipts; no force pushes."""
import argparse,json,os,pathlib,subprocess,time
from datetime import datetime,timezone
from restore import read,write,sha
ROOT=pathlib.Path(__file__).resolve().parents[3]
OUT=ROOT/'artifacts/b570_prefill_diagnostic_v1';DOC=ROOT/'benchmarks/b570_prefill_diagnostic_v1'
BRANCH='codex/b570-prefill-diagnostic-v1';REMOTE='https://github.com/leecdiang/HeteroSpec.git'
def utc():return datetime.now(timezone.utc).isoformat()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()
def push(commit):
    env=os.environ.copy();env.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='never')
    cmd=['git','-c','http.sslBackend=openssl','-c','pack.threads=2','-c','http.lowSpeedLimit=1024','-c','http.lowSpeedTime=120','push','origin',commit+':refs/heads/'+BRANCH]
    attempts=[]
    for attempt in range(1,4):
        logs=OUT/'delivery-logs';logs.mkdir(exist_ok=True)
        stem=commit[:12]+'-attempt-'+str(attempt);start=utc()
        with (logs/(stem+'.stdout.txt')).open('wb') as out,(logs/(stem+'.stderr.txt')).open('wb') as err:
            code=subprocess.run(cmd,cwd=ROOT,env=env,stdout=out,stderr=err).returncode
        remote=subprocess.check_output(['git','-c','http.sslBackend=openssl','ls-remote',REMOTE,'refs/heads/'+BRANCH],cwd=ROOT,text=True).split()
        seen=remote[0] if remote else None
        attempts.append({'attempt':attempt,'start':start,'end':utc(),'exit_code':code,'remote_head':seen,'stdout':str(logs/(stem+'.stdout.txt')),'stderr':str(logs/(stem+'.stderr.txt'))})
        if seen==commit:return attempts
        if code==0:raise RuntimeError('Push returned success but remote head differs')
        # Interrupted transport may have succeeded server-side; remote ref above
        # decides before any retry. Existing remote data is never replaced.
    raise RuntimeError('Three failed transport attempts; inspect saved delivery logs')
def main():
    assert git('branch','--show-current')==BRANCH
    assert read(DOC/'PORTABLE_LOCAL_VERIFICATION.json')['status']=='PASS'
    assert (DOC/'DELIVERY_SEAL.json').exists()
    index=read(OUT/'ARCHIVE.json');record_path=OUT/'UPLOAD_STATE.json'
    if record_path.exists():
        state=read(record_path);assert state['archive_index_sha256']==sha(OUT/'ARCHIVE.json')
    else:state={'status':'UPLOADING','branch':BRANCH,'archive_index_sha256':sha(OUT/'ARCHIVE.json'),'started':utc(),'batches':[]}
    write(record_path,state)
    tracked=set(git('ls-files','artifacts/b570_prefill_diagnostic_v1').splitlines())
    pending=[p for p in index['parts'] if 'artifacts/b570_prefill_diagnostic_v1/'+p['path'] not in tracked]
    batch_size=8
    # Metadata and restore sources are pushed with the first bounded content batch.
    for offset in range(0,len(pending),batch_size):
        batch=pending[offset:offset+batch_size]
        for p in batch:assert sha(OUT/p['path'])==p['sha256'] and (OUT/p['path']).stat().st_size==p['bytes']
        args=['git','add','scripts/platform/b570_prefill_delivery_v1','benchmarks/b570_prefill_diagnostic_v1',
          'artifacts/b570_prefill_diagnostic_v1/ARCHIVE.json','artifacts/b570_prefill_diagnostic_v1/REMOTE_MANIFEST.json','artifacts/b570_prefill_diagnostic_v1/.gitattributes']
        args += ['artifacts/b570_prefill_diagnostic_v1/'+p['path'] for p in batch]
        subprocess.run(args,cwd=ROOT,check=True)
        subprocess.run(['git','commit','-m',f'Seal B570 prefill raw evidence content batch {offset//batch_size+1}'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        commit=git('rev-parse','HEAD');state.update(current_commit=commit,current_batch_bytes=sum(p['bytes'] for p in batch));write(record_path,state)
        print(json.dumps({'phase':'PUSHING','commit':commit,'batch_parts':len(batch),'batch_bytes':state['current_batch_bytes']},ensure_ascii=False),flush=True)
        attempts=push(commit)
        state['batches'].append({'commit':commit,'parts':batch,'push_attempts':attempts});write(record_path,state)
        print(json.dumps({'phase':'PUSHED','commit':commit,'uploaded_parts':offset+len(batch),'total_parts':len(index['parts'])}),flush=True)
    # If a commit was created before a process interruption, push its existing
    # identity rather than recreate that batch or silently leave it local.
    head=git('rev-parse','HEAD');state['final_push_attempts']=push(head)
    state.update(status='UPLOADED_PENDING_REMOTE_READBACK',content_commit=head,completed=utc(),parts=len(index['parts']),archive_bytes=index['archive_bytes']);write(record_path,state)
    print(json.dumps({k:v for k,v in state.items() if k not in ['batches','final_push_attempts']},ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
