"""Separate pure-CPU complete U checker after the fresh GPU attempt, before timing."""
from pathlib import Path
import subprocess,json,hashlib,datetime
p=Path(__file__).resolve().parent;stage=json.loads((p/'STAGING_V3.json').read_bytes());s=Path(stage['stage']);qual=Path(stage['profile'])/'Temp/e11-qualification-001'
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
native=json.loads((qual/'result.json').read_bytes());assert native['status']=='PASS_E11_TWO_CONTRACTS' and native['explicit_prelaunch_charged']==8
receipt=Path('D:/HeteroSpec-PC/rtx223-e11-u-contract/qualification-001/attempt.jsonl');assert json.loads(receipt.read_bytes().splitlines()[-1])['event']['kind']=='PASS'
records=[];exe=p/'capture-cpu-001/validate_capture_cpu.exe'
assert sha(exe)==json.loads((p/'capture-cpu-001/RESULT.json').read_bytes())['checker_sha256']
for repeat in (0,1):
 assert (qual/f'B-r{repeat}-activation.bin').read_bytes()==(s/'activation_q8_1.bin').read_bytes()
 assert (qual/f'B-r{repeat}-output.bin').read_bytes()==(s/'backend-output.f32').read_bytes()
 argv=[str(exe),str(s/'weight.bin'),str(s/'activation.f32'),str(qual/f'U-r{repeat}-activation.bin'),str(qual/f'U-r{repeat}-output.bin')]
 cp=subprocess.run(argv,capture_output=True,timeout=30,creationflags=0x08000000);assert cp.returncode==0,cp.stderr
 result=json.loads(cp.stdout);assert result['pass'];result.update(repeat=repeat,quant_sha256=sha(qual/f'U-r{repeat}-activation.bin'),output_sha256=sha(qual/f'U-r{repeat}-output.bin'));records.append(result)
assert records[0]['quant_sha256']==records[1]['quant_sha256'] and records[0]['output_sha256']==records[1]['output_sha256']
report=dict(pass_=True,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),B_full_raw_legacy_replays=2,U_full_independent_replays=records,U_raw_bitwise_repeatable=True,checker_sha256=sha(exe),original_e10='FAIL_UNCHANGED',CUDA_initializations_in_this_checker=0)
with (p/'INDEPENDENT_QUALIFICATION.json').open('x',encoding='utf8') as f:json.dump(report,f,indent=2)
print(json.dumps(report))
