import time,json,subprocess,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
deadline=time.monotonic()+600
while not (R/'STUDY_COMPLETION.json').exists():
 assert time.monotonic()<deadline,'CPU pipeline waiting bound'
 time.sleep(.5)
assert json.loads((R/'STUDY_COMPLETION.json').read_bytes())['status']=='COMPLETED'
def step(name,args):
 p=subprocess.run([sys.executable,'-B','-X','utf8',*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
 (R/'receipts'/(name+'.stdout.log')).write_bytes(p.stdout);(R/'receipts'/(name+'.stderr.log')).write_bytes(p.stderr)
 assert p.returncode==0,p.stdout.decode(errors='replace')+p.stderr.decode(errors='replace')
 print(name,p.stdout.decode(errors='replace').strip(),flush=True)
step('audit',[str(R/'code/verify98.py'),'--root',str(R),'--output',str(R/'analysis')])
step('synthetic',[str(R/'code/test_verify98.py')])
step('report',[str(R/'code/report98.py')])
step('seal_complete',[str(R/'code/seal_complete98.py')])
step('local_restore',[str(R/'code/restore98.py'),'--cas',str(R/'COMPLETE_CAS.zip'),'--dest',str(R/'receipts/local_restore')])
step('local_rederive',[str(R/'receipts/local_restore/code/verify98.py'),'--root',str(R/'receipts/local_restore'),'--output',str(R/'receipts/local_rederived')])
names=['RESULTS.json','QUALIFICATION.json','WORK_WITNESSES.json','NUMERICAL_STATE_LAYOUTS.json','INDEPENDENT_VERIFICATION.json']
hashes={}
for n in names:
 b=(R/'analysis'/n).read_bytes();assert b==(R/'receipts/local_rederived'/n).read_bytes();hashes[n]=hashlib.sha256(b).hexdigest()
cas=json.loads((R/'COMPLETE_CAS.json').read_bytes())
receipt=dict(status='PASS_FRESH_ALL_BYTES_AND_INDEPENDENT_EXACT_REDERIVATION',cas_sha256=cas['sha256'],logical_files=cas['logical_files'],unique_objects=cas['unique_objects'],exact_artifacts=hashes,full_target_model_rehashed=True,new_model_forwards=0)
(R/'LOCAL_RESTORE.json').write_bytes((json.dumps(receipt,indent=2)+'\n').encode())
print('ALL_NATIVE_LOCAL_AUDIT_ARCHIVE_RESTORE_CLOSED',flush=True)
