"""Continue the unchanged selected panel after source-bound host schema repair."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
REPO=Path('C:/Users/ASUS/Documents/ChatGPT/HeteroSpec/pr160')
ROOT=Path('E:/rtx160');BUNDLE=ROOT/'research/epoch07'
CODE=REPO/'scripts/experiments/rtx_llama_repair_v1'
HELPERS=REPO/'benchmarks/rtx_llama_repair_v1/host_execution'
OPS=Path('D:/rtx160/operations')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(name,script,args):
 subprocess.run([sys.executable,'-B',str(OPS/'run_logged.py'),name,sys.executable,'-B',str(script),*map(str,args)],cwd=REPO,check=True)
def main():
 deadline=time.monotonic()+3600
 while not (OPS/'PREPARE07.json').exists():
  assert time.monotonic()<deadline;time.sleep(5)
 assert read(OPS/'PREPARE07.json')['exit_code']==0
 assert read(ROOT/'research/CROSS_MODEL_REGRESSION.json')['status']=='CROSS_MODEL_REGRESSION_PASS'
 panel=ROOT/'research/HELDOUT_SELECTION01.json'
 repair=ROOT/'research/HOST_SCHEMA_REPAIR.json'
 assert sha(panel)==read(repair)['selected_panel_sha256']
 assert not (ROOT/'research/epoch06/CANDIDATE_FREEZE.json').exists()
 for name in ('worker','original_worker','build_receipt','source_binding','target','draft','policy'):
  assert read(BUNDLE/'CONFIG.json')[name]==read(ROOT/'research/epoch06/CONFIG.json')[name]
 run('ADMISSION07',CODE/'host.py',['admit','--bundle',BUNDLE])
 run('DEVELOPMENT07',CODE/'host.py',['development','--bundle',BUNDLE])
 dev=read(BUNDLE/'DEVELOPMENT_AUDIT.json');assert dev['all_reference_equal'] and dev['all_observer_equal']
 m=read(ROOT/'research/epoch06/MECHANISM_REVIEW.json')
 m['host_schema_successor']={'numeric_policy_changed':False,'original_epoch':'epoch06','unchanged_panel_sha256':sha(panel)}
 for p in [repair,BUNDLE/'DEVELOPMENT_AUDIT.json',CODE/'host.py',Path(__file__)]:m['evidence'][str(p)]=sha(p)
 with (BUNDLE/'MECHANISM_REVIEW.json').open('x') as f:json.dump(m,f,indent=2)
 run('FREEZE07',CODE/'host.py',['seal','--bundle',BUNDLE,'--panel',panel,'--mechanism',BUNDLE/'MECHANISM_REVIEW.json','--development',BUNDLE/'DEVELOPMENT_AUDIT.json','--regression',ROOT/'research/CROSS_MODEL_REGRESSION.json'])
 run('CONFIRM07',CODE/'host.py',['confirm','--bundle',BUNDLE])
 run('INDEPENDENT_COST07',HELPERS/'independent_cost.py',['--bundle',BUNDLE,'--out',BUNDLE/'INDEPENDENT_COST.json'])
 print('CONFIRMATION_AND_INDEPENDENT_COST_COMPLETE',flush=True)
if __name__=='__main__':main()
