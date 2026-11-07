import sys,json,io,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import engine,verify_joint
from prepare import ROOT,STUDY,save,sha,now
captured=[]
class FakeProcess:
 pid=1000
 def __init__(self):self.stdout=iter([b'NOT_JSON\n']);self.stdin=io.BytesIO();self.returncode=None;self.killed=False
 def poll(self):return self.returncode
 def kill(self):self.killed=True;self.returncode=-9
 def wait(self,timeout=None):return self.returncode
def capture(*args,**kwargs):captured.append({'args':args,'kwargs':kwargs})
saved_spawn=engine.subprocess.Popen;saved_ledger=engine.ledger_context
root=ROOT/'work/failure-path-fixtures';root.mkdir(exist_ok=False)
try:
 engine.ledger_context=capture
 proc=FakeProcess();opened=[]
 def spawn(*args,**kwargs):opened.append(kwargs['stderr']);return proc
 engine.subprocess.Popen=spawn
 try:engine.Worker('R',2,root,io.BytesIO())
 except ValueError:pass
 else:raise AssertionError('malformed startup accepted')
 assert proc.killed and opened[0].closed
 w=engine.Worker.__new__(engine.Worker);w.proc=FakeProcess();w.stderr=(root/'close-stderr.log').open('wb');w.role='R';w.closed=False
 def failed_close(q):raise TimeoutError('synthetic close response timeout')
 w.call=failed_close
 try:w.close()
 except TimeoutError:pass
 else:raise AssertionError('close failure hidden')
 assert w.proc.killed and w.stderr.closed
finally:engine.subprocess.Popen=saved_spawn;engine.ledger_context=saved_ledger
# Empty stopped prefix exercises missing observations without inventing IDs.
meta=root/'metadata';save(meta/'JOINT_PROTOCOL.json',{'A':{'task_ids':['SYNTH_STATE_ONLY'],'conditions':['A0','A1','A2','A3','A4']}})
save(root/'work/A-pre-live/records.json',{'status':'INCOMPLETE_OPERATIONAL_FAILURE','runs':[],'error':'synthetic fixture: no process started','not_reached':12})
p=verify_joint.partial(root,meta,'A-pre-live');assert p['actual_attempted_runs']==0 and p['speedup'] is None and p['not_reached']==12
save(STUDY/'FAILURE_PATH_CHECK.json',{'status':'PASS','utc':now(),'cases':['startup failure kills only its synthetic process and closes stderr','close timeout kills only its synthetic process, closes stderr and propagates failure','empty stopped fixed prefix remains incomplete, actual0, not_reached12, null speedup/CI'],'all_processes_mocked':True,'real_processes':0,'model_forward_calls':0,'no_real_ledger_mutation':True,'synthetic_captured_ledger_events':len(captured),'engine_source_sha256':sha(ROOT/'scripts/platform/rtx_trajectory_cost_v4/engine.py'),'scope':'lifecycle and metadata failure checks; not engineering conditions, predictions, acknowledgements or model output'})
print('Three synthetic failure-path checks PASS; real model/process/ledger mutations=0')
