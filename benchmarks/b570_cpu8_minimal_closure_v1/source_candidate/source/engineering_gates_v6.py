"""Derived engineering gates from actual native operations, never receipt booleans alone."""
import json,re,sys,hashlib
from pathlib import Path
def need(x,m):
 if not x:raise ValueError(m)
def load(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def operation(root,id):
 from delivery_binding_v6 import invocation
 argv=load(root/'tools'/(id+'.operation.json'))['argv']
 return invocation(root,id,argv,root/'operations'/id/'stdout.log')
def check(root):
 root=Path(root);out={}
 for id,count in [('036-final-regressions',91),('026-budget-negatives',11)]:
  actual=operation(root,id);text=(root/'operations'/id/'stderr.log').read_text()
  need(re.search(r'Ran '+str(count)+r' tests? in ',text) is not None and text.rstrip().endswith('OK'),'actual test count/result '+id)
  out[id]=dict(actual=actual,tests=count,stderr_sha256=sha(root/'operations'/id/'stderr.log'))
 raw=load(root/'development/BRIDGE_REGRESSIONS.json');need(len(raw['cases'])==7 and all(x['status']=='EXPECTED_RAW_REJECTION' for x in raw['cases']),'actual bridge counterfactuals')
 operation(root,'025-bridge-negatives')
 original=load(root/'CAMPAIGN.json');ext=Path(original['external_root'])
 from delivery_binding_v6 import download,invocation
 row=load(ext/'probe-download-row.json');intent=load(ext/'download-intents/probe-download-01.json')
 out['download']=download(root,'probe-download-01',row,intent['request']['ref'])
 argv=load(root/'tools/030-isolated-probe-recompute.operation.json')['argv']
 out['restore']=invocation(root,'030-isolated-probe-recompute',argv,ext/'probe-remote-restore-01/REPORT.json')
 need((ext/'probe-original-report.json').read_bytes()==(ext/'probe-remote-restore-01/REPORT.json').read_bytes(),'actual independent probe bytes')
 # CPU-only build must be from the actual observed compiler command.
 build=load(root/'compiled/BUILD_CURRENT.json')
 compiler_events=[json.loads(line) for line in (root/'processes/compile-v6-2/OS_EVENTS.jsonl').read_bytes().splitlines()]
 need(build['compiler'] in compiler_events and build['exit'] in compiler_events,'compiler original native records')
 need(build['exit']['exit_code']==0 and int(build['exit']['exit_filetime'])>int(build['compiler']['created_filetime']),'actual compiler closure')
 need(build['dll_sha256']==sha(root/'compiled/candidate/LauncherCapture.dll') and build['source_sha256']==sha(root/'legacy/repo/benchmarks/b570_supervision_fix_v2/host/LauncherCapture.cs'),'actual source/compiled binding')
 return dict(status='ENGINEERING_RAW_GATES_RECONSTRUCTED',operations=out,scope='Engineering only, not formal native qualification or external certification')
