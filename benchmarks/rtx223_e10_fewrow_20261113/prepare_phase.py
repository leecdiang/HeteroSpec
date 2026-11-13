"""Freeze a new phase, then atomically queue its hash-bound entry."""
from pathlib import Path
import json,hashlib,sys,os
p=Path(__file__).resolve().parent
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def write(q,v):
 with q.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,indent=2)
phase=sys.argv[1];assert phase in ('qualification','timing')
assert json.loads((p/'CPU_SMOKE_PASS.json').read_bytes())['pass']
stage=json.loads((p/'STAGING.json').read_bytes());s=Path(stage['stage'])
out=Path(stage['profile'])/'Temp'/('e10-'+phase+'-001')
job=dict(schema='heterospec-e10-fewrow-v1',gpu_admitted=True,phase=phase,output_dir=str(out),device_uuid=json.loads((p/'CONTRACT.json').read_bytes())['device_uuid'])
for name,key in [('weight.bin','weight'),('activation.f32','input'),('backend-output.f32','backend_output'),('activation_q8_1.bin','quantized_activation')]:
 q=s/name;job[key+'_path']=str(q);job[key+'_sha256']=sha(q)
if phase=='timing':
 qual=Path(stage['profile'])/'Temp/e10-qualification-001'
 result=json.loads((qual/'result.json').read_bytes())
 assert result['status']=='PASS_TWO_CONTRACT_DIAGNOSTIC' and result['explicit_prelaunch_charged']==8
 receipt=Path('D:/HeteroSpec-PC/rtx223-e10-fewrow/qualification-001/attempt.jsonl')
 assert json.loads(receipt.read_text().splitlines()[-1])['kind']=='PASS'
 for filename,key in [('U-r0-activation.bin','U_qualified_activation'),('U-r0-output.bin','U_qualified_output')]:
  q=qual/filename;job[key+'_path']=str(q);job[key+'_sha256']=sha(q)
jobpath=s/(phase+'-job-001.json');write(jobpath,job)
plan=json.loads((p/'CPU_PLAN_001.json').read_bytes())
plan.update(phase=phase,app_launch_reservation=14 if phase=='qualification' else 355,receipt_dir='D:/HeteroSpec-PC/rtx223-e10-fewrow/'+phase+'-001',output_dir=str(out),argv=[str(s/'operator-upstream.exe'),str(jobpath)])
extras=[p/'CPU_SMOKE_PASS.json',p/'main_body_v2.inc',p/'upstream_wrap.cu',p/'CPU_NUMERICAL_DOMAIN.json',p/'UPSTREAM_BLOBS_VERIFIED.json',jobpath]
if phase=='timing':extras+=[qual/'result.json',receipt,qual/'U-r0-activation.bin',qual/'U-r0-output.bin']
plan['controller_inputs'] += [dict(path=str(q),sha256=sha(q)) for q in extras]
planpath=p/(phase.upper()+'_PLAN_001.json');write(planpath,plan)
entry=p/('execute_'+phase+'_001.py')
source="from pathlib import Path\nimport json,hashlib,sys,runpy\np=Path(__file__).resolve().parent\nplan=p/"+repr(planpath.name)+"\nassert hashlib.sha256(plan.read_bytes()).hexdigest()=="+repr(sha(planpath))+"\nfor row in json.loads(plan.read_bytes())['controller_inputs']:\n assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']\nsys.argv=[str(p/'runner.py'),str(plan)]\nrunpy.run_path(str(p/'runner.py'),run_name='__main__')\n"
with entry.open('x',encoding='utf8',newline='\n') as f:f.write(source)
req=dict(script=str(entry),sha256=sha(entry),reservation=plan['app_launch_reservation'],kind='NUMERICAL',counter_audit=True)
dest=p/'admin-queue'/('002-qualification.json' if phase=='qualification' else '003-timing.json')
tmp=dest.with_suffix('.pending');write(tmp,req);os.rename(tmp,dest)
print(json.dumps(dict(queued=str(dest),job_sha256=sha(jobpath),plan_sha256=sha(planpath))))
