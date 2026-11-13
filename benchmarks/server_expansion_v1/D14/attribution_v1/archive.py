"""Close new evidence and the exact predecessor chain; no network publication."""
from pathlib import Path
import argparse,fcntl,hashlib,json,shutil,subprocess,sys,time

def main():
    p=argparse.ArgumentParser()
    for k in ('root','work','audit'):p.add_argument('--'+k,type=Path,required=True)
    a=p.parse_args();r=a.root;w=a.work;audit=a.audit;sys.path.insert(0,str(r/'d14-runtime-02'))
    from common import read,save,sha,need
    from readback_export import verify
    prior=r/'d14-run-01';previous=r/'d14-public-export-02';start=time.monotonic()
    with (r/'STUDY_SCHEDULING.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        checked=verify(previous,raw_work=prior)
        need(checked['public_bundle_passed'] and checked['private_raw_captures_read_back']==checked['indexed_binary_captures'],'Full predecessor text/capture chain readback')
        save(audit/'PREDECESSOR_FULL_READBACK.json',dict(**checked,scope_sha256=sha(previous/'EXPORT_SCOPE.json'),original_local_readback_sha256=sha(previous/'LOCAL_READBACK.json'),wall_s=time.monotonic()-start,native_or_performance_reexecution=False))
    formal=read(w/'FORMAL_STAGE_STATUS-01.json');q=w/'qualification-03/NATIVE_CHECKS_COMPLETE.json';complete=audit/'COMPLETION.json'
    save(complete,dict(status='COMPLETE' if formal['status']=='COMPLETE' else 'QUALIFIED_FORMAL_NOT_RUN',finite_qualification_passed=read(q)['passed'],formal_performance_status='COMPLETE' if formal['status']=='COMPLETE' else 'NOT_RUN',formal_stage_sha256=sha(w/'FORMAL_STAGE_STATUS-01.json'),qualification_summary_sha256=sha(q),predecessor_scope_sha256=sha(previous/'EXPORT_SCOPE.json'),predecessor_readback_sha256=sha(audit/'PREDECESSOR_FULL_READBACK.json'),raw_scope='Own new captures plus exact predecessor archive, separate indices; all predecessor private captures independently reread',public_upload='NOT_RUN'))
    files=[]
    for path in sorted(audit.glob('*')):
        if path.is_file() and path.suffix in ('.json','.log') and 'private' not in path.name:files.append(dict(name='attribution/'+path.name,source=str(path),sha256=sha(path)))
    manifest=audit/'SUPPORT_MANIFEST.private.json';save(manifest,dict(schema='linux-transfer.exact-support-files.v1',files=files))
    out=r/'d14-attribution-export-01';cmd=[sys.executable,'-B',str(r/'export_transfer-v4.py'),'--work',str(w),'--runtime',str(r/'d14-runtime-02'),'--builds',str(r/'d14-deployment-build-02'),'--completion',str(complete),'--support-manifest',str(manifest),'--out',str(out)]
    result=subprocess.run(cmd);need(result.returncode==0,'Own archive/full capture readback failed')
    with (r/'STUDY_SCHEDULING.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);dest=out/'predecessor';dest.mkdir()
        for name in ('scientific-records.json.gz','TEXT_INDEX.json','BINARY_CAPTURE_INDEX.json','EXPORT_SCOPE.json','LOCAL_READBACK.json'):
            shutil.copy2(previous/name,dest/name);need(sha(previous/name)==sha(dest/name),'Predecessor delivery bytes differ')
        verify(dest)
        entries=[dict(path=str(p.relative_to(out)),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.rglob('*')) if p.is_file()]
        save(out/'DELIVERY_INDEX.json',dict(files=entries,predecessor_is_exact_original_archive=True,old_formal_times_not_pooled=True,external_publication='NOT_RUN',archive_and_private_readback_wall_s=time.monotonic()-start))
    print('ATTRIBUTION_AND_PREDECESSOR_CHAIN_ARCHIVED',flush=True)
if __name__=='__main__':main()
