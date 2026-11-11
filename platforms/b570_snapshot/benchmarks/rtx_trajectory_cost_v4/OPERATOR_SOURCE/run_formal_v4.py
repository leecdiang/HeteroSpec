"""Run already-authorized frozen phases sequentially; stop on any failed stage."""
import os,sys,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
sys.path.insert(0,str(SRC))
from prepare import STUDY,save,sha,now
receipt=json.loads((STUDY/'F0_REMOTE_RECEIPT.json').read_text(encoding='utf-8'))
assert receipt['full_retrieval_verified'] and receipt['commit']==receipt['remote_ref']
assert (STUDY/'NEW_STUDY_AUTHORIZATION.json').exists()
assert (ROOT/'work/DRAFT_PR.json').exists()
os.environ.update(PYTHONDONTWRITEBYTECODE='1',GODEBUG='http2client=0')
out=ROOT/'work/formal-operator';out.mkdir(exist_ok=False)
rows=[];record={'status':'STARTED','started_utc':now(),'F0':receipt['commit'],'stages':rows,'authorization_scope':'Direct human repair/continuation request; operator execution mode and content SHA binding are not asserted to be literal human input.'}
save(out/'records.json',record)
try:
    for mode in ['A-pre-live','seal-predictions','A-live','B-formal','verify','archive']:
        cmd=[sys.executable,'-B',str(SRC/'study.py'),mode]
        if mode in ['A-pre-live','B-formal']:cmd+=['--authorization','EXECUTE_FROZEN','--reviewed-sha',receipt['commit']]
        row={'mode':mode,'command':cmd,'started_utc':now(),'status':'STARTED'};rows.append(row);save(out/'records.json',record)
        print('START',mode,row['started_utc'],flush=True)
        with (out/(mode+'.stdout.log')).open('xb') as stdout,(out/(mode+'.stderr.log')).open('xb') as stderr:
            proc=subprocess.Popen(cmd,cwd=ROOT,stdout=stdout,stderr=stderr);row['pid']=proc.pid;save(out/'records.json',record);code=proc.wait()
        row.update(ended_utc=now(),exit_code=code,status='COMPLETE' if code==0 else 'FAILED',stdout_sha256=sha(out/(mode+'.stdout.log')),stderr_sha256=sha(out/(mode+'.stderr.log')));save(out/'records.json',record)
        print(row['status'],mode,row['ended_utc'],flush=True)
        if code:raise RuntimeError('Frozen stage failed: '+mode+'; preserve actual prefix, no automatic model retry')
    record['status']='COMPLETE'
except Exception as e:record.update(status='STOPPED_STAGE_FAILURE',error=repr(e));raise
finally:record['ended_utc']=now();save(out/'records.json',record)
