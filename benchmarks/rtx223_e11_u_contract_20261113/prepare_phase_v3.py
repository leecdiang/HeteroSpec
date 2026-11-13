"""Freeze and queue only the admitted B/U phases. No retries are automatic."""
from pathlib import Path
import json,hashlib,sys,os
p=Path(__file__).resolve().parent
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
def write(q,v):
 with q.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,indent=2)
phase=sys.argv[1];assert phase in ('qualification','timing')
assert json.loads((p/'CPU_SMOKE_PASS.json').read_bytes())['pass']
assert json.loads((p/'counter-cpu-002/RESULT.json').read_bytes())['pass_']
stage=json.loads((p/'STAGING_V3.json').read_bytes());s=Path(stage['stage']);profile=Path(stage['profile'])
out=profile/'Temp'/('e11-'+phase+'-001')
job=dict(schema='heterospec-e11-ucontract-v1',gpu_admitted=True,phase=phase,output_dir=str(out),device_uuid=json.loads((p/'CONTRACT.json').read_bytes())['device_uuid'])
for name,key in [('weight.bin','weight'),('activation.f32','input'),('backend-output.f32','backend_output'),('activation_q8_1.bin','quantized_activation')]:
 q=s/name;job[key+'_path']=str(q);job[key+'_sha256']=sha(q)
extras=[p/x for x in ['CPU_SMOKE_PASS.json','main_body_v3.inc','upstream_wrap_v2.cu','UPSTREAM_BLOBS_VERIFIED.json','counter-cpu-002/RESULT.json','STATIC_ADMISSION_V3.json','PERFORMANCE_DECISION.json','analyze_v3.py']]
if phase=='timing':
 assert json.loads((p/'INDEPENDENT_QUALIFICATION.json').read_bytes())['pass_']
 qual=profile/'Temp/e11-qualification-001';result=json.loads((qual/'result.json').read_bytes())
 assert result['status']=='PASS_E11_TWO_CONTRACTS' and result['explicit_prelaunch_charged']==8
 assert result['explicit_by_operation']==dict(B_quantizer=2,B_projection=2,U_quantizer=2,U_projection=2)
 receipt=Path('D:/HeteroSpec-PC/rtx223-e11-u-contract/qualification-001/attempt.jsonl')
 assert json.loads(receipt.read_bytes().splitlines()[-1])['event']['kind']=='PASS'
 for filename,key in [('U-r0-activation.bin','U_qualified_activation'),('U-r0-output.bin','U_qualified_output')]:
  q=qual/filename;job[key+'_path']=str(q);job[key+'_sha256']=sha(q);extras.append(q)
 extras += [qual/'result.json',receipt,p/'INDEPENDENT_QUALIFICATION.json']
jobpath=s/(phase+'-job-001.json');write(jobpath,job)
plan=json.loads((p/'CPU_PLAN_003.json').read_bytes());plan.update(phase=phase,app_launch_reservation=14 if phase=='qualification' else 416,receipt_dir='D:/HeteroSpec-PC/rtx223-e11-u-contract/'+phase+'-001',output_dir=str(out),argv=[str(s/'operator-ucontract.exe'),str(jobpath)])
plan['controller_inputs'] += [dict(path=str(q),sha256=sha(q)) for q in [*extras,jobpath]]
planpath=p/(phase.upper()+'_PLAN_001.json');write(planpath,plan)
entry=p/('execute_'+phase+'_001.py');source="from pathlib import Path\nimport json,hashlib,sys,runpy\np=Path(__file__).resolve().parent\nplan=p/"+repr(planpath.name)+"\nassert hashlib.sha256(plan.read_bytes()).hexdigest()=="+repr(sha(planpath))+"\nfor row in json.loads(plan.read_bytes())['controller_inputs']:\n assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']\nsys.argv=[str(p/'runner_v3.py'),str(plan)]\nrunpy.run_path(str(p/'runner_v3.py'),run_name='__main__')\n"
with entry.open('x',encoding='utf8',newline='\n') as f:f.write(source)
dest=p/'admin-queue'/('002-qualification.json' if phase=='qualification' else '003-timing.json');tmp=dest.with_suffix('.pending')
write(tmp,dict(script=str(entry),sha256=sha(entry),reservation=plan['app_launch_reservation'],kind='NUMERICAL',counter_audit=True));os.rename(tmp,dest)
print(json.dumps(dict(queued=str(dest),job_sha256=sha(jobpath),plan_sha256=sha(planpath))))
