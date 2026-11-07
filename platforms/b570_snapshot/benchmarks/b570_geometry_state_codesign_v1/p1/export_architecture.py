"""Run unchanged schema-2 exporter with original R and actual global raw root.
Only rebase raw path names; preserve the original record hash and keep VERIFY sidecars separate.
"""
import copy,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from protocol import read_json,digest,write_new,file_sha
from architecture import architecture_record
PLAN=read_json(ROOT/'p0/PLAN_P1.json');RUNTIME=read_json(ROOT/'p0/RUNTIME.json');RUN=ROOT/'_host/run'
def main():
 out=ROOT/'p1/architecture';out.mkdir(exist_ok=False);raw={p.parent.name:read_json(p) for p in RUN.glob('*/NORMALIZED.json')};rebased={}
 for slot,r in raw.items():
  v=copy.deepcopy(r)
  for a in v['raw_artifacts']:a['path']=slot+'/'+a['path']
  rebased[slot]=v
 index=[]
 for s in PLAN['slots']:
  if s['slot'] not in rebased:continue
  ref=None
  if s['arm']!='R':
   rs=next(x for x in PLAN['slots'] if x['arm']=='R' and x['task']==s['task'] and x['session']==s['session'] and not x['warmup'])
   ref=rebased.get(rs['slot'])
  result=architecture_record(rebased[s['slot']],plan=PLAN,frozen_runtime_sha256=digest(RUNTIME),raw_root=RUN,reference_record=ref)
  p=out/(s['slot']+'.json');write_new(p,result);index.append(dict(slot=s['slot'],task=s['task'],arm=s['arm'],mode=s['mode'],original_normalized_sha256=digest(raw[s['slot']]),path_rebased_record_sha256=digest(rebased[s['slot']]),export_sha256=file_sha(p),qualification=result['qualification']['paired_original_reference_endpoint']))
 write_new(ROOT/'p1/ARCHITECTURE_EXPORTS.json',dict(schema=2,execution_contract='VIOLATION_STOPPED; exported single-record MATCH is exploratory only, never compliant-panel qualification',exports=index,path_rebase_rule='Each original raw_artifacts filename is prefixed with its actual slot directory; no payload/request/work/endpoint edits',VERIFY_source_bound_witnesses='VERIFY_WITNESSES.json; never synthesized into exporter fields',hardware_stage1='HOLD_MISSING_EVIDENCE',native_starts_added=0))
 print(json.dumps(dict(schema=2,exports=len(index),hardware_stage1='HOLD_MISSING_EVIDENCE')))
if __name__=='__main__':main()
