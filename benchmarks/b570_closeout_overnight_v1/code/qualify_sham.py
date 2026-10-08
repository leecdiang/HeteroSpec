"""Fresh plain/sham equivalence for modified resident frontend, before B."""
import json,subprocess,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
old=Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json')
inputs=read(old);tasks=['HumanEval/134','HumanEval/42','HumanEval/145','HumanEval/138','HumanEval/58']
selected=[{'id':t,'prompt_ids':read(inputs[t]['ids'])} for t in tasks]
configs=[{'label':'T_plain','native':False,'matched':True,'plain':True,'prefill':1,'ub':1,'capture':True},{'label':'T_sham','native':False,'matched':True,'prefill':1,'ub':1,'capture':True},{'label':'N_plain','native':True,'plain':True,'k':2,'prefill':1,'ub':1,'capture':True},{'label':'N_sham','native':True,'k':2,'prefill':1,'ub':1,'capture':True}]
schedule=[{'config':c,'inputs':selected} for c in configs]
path=ROOT/'G0_SHAM_SCHEDULE.json'
if path.exists():assert read(path)==schedule
else:dump(path,schedule)
subprocess.run([sys.executable,str(ROOT/'runner.py'),'schedule','G0_SHAM',str(path)],check=True)
rows=[r for r in read(ROOT/'G0_SHAM_RESULTS.json') if not r['warm']];checks=[]
for task in tasks:
 for role in ['T','N']:
  a=next(r for r in rows if r['task']==task and r['config']['label']==role+'_plain');b=next(r for r in rows if r['task']==task and r['config']['label']==role+'_sham')
  def capture(r):return read(next(ROOT/p for p in r['files'] if p.endswith('/capture.json')))
  ca=capture(a);cb=capture(b)
  good=all(a['endpoint'][k]==b['endpoint'][k] for k in ['ids','eog','reason']) and ca['commits']==cb['commits'] and ca['trace']==cb['trace']
  checks.append({'task':task,'role':role,'complete_array_trace_decision_score_equal':good})
dump(ROOT/'G0_SHAM.json',{'status':'PASS' if all(r['complete_array_trace_decision_score_equal'] for r in checks) else 'FAIL','requests':20,'warmups':4,'pairs':checks})
print(read(ROOT/'G0_SHAM.json'))
