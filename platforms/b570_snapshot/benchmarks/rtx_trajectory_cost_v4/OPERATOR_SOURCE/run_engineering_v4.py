"""Authorized fresh engineering sequence; never starts a reserved/formal phase."""
import sys,subprocess,json,shutil,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
sys.path.insert(0,str(SRC))
from prepare import STUDY,save,sha,now
import engineering,engineering_extra,negative,finalize,configuration,identity
assert json.loads((STUDY/'CAPTURE_REPAIR_QUALIFICATION.json').read_text(encoding='utf-8'))['status']=='PASS'
for p in SRC.glob('*.py'):ast.parse(p.read_text(encoding='utf-8'),filename=str(p))
before=ROOT/'work/preparation-initial';before.mkdir(exist_ok=False)
for name in ['ASSET_IDENTITY.json','ENVIRONMENT.json','BUILD_IDENTITY.json','EXPOSURE_AUDIT.json']:shutil.copy2(STUDY/name,before/name)
previous=ROOT.with_name('HeteroSpec-v3')
failure_script=(previous/'work/check_failure_paths.py').read_text(encoding='utf-8').replace('rtx_trajectory_cost_v3','rtx_trajectory_cost_v4')
(ROOT/'work/check_failure_paths.py').write_text(failure_script,encoding='utf-8')
subprocess.run([sys.executable,'-B',str(ROOT/'work/check_failure_paths.py')],cwd=ROOT,check=True)
print('START: fresh 360-condition fixed engineering schedule',flush=True)
engineering.main('engineering-attempt1')
print('START: fresh observer/endpoint engineering and constructed contexts',flush=True)
engineering_extra.main()
print('START: independent raw/statistical negative cases',flush=True)
negative.main()
print('START: independent preparation verification and external-byte recheck',flush=True)
finalize.main()
save(STUDY/'V4_ENGINEERING_SEQUENCE.json',{'status':'PASS','utc':now(),'new_study':'RTX_TRAJECTORY_AND_MATCHED_COST_V4','fresh_engineering_conditions':430,'capture_repair_conditions':30,'reserved_model_forwards':0,'formal_actual_runs':0,'old_V3_evidence_overwritten':False,'formal_reruns':0})
print('PASS: 430 fresh engineering conditions, independent gates/negatives, reserved forwards remain zero',flush=True)
