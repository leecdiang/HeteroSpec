"""Exposed-task width/cap caller proof and bounded pre-new-input ETA measurement."""
import json,subprocess,sys,statistics
from pathlib import Path
ROOT=Path(__file__).parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8',newline='\n')
manifest=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
tasks=['HumanEval/134','HumanEval/58'];inputs=[{'id':t,'prompt_ids':read(manifest[t]['ids'])} for t in tasks]
sessions=[]
for k,ub in [(1,2),(3,4),(5,6),(7,8)]:
 for native in [False,True]:sessions.append({'config':{'label':'W_NATIVE' if native else 'W_TARGET','native':native,'matched':not native,'prefill':128,'ub':ub,'k':k,'capture':True,'cap':128},'inputs':inputs})
path=ROOT/'G0_WIDTH_SCHEDULE.json'
if path.exists():assert read(path)==sessions
else:save(path,sessions)
subprocess.run([sys.executable,str(ROOT/'runner.py'),'schedule','G0_WIDTH',str(path)],check=True)
rows=[r for r in read(ROOT/'G0_WIDTH_RESULTS.json') if not r['warm']]
expected=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/evaluation/HISTORICAL_EXPECTED.json'))
summary=[]
for r in rows:
 ref=expected[r['task']+'/R/1'];raw=read(next(ROOT/p for p in r['files'] if p.endswith('/capture.json')))
 graphs=[g['ne1'] for t in raw['trace'] if t['event']=='decode' and t['role']=='target' and t['phase']=='continuation' for g in t['graphs'] if g['tensor']=='embd']
 callers=[t['caller_batch_length'] for t in raw['trace'] if t['event']=='decode' and t['role']=='target' and t['phase']=='continuation']
 summary.append({'unit_id':r['unit_id'],'task':r['task'],'config':r['config'],'reference_equal':r['endpoint']['ids']==ref['ids'] and r['endpoint']['eog']==ref['eog'],'occupied_query_range':[min(graphs),max(graphs)] if graphs else None,'actual_caller_range':[min(callers),max(callers)] if callers else None,'actual_generation_ms':r['metrics']['generation_ms'],'whole_request_ms':r['metrics']['whole_request_ms'],'reference_length':len(ref['ids']),'actual_length':len(r['endpoint']['ids']),'timing_scope':'capture-enabled engineering cost only; no qualified speed claim'})
save(ROOT/'G0_WIDTH.json',{'status':'COMPLETE_WITH_RETAINED_OUTPUT_GATES','requests':16,'warmups':8,'observations':summary,'unknown':['observed graph topology is not unique Vulkan dispatch identity']})
print({'width_proof_complete':len(summary),'reference_matches':sum(r['reference_equal'] for r in summary)},flush=True)
