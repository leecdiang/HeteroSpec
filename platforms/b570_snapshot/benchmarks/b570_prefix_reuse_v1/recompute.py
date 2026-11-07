"""CPU-only report reconstructed from restored native bytes."""
from pathlib import Path
import datetime,json,sys
from verify_raw import verify,read,sha
def recompute(root):
 root=Path(root);report=verify(root)
 toolkit=root/'repro'/'toolkit';sys.path.insert(0,str(toolkit))
 import study,selector
 manifest=read(root/'manifest.json');panel=read(root/'panel.json')
 assert study.select(manifest)==panel
 report['descriptor_census']=study.inspect_manifest(manifest)
 def opportunity(rows):
  return dict(paths=len(rows),roots=len({x['root_id'] for x in rows}),crossing_paths=sum(x['crossed_qb_calls']>0 for x in rows),calls={a:sum(x['calls'][a] for x in rows) for a in study.FIXED},rechunk_fewer_calls_than_cut=sum(x['calls']['WB-rechunk']<x['calls']['WB-cut'] for x in rows),rechunk_equal_calls_to_cut=sum(x['calls']['WB-rechunk']==x['calls']['WB-cut'] for x in rows),rechunk_more_calls_than_cut=sum(x['calls']['WB-rechunk']>x['calls']['WB-cut'] for x in rows))
 report['graph_call_opportunity']={k:opportunity(v) for k,v in [('full_eligible_pool',report['descriptor_census']['eligible']),('calibration',panel['calibration']),('test',panel['test'])]}
 detail=read(root/'DESCRIPTOR_OPPORTUNITY_DETAIL.json')
 for k,v in report['graph_call_opportunity'].items():assert detail[k]==v
 # Keep report compact: complete pool remains in manifest/census and archive.
 for key in ('eligible','rejected'):report['descriptor_census'].pop(key)
 report['panel_sha256']=study.digest(panel)
 if (root/'calibration.json').exists():
  expected=selector.fit(read(root/'calibration.json'),panel);actual=read(root/'policy.json');assert expected==actual
  report['policy']=actual
  freeze=read(root/'SOURCE_POLICY_FREEZE.json')
  assert freeze['source_sha256']==study.digest(freeze['source'])
  assert freeze['policy_sha256']==study.digest(actual)
  assert freeze['calibration_sha256']==sha(root/'calibration.json')
  assert freeze['qualification_sha256']==sha(root/'CALIBRATION_QUALIFICATION_V3.json')
  assert freeze['source']['worker']==sha(root/'candidate-03/worker.cpp')
  for name,h in freeze['source']['runner_sources'].items():assert sha(root/'repro'/name)==h
  for name,h in freeze['source']['toolkit_sources'].items():assert sha(root/'repro/toolkit'/name)==h
  for role,key in [('candidate-03','candidate'),('reference-01','reference'),('reference-03','aligned_reference_observer')]:assert read(root/role/'FILES.json')==freeze['source'][key]
  gate=read(root/'COORDINATION_RELEASE.json');remote=read(root/'coordination/RTX_SOURCE_POLICY_FREEZE.json')
  assert gate['released'] and not gate['independent_panel_fork']
  assert gate['local_freeze_sha256']==sha(root/'SOURCE_POLICY_FREEZE.json')
  assert gate['remote_freeze_sha256']==sha(root/'coordination/RTX_SOURCE_POLICY_FREEZE.json')
  first_main=min(datetime.datetime.fromisoformat(read(p)['utc']) for p in (root/'units').glob('main-*/BUDGET.json'))
  assert first_main>=datetime.datetime.fromisoformat(gate['utc'])>=max(datetime.datetime.fromisoformat(freeze['utc']),datetime.datetime.fromisoformat(remote['utc']))
  report['bilateral_freeze_order_verified']=True
 if (root/'results.json').exists():
  main_q=[x for x in report['native_qualification'] if x['unit'].startswith('main-qualification-')]
  cal_q=[x for x in report['native_qualification'] if x['unit'].startswith('cal-qualification-v3-')]
  assert len(main_q)==128 and all(x['qualified'] for x in main_q)
  assert len(cal_q)==36 and all(x['qualified'] for x in cal_q)
  assert read(root/'results.json')['source_freeze_sha256']==sha(root/'SOURCE_POLICY_FREEZE.json')
  report['main_analysis']=study.analyze(read(root/'results.json'),panel)
 else:report['main_analysis']=None
 auth=read(root/'INHERITED_AUTHENTICATION.json')
 for name,h in auth['old_R_hashes'].items():assert sha(root/'historical'/name)==h
 assert sha(root/'historical/K1_REGRESSION.json')==auth['old_k1_sha256']
 report['old_R_and_k1_hashes']=dict(original_R=auth['old_R_hashes'],original_k1=auth['old_k1_sha256'])
 if (root/'ALIGNED_TIMING.json').exists() and (root/'results.json').exists():
  from report_details import report as details
  report['supplementary_costs_and_controls']=details(root)
 return report
if __name__=='__main__':print(json.dumps(recompute(sys.argv[1]),indent=2))
