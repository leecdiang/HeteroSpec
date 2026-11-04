"""CPU-only report reconstructed from restored native bytes."""
from pathlib import Path
import json,sys
from verify_raw import verify,read,sha
def recompute(root):
 root=Path(root);report=verify(root)
 toolkit=root/'repro'/'toolkit';sys.path.insert(0,str(toolkit))
 import study,selector
 manifest=read(root/'manifest.json');panel=read(root/'panel.json')
 assert study.select(manifest)==panel
 report['descriptor_census']=study.inspect_manifest(manifest)
 # Keep report compact: complete pool remains in manifest/census and archive.
 for key in ('eligible','rejected'):report['descriptor_census'].pop(key)
 report['panel_sha256']=study.digest(panel)
 if (root/'calibration.json').exists():
  expected=selector.fit(read(root/'calibration.json'),panel);actual=read(root/'policy.json');assert expected==actual
  report['policy']=actual
 if (root/'results.json').exists():report['main_analysis']=study.analyze(read(root/'results.json'),panel)
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
