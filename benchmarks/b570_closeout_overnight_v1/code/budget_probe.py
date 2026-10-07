"""Paid, capture-off ETA probes on two already exposed old inputs only."""
from pathlib import Path
import json,sys,subprocess,time
ROOT=Path(__file__).parent
while (ROOT/'ENGINEERING_PAUSE').exists():
 import runner
 if runner.stopped():raise RuntimeError('Cutoff during engineering boundary pause')
 time.sleep(1)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
old=read(Path('C:/hs/b570-prefill-v1/artifacts/b570_prefill_diagnostic_v1/INPUTS.json'))
inputs=[{'id':t,'prompt_ids':read(old[t]['ids'])} for t in ['HumanEval/58','HumanEval/42']]
configs=[dict(label='ETA_R',native=False,plain=True,prefill=128,ub=128,k=2),dict(label='ETA_T',native=False,matched=True,prefill=128,ub=1,k=2),dict(label='ETA_N1',native=True,prefill=128,ub=1,k=2)]
for k,ub in [(1,2),(3,4),(5,6),(7,8)]:
 for native in [False,True]:configs.append(dict(label='ETA_W_NATIVE' if native else 'ETA_W_TARGET',native=native,matched=not native,prefill=128,ub=ub,k=k))
schedule=[dict(config=dict(c,cap=512,capture=False),inputs=inputs) for c in configs]
path=ROOT/'G0_ETA_SCHEDULE.json'
if path.exists():assert read(path)==schedule
else:path.write_text(json.dumps(schedule,indent=2)+'\n',encoding='utf-8',newline='\n')
subprocess.run([sys.executable,str(ROOT/'runner.py'),'schedule','G0_ETA',str(path)],check=True)
rows=[r for r in read(ROOT/'G0_ETA_RESULTS.json') if not r['warm']]
summary={'status':'COMPLETE_OLD_INPUT_ENGINEERING_ONLY','requests':len(rows),'warmups':len(configs),'observations':[{'task':r['task'],'config':r['config'],'host_seconds':r['host_seconds'],'generation_ms':r['metrics']['generation_ms'],'whole_request_ms':r['metrics']['whole_request_ms'],'actual_length':len(r['endpoint']['ids']),'reason':r['endpoint']['reason']} for r in rows],'selection':'No new MBPP inputs; time estimates only, no output-based task selection or qualified speed claim.'}
(ROOT/'G0_ETA.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8',newline='\n')
print({'old_input_eta_requests':len(rows)},flush=True)
