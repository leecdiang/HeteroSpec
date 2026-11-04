#!/usr/bin/env python3
"""Compare logical sidecar annotations to independently observed native endpoints."""
import argparse, pathlib, sys, importlib.util, hashlib, json, copy
sys.dont_write_bytecode=True
p=argparse.ArgumentParser();p.add_argument('--inspector',type=pathlib.Path,required=True);p.add_argument('--journal',type=pathlib.Path,required=True);p.add_argument('--native',type=pathlib.Path,required=True);p.add_argument('--prompt-ids',required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
def require(x,m):
 if not x:raise ValueError(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('reviewed_inspector',a.inspector);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
raw=a.journal.read_bytes();prompt=[int(x) for x in a.prompt_ids.split(',')];side=module.inspect(raw,prompt)
require(side.get('prompt_binding_status')=='CALLER_SUPPLIED_NOT_VERIFIED_BY_JOURNAL','prompt binding caveat missing')
source=[json.loads(line)['result'] for line in raw.splitlines() if json.loads(line)['status']=='COMPLETED'];native=json.loads(a.native.read_text())['attempts']
require(len(source)==len(side['records'])==len(native)>0,'case count mismatch')
key=lambda x:tuple(x[k] for k in ('draft_ubatch','forced_reject_index','cap','stop_after_output_index'))
for s,r,n in zip(source,side['records'],native):
 require(key(s)==key(n),'case identity mismatch');v=r['annotation'];t=n['terminal_materialization_evidence']
 require(v['logical_committed_end_exclusive']==t['materialized_next_position'],'prefix position mismatch')
 require(v['terminal_branch']==t['terminal_kind'],'branch mismatch')
 suffix=v['emitted_unconsumed_suffix'];require(len(suffix)==int(not t['last_output_materialized']),'pending count mismatch')
 require((suffix[0]['id'] if suffix else None)==t['unmaterialized_output_token'],'pending token mismatch')
 row=v['boundary_logit_source']['source_row_index'] if v['boundary_logit_source']['phase']=='verify' else -1
 require(row==t['frontier_logit_row'],'frontier row mismatch')
 require(v['recovery']['status']=='UNPROVEN' and v['recovery']['resume_authorized'] is False,'unexpected recovery claim')
rejected=0
for s in source:
 if not s['cycles']:continue
 for field,value in [('keep',s['cycles'][-1]['keep']+1),('base',s['cycles'][-1]['base']+1),('last','unknown'),('pending',1),('accepted',True)]:
  bad=copy.deepcopy(s);bad['cycles'][-1][field]=value
  try:module.derive(bad,prompt)
  except ValueError:rejected+=1
  else:raise ValueError('corrupted record accepted: '+field)
type_rejected=0
for s in source:
 if not s['cycles']:continue
 for field in ('base','keep'):
  bad=copy.deepcopy(s);bad['cycles'][-1][field]=float(bad['cycles'][-1][field])
  try:module.derive(bad,prompt)
  except ValueError:type_rejected+=1
  else:raise ValueError('noninteger frontier accepted: '+field)
require(raw==a.journal.read_bytes(),'journal bytes changed')
result={'status':'PASS','inspector_sha256':sha(a.inspector),'journal_sha256':sha(a.journal),'native_result_sha256':sha(a.native),'native_annotations_matched':len(native),'structural_mutations_rejected':rejected,'noninteger_frontiers_rejected':type_rejected,'journal_bytes_unchanged':True,'recovery_status':'UNPROVEN','scope':'Logical sidecar consistency with pinned CPU fixture observations; no checkpoint or deployment qualification'}
with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps(result))
