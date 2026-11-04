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
 report['old_R_and_k1_hashes']=dict(original_R=read(root/'INHERITED_AUTHENTICATION.json')['old_R_hashes'],original_k1=read(root/'INHERITED_AUTHENTICATION.json')['old_k1_sha256'])
 return report
if __name__=='__main__':print(json.dumps(recompute(sys.argv[1]),indent=2))
