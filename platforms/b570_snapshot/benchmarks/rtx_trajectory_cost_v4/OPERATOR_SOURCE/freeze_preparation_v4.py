"""Fresh zero-inference metadata verification, four capsules and real F0 receipt."""
import sys,json,subprocess,os,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SRC=ROOT/'scripts/platform/rtx_trajectory_cost_v4'
sys.path.insert(0,str(SRC))
from prepare import STUDY,save,now,sha
assert json.loads((STUDY/'V4_ENGINEERING_SEQUENCE.json').read_text(encoding='utf-8'))['status']=='PASS'
assert not (STUDY/'F0_MANIFEST.json').exists()
os.environ.update(PYTHONDONTWRITEBYTECODE='1',GODEBUG='http2client=0')
subprocess.run([sys.executable,'-B',str(ROOT/'work/complete_preparation_metadata.py')],cwd=ROOT,check=True)
for name in ['initialize_v4.py','run_engineering_v4.py','complete_preparation_metadata.py','run_formal_v4.py','audit_source_v4.py','freeze_preparation_v4.py']:
    shutil.copy2(ROOT/'work'/name,STUDY/'OPERATOR_SOURCE'/name)
# This is a fresh interpreter: it uses corrected V4 branch metadata rather
# than the preparation process's earlier in-memory V3 label.
subprocess.run([sys.executable,'-B',str(SRC/'finalize.py')],cwd=ROOT,check=True)
save(STUDY/'FINAL_PREPARATION_SOURCE_INVENTORY.json',{'status':'PASS','utc':now(),'files':{p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(SRC.iterdir()) if p.suffix in ['.py','.cpp']},'formal_actual_runs':0,'fresh_engineering_conditions':430,'source_evolution':'PRE_F0_SOURCE_EVOLUTION.json'})
subprocess.run([sys.executable,'-B',str(SRC/'study.py'),'seal-protocol'],cwd=ROOT,check=True)
print('F0 engineering publication and full retrieval PASS; formal not started',flush=True)
